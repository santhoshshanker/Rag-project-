import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag_engine import DentalVectorStore
from backend.llm_orchestrator import DentalLLMOrchestrator

def run_tests():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    sample_docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_documents")

    vector_store = DentalVectorStore(storage_dir=data_dir)
    vector_store.auto_seed_sample_documents(sample_docs_dir)
    llm = DentalLLMOrchestrator(config_file=os.path.join(data_dir, "config.json"))

    print("1. Testing Vector Store Stats ...")
    stats = vector_store.get_stats()
    print("   Total docs:", stats["total_documents"], "| Total chunks:", stats["total_chunks"])
    assert stats["total_documents"] >= 1, "Expected indexed documents!"

    print("\n2. Testing Greeting & Conversational Intent ...")
    res = llm.generate_answer(
        query="Hello, who are you and how can you help me?",
        retrieved_chunks=[]
    )
    print("   Answer snippet:", res["answer"][:120].replace('\n', ' '))
    print("   Suggested followups:", res.get("suggested_followups"))
    assert len(res.get("suggested_followups", [])) >= 2, "Followups missing!"

    print("\n3. Testing Clinical Query (Lidocaine Dosing) ...")
    query = "What is the maximum lidocaine dose for a 30kg child?"
    chunks = vector_store.retrieve(query, top_k=3)
    assert len(chunks) > 0, "No chunks retrieved for lidocaine!"
    res = llm.generate_answer(query=query, retrieved_chunks=chunks)
    print("   Answer snippet:", res["answer"][:120].replace('\n', ' '))
    print("   Sources count:", len(res["sources"]))
    assert len(res["sources"]) > 0, "Expected sources for lidocaine query!"

    print("\n4. Testing Patient Safety Allergy Flag (John Doe - Penicillin Allergy) ...")
    query = "What antibiotic should I prescribe for odontogenic infection?"
    chunks = vector_store.retrieve(query, top_k=3)
    p_info = {
        "name": "John Doe",
        "age": 42,
        "treatment_type": "Oral Surgery",
        "medical_alerts": ["Penicillin Allergy (Severe)"]
    }
    res = llm.generate_answer(query=query, retrieved_chunks=chunks, patient_info=p_info)
    assert "penicillin" in res["answer"].lower() and "allergy" in res["answer"].lower(), "Allergy flag not triggered!"
    print("   Safety Alert properly flagged Penicillin allergy!")

    print("\n5. Testing Static Files exist on disk ...")
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    for f in ["index.html", "styles.css", "app.js"]:
        fpath = os.path.join(frontend_dir, f)
        assert os.path.exists(fpath), f"Missing {f}!"
        size = os.path.getsize(fpath)
        print(f"   {f} verified ({size} bytes)")

    print("\nALL DIRECT VERIFICATION TESTS PASSED SUCCESSFULLY! 🦷✨")

if __name__ == "__main__":
    run_tests()
