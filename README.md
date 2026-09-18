# 🦷 Dental Assistant Copilot (Clinical RAG & LLM)

A modern, clinical-grade **Dental Assistant Copilot** web application built with **FastAPI**, **Retrieval-Augmented Generation (RAG)**, and **Multi-Provider LLM Integration** (Built-in Dental Clinical Engine, Google Gemini API, and OpenAI API).

Designed specifically for dental surgeons, periodontists, endodontists, hygienists, and registered dental assistants (RDAs) to provide immediate, evidence-grounded clinical decision support.

---

## ✨ Key Features

1. **Evidence-Grounded RAG Pipeline**:
   - Ingests dental clinical guidelines, ADA protocols, pharmacopeias, and electronic health records (EHR) in **PDF**, **TXT**, and **MD** formats.
   - Smart chunking with section-level dental metadata and semantic term boosting.
   - Vector search powered by dense embeddings and normalized Cosine Similarity.
   - Answers are strictly grounded in retrieved evidence to prevent hallucinations.
2. **Interactive Source Citations**:
   - Every AI recommendation displays visual source cards showing the document name, clinical section, and match percentage.
   - Click any source card to inspect the exact document chunk excerpt that supported the recommendation.
3. **Multi-turn Chat Copilot**:
   - Conversational thread maintaining clinical context.
   - Quick clinical prompt chips for rapid 1-click testing (e.g. Lidocaine pediatric dose, dry socket management, tooth avulsion splinting, NaOCl + Chlorhexidine chemical warning).
   - Clean markdown formatting with bolded dosages, action items, and clinical callouts.
4. **Active Patient Context & Safety Cross-Check**:
   - Dedicated patient profile panel: Name, Age, Biological Sex, Treatment Type, Medical Alerts & Drug Allergies, and Chief Complaint.
   - Pre-loaded patient scenarios:
     - **John Doe (42y)**: Oral Surgery & Implant, severe Penicillin allergy, Hypertension.
     - **Emma Watson (8y)**: Pediatric Trauma, avulsed permanent central incisor.
     - **Robert Vance (67y)**: Periodontics & Extractions on Warfarin (Coumadin), AFib, Diabetes.
     - **Maria Garcia (29y)**: Endodontics, acute pulpitis.
   - **Automated Safety Alerts**: The copilot cross-examines patient allergies (e.g. flagging Penicillin contraindications and recommending Clindamycin/Azithromycin) and cardiac epinephrine limits (max 0.04 mg / 2 cartridges for cardiac patients).
5. **Multi-Provider LLM Support**:
   - **Built-in Dental Clinical Engine**: 100% offline, zero external API keys needed—works immediately out-of-the-box!
   - **Google Gemini API**: `gemini-1.5-flash` / `gemini-2.5-flash`.
   - **OpenAI API**: `gpt-4o-mini` / `gpt-3.5-turbo`.
   - In-app Settings modal for easily switching providers and configuring keys.
6. **Clinical Safety Disclaimer**:
   - Prominent disclaimer clarifying that the copilot is a clinical reference tool and does not replace qualified dental examination or formal diagnosis.
7. **Clinical Staff Sign-In**:
   - Staff login with pre-configured quick demo accounts (Lead Dental Surgeon, RDA, General Dentist).
8. **Consultation Summary Export**:
   - 1-click export of the entire clinical consultation (Patient profile + Q&A dialogue + Citations + Disclaimer) to clipboard or EHR chart.

---

## 📁 Project Structure

```
vac project/
├── backend/
│   ├── __init__.py
│   ├── rag_engine.py          # Vector store, PDF/text parser, semantic chunking, cosine similarity
│   ├── llm_orchestrator.py    # LLM integration (Built-in Dental Engine, Gemini, OpenAI)
│   └── server.py              # FastAPI REST endpoints & static file serving
├── frontend/
│   ├── index.html             # Modern clinical dental interface
│   ├── styles.css             # Dental theme (Ocean Cyan, Dental Teal, Slate Navy)
│   └── app.js                 # State management, RAG querying, modals, patient sync
├── sample_documents/          # Authentic clinical guidelines (PDF & TXT formats)
│   ├── Local_Anesthesia_Dosing_and_Toxicity_Guidelines.pdf (.txt)
│   ├── Endodontic_Irrigation_and_Disinfection_Protocol.pdf (.txt)
│   ├── Post_Extraction_Care_and_Bleeding_Protocol.pdf (.txt)
│   ├── Pediatric_Dental_Trauma_and_Avulsion_Protocol.pdf (.txt)
│   ├── Periodontal_Screening_and_Stage_Grading.pdf (.txt)
│   └── Patient_Record_John_Doe_Tooth19.pdf (.txt)
├── scripts/
│   └── generate_sample_pdfs.py # Automated PDF generator for clinical guidelines
├── data/                      # Persistent vector store and config (auto-generated)
├── requirements.txt           # Python dependencies
├── main.py                    # Application launch script
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.9+ (Python 3.14 verified)
- Node.js (optional, only if using external build tools; the app runs on native vanilla web standards)

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python main.py
```

### 4. Open in Your Browser
Navigate to:
```
http://localhost:8000
```

---

## 🧪 Testing the Application (Sample Queries)

The application automatically seeds 6 comprehensive dental guidelines and clinical records on first run. You can test these queries right away:

1. **Pediatric Local Anesthesia Dosing**:
   - Select patient **Emma Watson (8y)**.
   - Query: `"What is the maximum lidocaine dose for a 30kg child?"`
   - *Result*: Calculates 4.4 mg/kg (132 mg lidocaine = 3.6 cartridges maximum) citing `Local_Anesthesia_Dosing_and_Toxicity_Guidelines.pdf`.

2. **Patient Allergy Cross-Check**:
   - Select patient **John Doe (42y, Penicillin Allergy)**.
   - Query: `"What antibiotic should I prescribe for acute apical abscess?"`
   - *Result*: Flags **Critical Allergy Alert** for Penicillin/Amoxicillin, recommending **Clindamycin 300 mg** or **Azithromycin 500 mg** grounded in `Patient_Record_John_Doe_Tooth19.pdf` and clinical guidelines.

3. **Endodontic Irrigation Chemical Warning**:
   - Query: `"Can I mix Sodium Hypochlorite and Chlorhexidine during canal irrigation?"`
   - *Result*: Warns against forming cytotoxic Parachloroaniline (PCA) brownish precipitate; mandates saline intermediate flush, citing `Endodontic_Irrigation_and_Disinfection_Protocol.pdf`.

4. **Dry Socket & Bleeding Management**:
   - Query: `"What is the protocol for dry socket (alveolar osteitis) and post-op bleeding?"`
   - *Result*: Cites warm saline irrigation, Alveogyl / Eugenol sedative dressing, biting on a damp black tea bag (tannic acid), and topical Tranexamic acid (TXA) from `Post_Extraction_Care_and_Bleeding_Protocol.pdf`.

---

## 🔒 Optional External LLM Keys
To use Google Gemini or OpenAI:
1. Click the **Settings** button in the top navigation bar.
2. Select **Google Gemini** or **OpenAI**.
3. Enter your API key and click **Save Configuration**.
4. Keys are saved locally in `data/config.json`.
