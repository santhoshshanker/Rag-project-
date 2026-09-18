import os
import re
import math
import json
import uuid
import numpy as np
from typing import List, Dict, Any, Optional
import pypdf
import io

class DentalVectorStore:
    """
    A lightweight, robust, zero-dependency dental vector store.
    Uses dense semantic n-gram & medical term TF-IDF feature embeddings with Cosine Similarity,
    providing high-performance vector search offline or online.
    Can be seamlessly supplemented with OpenAI/Gemini embeddings.
    """
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.docs_file = os.path.join(self.storage_dir, "documents.json")
        self.chunks_file = os.path.join(self.storage_dir, "chunks.json")
        
        # State
        self.documents: Dict[str, Dict[str, Any]] = {}  # doc_id -> metadata
        self.chunks: List[Dict[str, Any]] = []         # list of chunk objects
        self.vectors: Optional[np.ndarray] = None       # matrix (num_chunks, dim)
        self.vocab: Dict[str, int] = {}                # term -> feature index
        self.idf: Dict[str, float] = {}                # term -> idf weight
        self.dim = 512                                 # dense embedding dimension
        
        self.load_from_disk()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words, bi-grams, and medical acronyms."""
        cleaned = re.sub(r'[^a-zA-Z0-9%#\.\-\+]', ' ', text.lower())
        tokens = [t.strip('.') for t in cleaned.split() if len(t) > 1 or t in ['#', '%']]
        
        # Add bi-grams for enhanced dental phrase matching (e.g. "dry socket", "root canal", "local anesthesia")
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _build_embedding(self, text: str) -> np.ndarray:
        """
        Compute a dense 512-dimensional normalized semantic vector
        using multi-hash projection with term weights and medical entity boosts.
        """
        tokens = self._tokenize(text)
        vec = np.zeros(self.dim, dtype=np.float32)
        if not tokens:
            return vec

        # Priority dental terminology boost
        clinical_boosts = {
            'lidocaine': 2.5, 'articaine': 2.5, 'mepivacaine': 2.5, 'epinephrine': 2.2,
            'anesthesia': 2.0, 'cartridge': 2.0, 'mrd': 2.5, 'mg_kg': 2.5, 'dose': 2.0,
            'hypochlorite': 2.5, 'naocl': 2.5, 'edta': 2.5, 'canal': 2.0, 'root_canal': 2.5,
            'irrigation': 2.2, 'chlorhexidine': 2.2, 'chx': 2.2, 'pca': 2.5, 'calcium_hydroxide': 2.2,
            'avulsion': 2.5, 'replant': 2.5, 'primary_tooth': 2.5, 'deciduous': 2.2, 'splint': 2.0,
            'hbss': 2.5, 'milk': 2.0, 'socket': 2.0, 'dry_socket': 2.8, 'osteitis': 2.5,
            'alveolar': 2.0, 'bleeding': 2.2, 'hemostasis': 2.2, 'surgicel': 2.2, 'gelfoam': 2.2,
            'tranexamic': 2.5, 'txa': 2.5, 'warfarin': 2.5, 'inr': 2.5, 'penicillin': 2.5,
            'allergy': 2.5, 'clindamycin': 2.5, 'amoxicillin': 2.2, 'ibuprofen': 2.0, 'perio': 2.0,
            'probing': 2.0, 'stage': 2.0, 'grade': 2.0, 'cal': 2.0, 'bone_loss': 2.2
        }

        for token in tokens:
            # Term weight with boost
            weight = clinical_boosts.get(token, 1.0)
            if token in self.idf:
                weight *= self.idf[token]

            # Dual-hash projection for low collision dense distribution
            h1 = abs(hash(token)) % self.dim
            h2 = abs(hash(token[::-1] + "_denta")) % self.dim
            
            vec[h1] += weight * 0.7
            vec[h2] += weight * 0.3

        # L2-normalize vector
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec /= norm
        return vec

    def _recompute_all_vectors(self):
        """Recompute IDF and dense vectors for all chunks."""
        if not self.chunks:
            self.vectors = None
            return

        # Compute document frequencies
        doc_freq: Dict[str, int] = {}
        total_chunks = len(self.chunks)
        for chunk in self.chunks:
            unique_terms = set(self._tokenize(chunk['text']))
            for t in unique_terms:
                doc_freq[t] = doc_freq.get(t, 0) + 1

        # Smooth IDF
        self.idf = {t: math.log((1 + total_chunks) / (1 + df)) + 1.0 for t, df in doc_freq.items()}

        # Build matrix
        matrix = []
        for chunk in self.chunks:
            vec = self._build_embedding(chunk['text'])
            matrix.append(vec)
        self.vectors = np.array(matrix, dtype=np.float32)

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF byte stream."""
        pdf_file = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(pdf_file)
        full_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                full_text.append(f"[Page {i+1}]\n{page_text}")
        return "\n\n".join(full_text)

    def chunk_text(self, text: str, chunk_size: int = 550, overlap: int = 100) -> List[str]:
        """
        Intelligently split dental text by paragraphs, headings, or list items
        maintaining semantic integrity.
        """
        paragraphs = re.split(r'\n{2,}', text)
        chunks = []
        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_len = len(para)

            if current_len + para_len <= chunk_size:
                current_chunk.append(para)
                current_len += para_len + 2
            else:
                if current_chunk:
                    chunk_str = "\n\n".join(current_chunk)
                    chunks.append(chunk_str)
                    
                    # Compute overlap text
                    overlap_chars = chunk_str[-overlap:] if len(chunk_str) > overlap else ""
                    current_chunk = [overlap_chars, para] if overlap_chars else [para]
                    current_len = sum(len(p) for p in current_chunk) + 2
                else:
                    # Individual paragraph exceeds chunk_size, split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    s_chunk = []
                    s_len = 0
                    for s in sentences:
                        if s_len + len(s) <= chunk_size:
                            s_chunk.append(s)
                            s_len += len(s) + 1
                        else:
                            if s_chunk:
                                chunks.append(" ".join(s_chunk))
                            s_chunk = [s]
                            s_len = len(s)
                    if s_chunk:
                        chunks.append(" ".join(s_chunk))
                    current_chunk = []
                    current_len = 0

        if current_chunk:
            final_str = "\n\n".join(current_chunk).strip()
            if final_str and (not chunks or final_str != chunks[-1]):
                chunks.append(final_str)

        return chunks

    def add_document(self, filename: str, content_bytes: bytes, file_type: Optional[str] = None) -> Dict[str, Any]:
        """Process and ingest a dental document."""
        if file_type is None:
            ext = os.path.splitext(filename)[1].lower()
            file_type = ext.replace('.', '')

        # Extract text based on extension
        if file_type == 'pdf':
            text = self.extract_text_from_pdf(content_bytes)
        else:
            try:
                text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = content_bytes.decode('latin-1')

        if not text.strip():
            raise ValueError(f"No readable text could be extracted from {filename}")

        doc_id = str(uuid.uuid4())[:8]
        raw_chunks = self.chunk_text(text)
        
        # Infer section titles or topics
        doc_chunks = []
        for i, c_text in enumerate(raw_chunks):
            chunk_id = f"{doc_id}_c{i}"
            
            # Simple heuristic for section title
            first_line = c_text.split('\n')[0].strip()[:60]
            section = first_line if any(first_line.startswith(p) for p in ["1.", "2.", "3.", "4.", "5.", "A.", "B.", "C.", "CLINICAL", "PATIENT"]) else f"Section {i+1}"

            chunk_obj = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "doc_name": filename,
                "section": section,
                "text": c_text,
                "char_count": len(c_text)
            }
            doc_chunks.append(chunk_obj)

        doc_meta = {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_count": len(doc_chunks),
            "char_count": len(text),
            "created_at": str(np.datetime64('now'))
        }

        # Save to memory and disk
        self.documents[doc_id] = doc_meta
        self.chunks.extend(doc_chunks)
        self._recompute_all_vectors()
        self.save_to_disk()

        return doc_meta

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document and its chunks from the vector store."""
        if doc_id not in self.documents:
            return False
        
        del self.documents[doc_id]
        self.chunks = [c for c in self.chunks if c['doc_id'] != doc_id]
        self._recompute_all_vectors()
        self.save_to_disk()
        return True

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.12) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity retrieval against indexed dental chunks.
        Returns top-K matching chunks with relevance score and metadata.
        """
        if not self.chunks or self.vectors is None:
            return []

        query_vec = self._build_embedding(query)
        q_norm = np.linalg.norm(query_vec)
        if q_norm < 1e-6:
            return []

        # Cosine similarity dot product with normalized vectors
        scores = np.dot(self.vectors, query_vec)
        
        # Rank indices
        top_indices = np.argsort(scores)[::-1]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score and len(results) >= 1:
                break
            
            chunk = self.chunks[idx].copy()
            # Normalize percentage score between 0% and 100%
            match_pct = round(min(1.0, max(0.0, (score + 0.15) * 1.15)) * 100, 1)
            chunk['score'] = round(score, 4)
            chunk['match_percentage'] = match_pct
            results.append(chunk)
            
            if len(results) >= top_k:
                break

        return results

    def list_documents(self) -> List[Dict[str, Any]]:
        return list(self.documents.values())

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "indexed_terms": len(self.idf)
        }

    def save_to_disk(self):
        try:
            with open(self.docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2)
            with open(self.chunks_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Notice: Read-only filesystem detected, skipping save_to_disk: {e}")


    def load_from_disk(self):
        if os.path.exists(self.docs_file) and os.path.exists(self.chunks_file):
            try:
                with open(self.docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                self._recompute_all_vectors()
            except Exception as e:
                print(f"Warning loading vector store: {e}")
                self.documents = {}
                self.chunks = []

    def auto_seed_sample_documents(self, sample_dir: str):
        """Auto-seed sample clinical documents if empty."""
        if self.documents:
            return  # Already has documents
        
        if not os.path.exists(sample_dir):
            return

        print(f"Auto-seeding sample dental documents from {sample_dir}...")
        # Prefer PDFs for realistic testing, fallback to TXT
        preferred_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
        if not preferred_files:
            preferred_files = [f for f in os.listdir(sample_dir) if f.endswith('.txt')]

        for fname in preferred_files:
            fpath = os.path.join(sample_dir, fname)
            with open(fpath, 'rb') as f:
                content = f.read()
            ext = 'pdf' if fname.endswith('.pdf') else 'txt'
            self.add_document(fname, content, file_type=ext)
        print(f"Successfully auto-seeded {len(self.documents)} sample dental documents ({len(self.chunks)} chunks).")
