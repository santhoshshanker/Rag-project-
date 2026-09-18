import os
import io
import shutil
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.rag_engine import DentalVectorStore
from backend.llm_orchestrator import DentalLLMOrchestrator

app = FastAPI(
    title="Dental Assistant Copilot API",
    description="Clinical RAG and LLM Assistant for Dental Practitioners",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG vector database & LLM orchestrator
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_documents")

vector_store = DentalVectorStore(storage_dir=DATA_DIR)
llm_orchestrator = DentalLLMOrchestrator(config_file=os.path.join(DATA_DIR, "config.json"))

# Pre-seed sample documents if vector store is empty
vector_store.auto_seed_sample_documents(SAMPLE_DOCS_DIR)

# In-memory session & demo patient state
PATIENT_PRESETS = [
    {
        "id": "p1",
        "name": "John Doe",
        "age": 42,
        "gender": "Male",
        "treatment_type": "Oral Surgery & Implant",
        "medical_alerts": ["Penicillin Allergy (Severe)", "Hypertension (Controlled)"],
        "chief_complaint": "Severe throbbing lower left jaw pain, fractured tooth #19 on olive pit."
    },
    {
        "id": "p2",
        "name": "Emma Watson",
        "age": 8,
        "gender": "Female",
        "treatment_type": "Pediatric Trauma",
        "medical_alerts": ["Asthma (Albuterol PRN)", "Latex Sensitivity"],
        "chief_complaint": "Bicycle fall 40 minutes ago; tooth #8 avulsed, transported in cold milk."
    },
    {
        "id": "p3",
        "name": "Robert Vance",
        "age": 67,
        "gender": "Male",
        "treatment_type": "Periodontics & Extractions",
        "medical_alerts": ["Atrial Fibrillation on Warfarin (Coumadin)", "Type 2 Diabetes (HbA1c 6.8%)"],
        "chief_complaint": "Bleeding gums on brushing, tooth #30 mobility degree 2, planned extraction."
    },
    {
        "id": "p4",
        "name": "Maria Garcia",
        "age": 29,
        "gender": "Female",
        "treatment_type": "Endodontics",
        "medical_alerts": ["No Known Drug Allergies (NKDA)"],
        "chief_complaint": "Spontaneous lingering thermal sensitivity on upper right first molar (#3)."
    }
]

active_patient = PATIENT_PRESETS[0].copy()

DEMO_USERS = [
    {"username": "drsarah", "password": "password123", "name": "Dr. Sarah Lin, DDS", "role": "Lead Dental Surgeon", "license": "DDS-CA-88419"},
    {"username": "alexrda", "password": "password123", "name": "Alex Rivera, RDA", "role": "Registered Dental Assistant", "license": "RDA-CA-44910"},
    {"username": "demo", "password": "demo", "name": "Dr. Alex Taylor, DMD", "role": "General Dentist", "license": "DMD-DEMO-01"}
]

# Models
class QueryRequest(BaseModel):
    query: str
    patient_info: Optional[Dict[str, Any]] = None
    top_k: int = 3
    chat_history: Optional[List[Dict[str, str]]] = None

class PatientUpdateRequest(BaseModel):
    name: str
    age: int
    gender: str
    treatment_type: str
    medical_alerts: List[str]
    chief_complaint: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ConfigUpdateRequest(BaseModel):
    provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_model: Optional[str] = None
    temperature: Optional[float] = None

# Routes
@app.get("/api/health")
def health_check():
    stats = vector_store.get_stats()
    return {
        "status": "healthy",
        "service": "Dental Assistant Copilot",
        "vector_store": stats,
        "active_llm_provider": llm_orchestrator.config.get("provider", "builtin")
    }

@app.post("/api/auth/login")
def login(req: LoginRequest):
    for u in DEMO_USERS:
        if u["username"] == req.username and u["password"] == req.password:
            return {
                "success": True,
                "user": {
                    "username": u["username"],
                    "name": u["name"],
                    "role": u["role"],
                    "license": u["license"]
                },
                "token": f"mock-jwt-token-{u['username']}"
            }
    # Auto-allow any new username for easy classroom / clinic testing
    if len(req.username) >= 3 and len(req.password) >= 4:
        new_u = {
            "username": req.username,
            "name": f"Dr. {req.username.capitalize()}",
            "role": "Dental Clinician",
            "license": "LIC-PROV-99"
        }
        return {
            "success": True,
            "user": new_u,
            "token": f"mock-jwt-token-{req.username}"
        }
    raise HTTPException(status_code=401, detail="Invalid dental staff credentials. (Hint: Try username 'demo' and password 'demo')")

@app.get("/api/patient/presets")
def get_presets():
    return PATIENT_PRESETS

@app.get("/api/patient/current")
def get_current_patient():
    global active_patient
    return active_patient

@app.post("/api/patient/current")
def update_current_patient(req: PatientUpdateRequest):
    global active_patient
    active_patient = req.model_dump()
    return {"success": True, "patient": active_patient}

@app.get("/api/documents")
def list_documents():
    docs = vector_store.list_documents()
    stats = vector_store.get_stats()
    return {
        "documents": docs,
        "stats": stats
    }

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_dental_doc.txt"
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    if ext not in ['pdf', 'txt', 'md', 'json', 'csv']:
        raise HTTPException(status_code=400, detail="Only PDF, TXT, MD, JSON or CSV files are supported.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        doc_meta = vector_store.add_document(filename, content, file_type=ext)
        return {
            "success": True,
            "message": f"Successfully processed and indexed '{filename}'",
            "document": doc_meta,
            "stats": vector_store.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    success = vector_store.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "success": True,
        "message": f"Document {doc_id} deleted.",
        "stats": vector_store.get_stats()
    }

@app.get("/api/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str):
    chunks = [c for c in vector_store.chunks if c.get("doc_id") == doc_id]
    if not chunks and doc_id not in vector_store.documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"doc_id": doc_id, "chunks": chunks}

@app.post("/api/query")
def query_rag(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve top-K relevant chunks using semantic vector cosine similarity
    retrieved_chunks = vector_store.retrieve(req.query, top_k=req.top_k)

    # 2. Use patient info from request, or fallback to active patient
    p_info = req.patient_info or active_patient

    # 3. Generate grounded answer via LLM Orchestrator
    llm_result = llm_orchestrator.generate_answer(
        query=req.query,
        retrieved_chunks=retrieved_chunks,
        patient_info=p_info,
        chat_history=req.chat_history
    )

    # Return full RAG payload
    return {
        "query": req.query,
        "answer": llm_result["answer"],
        "provider_used": llm_result["provider_used"],
        "sources": llm_result["sources"],
        "suggested_followups": llm_result.get("suggested_followups", []),
        "retrieved_chunks_count": len(retrieved_chunks),
        "patient_context": {
            "name": p_info.get("name"),
            "age": p_info.get("age"),
            "treatment_type": p_info.get("treatment_type"),
            "medical_alerts": p_info.get("medical_alerts")
        }
    }

@app.get("/api/config")
def get_config():
    cfg = llm_orchestrator.config.copy()
    # Mask API keys for security in UI response
    if cfg.get("gemini_api_key"):
        cfg["gemini_api_key_masked"] = cfg["gemini_api_key"][:4] + "..." + cfg["gemini_api_key"][-4:]
    else:
        cfg["gemini_api_key_masked"] = ""

    if cfg.get("openai_api_key"):
        cfg["openai_api_key_masked"] = cfg["openai_api_key"][:4] + "..." + cfg["openai_api_key"][-4:]
    else:
        cfg["openai_api_key_masked"] = ""

    # Don't expose full key in GET
    cfg.pop("gemini_api_key", None)
    cfg.pop("openai_api_key", None)
    return cfg

@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    updates = {}
    if req.provider is not None:
        updates["provider"] = req.provider
    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        updates["gemini_api_key"] = req.gemini_api_key.strip()
    if req.openai_api_key is not None and req.openai_api_key.strip():
        updates["openai_api_key"] = req.openai_api_key.strip()
    if req.gemini_model is not None:
        updates["gemini_model"] = req.gemini_model
    if req.openai_model is not None:
        updates["openai_model"] = req.openai_model
    if req.temperature is not None:
        updates["temperature"] = req.temperature

    llm_orchestrator.save_config(updates)
    return {"success": True, "message": "Configuration updated successfully."}

# Mount static frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{full_path:path}")
    def serve_static(full_path: str):
        target = os.path.join(FRONTEND_DIR, full_path)
        if os.path.exists(target) and os.path.isfile(target):
            media_type = None
            if full_path.endswith('.css'):
                media_type = 'text/css'
            elif full_path.endswith('.js'):
                media_type = 'application/javascript'
            elif full_path.endswith('.json'):
                media_type = 'application/json'
            elif full_path.endswith('.svg'):
                media_type = 'image/svg+xml'
            elif full_path.endswith('.png'):
                media_type = 'image/png'
            return FileResponse(target, media_type=media_type)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
