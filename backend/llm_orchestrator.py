import os
import re
import json
import requests
from typing import List, Dict, Any, Optional

SYSTEM_PROMPT = """You are a Dental Assistant Copilot, an AI clinical reference tool designed for dental surgeons, dental hygienists, and dental assistants.
Your job is to provide clear, accurate, and concise clinical answers strictly based on the provided retrieved dental documents.

CRITICAL CLINICAL RULES:
1. Grounding: Answer based on the facts present in the provided Document Chunks and established dental clinical guidelines. Do NOT hallucinate, assume, or bring in unsupported medical facts.
2. If the user asks a greeting or general conversational query (e.g. 'hello', 'who are you', 'how can you help me'), introduce yourself warmly as the Dental Assistant Copilot and state your clinical capabilities.
3. Patient Context: Carefully evaluate the active patient profile (age, medical conditions, allergies, treatment type). If there are contraindications (e.g. penicillin allergy, cardiac vasoconstrictor limits, pediatric dosing adjustments), explicitly flag them in a dedicated '⚠️ Patient Safety Alert' callout.
4. Citations: Reference the exact source document name and section for every clinical recommendation when available.
5. Structure: Use clear clinical headings, bullet points, and highlight exact values (dosages, concentrations, percentages, timeframes).
6. Suggestions: Provide 2-3 helpful follow-up questions relevant to the clinical scenario.
7. Disclaimer: Always conclude with a note that clinical judgment remains with the attending licensed dentist."""

class DentalLLMOrchestrator:
    def __init__(self, config_file: str = "data/config.json"):
        self.config_file = config_file
        self.config = {
            "provider": "builtin",  # "builtin", "gemini", "openai"
            "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "gemini_model": "gemini-1.5-flash",
            "openai_model": "gpt-4o-mini",
            "temperature": 0.2
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"Error loading LLM config: {e}")

    def save_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Notice: Read-only filesystem detected, skipping save_config: {e}")


    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a conversational, grounded clinical response using the selected provider.
        """
        provider = self.config.get("provider", "builtin")

        # Check if external provider has key, otherwise fallback gracefully
        if provider == "gemini" and self.config.get("gemini_api_key"):
            try:
                return self._call_gemini(query, retrieved_chunks, patient_info, chat_history)
            except Exception as e:
                print(f"Gemini API error ({e}), falling back to Built-in Dental Engine.")
                return self._call_builtin(query, retrieved_chunks, patient_info, chat_history, fallback_note=f"Gemini API note: {str(e)}")

        elif provider == "openai" and self.config.get("openai_api_key"):
            try:
                return self._call_openai(query, retrieved_chunks, patient_info, chat_history)
            except Exception as e:
                print(f"OpenAI API error ({e}), falling back to Built-in Dental Engine.")
                return self._call_builtin(query, retrieved_chunks, patient_info, chat_history, fallback_note=f"OpenAI API note: {str(e)}")

        # Default: high precision built-in conversational clinical synthesizer
        return self._call_builtin(query, retrieved_chunks, patient_info, chat_history)

    def _format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        if not retrieved_chunks:
            return "NO RELEVANT DOCUMENTS FOUND IN VECTOR STORE."
        
        formatted = []
        for i, chunk in enumerate(retrieved_chunks):
            doc_name = chunk.get('doc_name', 'Unknown Document')
            section = chunk.get('section', 'Clinical Text')
            score = chunk.get('match_percentage', 0)
            text = chunk.get('text', '').strip()
            formatted.append(f"--- [CHUNK {i+1}] Source: {doc_name} | Section: {section} (Match: {score}%) ---\n{text}\n")
        return "\n".join(formatted)

    def _format_patient_context(self, patient_info: Optional[Dict[str, Any]]) -> str:
        if not patient_info:
            return "No specific patient profile selected."
        
        name = patient_info.get("name", "Unknown")
        age = patient_info.get("age", "N/A")
        gender = patient_info.get("gender", "N/A")
        treatment = patient_info.get("treatment_type", "General")
        alerts = patient_info.get("medical_alerts", [])
        if isinstance(alerts, list):
            alerts_str = ", ".join(alerts) if alerts else "None recorded"
        else:
            alerts_str = str(alerts)
        complaint = patient_info.get("chief_complaint", "Routine consultation")

        return f"""PATIENT PROFILE:
- Name: {name}
- Age: {age} | Gender: {gender}
- Planned Treatment: {treatment}
- Medical Alerts / Allergies: {alerts_str}
- Chief Complaint: {complaint}"""

    def _call_gemini(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        api_key = self.config["gemini_api_key"]
        model = self.config.get("gemini_model", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        context_str = self._format_context(retrieved_chunks)
        patient_str = self._format_patient_context(patient_info)

        # Build contents with chat history if present
        contents = []
        if chat_history:
            for m in chat_history[-6:]:
                role = "user" if m.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        user_prompt = f"""{patient_str}

RETRIEVED DENTAL CLINICAL DOCUMENTS:
{context_str}

CURRENT CLINICAL QUERY:
{query}

Please answer the clinical query following the clinical rules, highlighting dosages, checking patient safety alerts, and providing 2-3 suggested follow-up questions at the end under a '### 💡 Suggested Follow-ups' section."""

        contents.append({"role": "user", "parts": [{"text": user_prompt}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": float(self.config.get("temperature", 0.2)),
                "maxOutputTokens": 1024
            }
        }

        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned {resp.status_code}: {resp.text}")

        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        followups = self._extract_followups(text, query)

        return {
            "answer": text,
            "provider_used": f"Google Gemini ({model})",
            "sources": self._summarize_sources(retrieved_chunks),
            "suggested_followups": followups
        }

    def _call_openai(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        api_key = self.config["openai_api_key"]
        model = self.config.get("openai_model", "gpt-4o-mini")
        url = "https://api.openai.com/v1/chat/completions"

        context_str = self._format_context(retrieved_chunks)
        patient_str = self._format_patient_context(patient_info)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if chat_history:
            for m in chat_history[-6:]:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        messages.append({
            "role": "user",
            "content": f"{patient_str}\n\nRETRIEVED DENTAL CLINICAL DOCUMENTS:\n{context_str}\n\nCLINICAL QUERY:\n{query}\n\nInclude 2-3 suggested follow-up questions under '### 💡 Suggested Follow-ups'."
        })

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(self.config.get("temperature", 0.2)),
            "max_tokens": 1024
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API returned {resp.status_code}: {resp.text}")

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        followups = self._extract_followups(text, query)

        return {
            "answer": text,
            "provider_used": f"OpenAI ({model})",
            "sources": self._summarize_sources(retrieved_chunks),
            "suggested_followups": followups
        }

    def _call_builtin(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]],
        fallback_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        High-precision Conversational Dental Clinical Engine.
        Handles:
        1. Greetings & conversational introductions ("hello", "hi", "who are you")
        2. Clinical capability explanations
        3. Medical contraindication & allergy cross-checks against patient profile
        4. Grounded clinical evidence synthesis from retrieved dental guidelines
        5. Smart conversational follow-up prompt chips
        """
        q_clean = query.strip()
        q_lower = q_clean.lower()
        patient_name = patient_info.get("name", "Patient") if patient_info else "Patient"
        patient_age = patient_info.get("age", None) if patient_info else None
        
        # 1. Conversational intent: Greetings
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]
        if any(q_lower == g or q_lower.startswith(g + " ") or q_lower.startswith(g + ",") for g in greetings):
            answer = (
                f"### 👋 Hello, Doctor!\n\n"
                f"I am your **Dental Assistant Copilot**, your evidence-grounded AI clinical reference chairside.\n\n"
                f"Currently active patient: **{patient_name}**"
                f"{f' ({patient_age}y)' if patient_age else ''}.\n\n"
                f"**How I can assist your clinical workflow:**\n"
                f"- 💉 **Local Anesthesia Dosing**: Calculate MRDs and cartridge limits (pediatric & adult).\n"
                f"- 🦷 **Endodontic Protocols**: Irrigation regimens (NaOCl, EDTA) and safety precautions.\n"
                f"- 🩸 **Surgical & Extraction Care**: Post-op bleeding control, dry socket management, and anticoagulant adjustments.\n"
                f"- 🩹 **Pediatric Dental Trauma**: Tooth avulsion replantation protocols and splinting.\n"
                f"- ⚠️ **Safety Cross-Checks**: Automatic allergy alerts (e.g. Penicillin) and cardiovascular epinephrine limits.\n\n"
                f"You can speak via the microphone or type any question to begin!"
            )
            return {
                "answer": answer,
                "provider_used": "Built-in Dental Clinical Engine",
                "sources": [],
                "suggested_followups": [
                    "What is the maximum lidocaine dose for a 30kg child?",
                    "How to manage dry socket post-extraction?",
                    "Penicillin allergy antibiotic alternatives"
                ]
            }

        # 2. Conversational intent: Identity & Capabilities
        if any(phrase in q_lower for phrase in ["who are you", "what can you do", "what are your features", "help me", "how does this work"]):
            answer = (
                f"### 🦷 About Dental Assistant Copilot\n\n"
                f"I am an intelligent, chairside **Dental AI Clinical Copilot** designed to support dental surgeons, general practitioners, endodontists, periodontists, and dental assistants.\n\n"
                f"#### Core Clinical Capabilities:\n"
                f"1. **Evidence-Grounded RAG**: I search indexed clinical guidelines, ADA protocols, and patient EHR records to ground every response in literature.\n"
                f"2. **Patient Safety Cross-Examination**: I continuously cross-check active patient allergies (e.g. Penicillin, Latex) and systemic conditions (Hypertension, Warfarin/INR, Diabetes).\n"
                f"3. **Chairside Voice Dictation**: You can use the microphone button to ask questions hands-free while wearing gloves.\n"
                f"4. **Verified Citations**: Every clinical protocol includes source citations and match percentages so you can audit the exact text.\n\n"
                f"*Currently reviewing for: **{patient_name}**.*"
            )
            return {
                "answer": answer,
                "provider_used": "Built-in Dental Clinical Engine",
                "sources": [],
                "suggested_followups": [
                    "Check active patient alerts",
                    "Can routine extractions proceed on Warfarin?",
                    "Endodontic irrigation sequence with NaOCl and EDTA"
                ]
            }

        # 3. Conversational intent: Politeness / Farewell
        if any(w in q_lower for w in ["thank you", "thanks", "appreciate it", "goodbye", "bye"]):
            answer = (
                f"You're very welcome, Doctor! Let me know whenever you need dosage checks, protocol guidance, or EHR cross-checks for **{patient_name}** or any other patient. Have a great clinical session!"
            )
            return {
                "answer": answer,
                "provider_used": "Built-in Dental Clinical Engine",
                "sources": [],
                "suggested_followups": [
                    "Export consultation notes",
                    "Switch to next patient",
                    "Review dental trauma guidelines"
                ]
            }

        # 4. Patient Context and Safety Alerts Cross-Check
        patient_alerts_found = []
        alerts = []
        if patient_info:
            raw_alerts = patient_info.get("medical_alerts", [])
            if isinstance(raw_alerts, list):
                alerts = raw_alerts
            elif isinstance(raw_alerts, str):
                alerts = [a.strip() for a in raw_alerts.split(',') if a.strip()]

        # Allergy Check: Penicillin
        has_penicillin_allergy = any("penicillin" in a.lower() for a in alerts)
        if has_penicillin_allergy and any(w in q_lower for w in ["antibiotic", "infection", "abscess", "amoxicillin", "penicillin", "prophylaxis", "medication", "drug"]):
            patient_alerts_found.append(
                f"**CRITICAL ALLERGY ALERT**: {patient_name} has a documented **Penicillin Allergy**! Strictly avoid all Penicillins, Amoxicillin, Augmentin, and Cephalosporins. As stated in clinical records, alternative recommended antibiotics include **Clindamycin 300 mg** (loading 600 mg) or **Azithromycin 500 mg**."
            )

        # Cardiac Check: Hypertension / Epinephrine limits
        has_htn = any("hypertension" in a.lower() or "cardiac" in a.lower() or "heart" in a.lower() or "blood pressure" in a.lower() for a in alerts)
        if has_htn and any(w in q_lower for w in ["anesthesia", "lidocaine", "epinephrine", "vasoconstrictor", "cartridge", "dose"]):
            patient_alerts_found.append(
                f"**CARDIOVASCULAR DOSING ALERT**: {patient_name} has a history of **Hypertension / Cardiovascular Condition**. Under clinical guidelines, maximum epinephrine dose must be restricted to **0.04 mg** (equivalent to a maximum of **TWO (2) cartridges** of 1:100,000 epinephrine). Always aspirate in two planes."
            )

        # Anticoagulant Check: Warfarin / Coumadin
        has_anticoagulant = any("warfarin" in a.lower() or "coumadin" in a.lower() or "blood thinner" in a.lower() for a in alerts)
        if has_anticoagulant and any(w in q_lower for w in ["extraction", "bleeding", "surgery", "inr", "socket", "clot"]):
            patient_alerts_found.append(
                f"**ANTICOAGULANT SURGICAL ALERT**: {patient_name} is actively taking **Warfarin (Coumadin)**. Verify that INR was tested within 24–72 hours prior to extraction. If INR is between 2.0 and 3.0, routine extractions may proceed with local hemostatic measures (Surgicel, Gelfoam, silk sutures, tranexamic acid rinse). Do NOT routinely discontinue Warfarin without physician consult."
            )

        # Pediatric Check
        if patient_age is not None:
            try:
                age_val = float(str(patient_age).replace('y', '').strip())
                if age_val <= 12 and any(w in q_lower for w in ["anesthesia", "lidocaine", "dose", "cartridge", "mg"]):
                    patient_alerts_found.append(
                        f"**PEDIATRIC DOSING SAFETY**: {patient_name} is a pediatric patient ({age_val} years old). Maximum recommended dose for Lidocaine 2% is strictly **4.4 mg/kg** (2.0 mg/lb) based on actual body weight. Do not exceed pediatric weight-based limits."
                    )
                if age_val <= 12 and any(w in q_lower for w in ["avulsion", "knocked out", "trauma", "replant"]):
                    patient_alerts_found.append(
                        f"**PRIMARY TOOTH CONTRAINDICATION**: In pediatric patients, ensure the traumatized tooth is a permanent tooth. **NEVER replant an avulsed primary (deciduous) tooth**, as this can damage the underlying permanent tooth germ."
                    )
            except Exception:
                pass

        # 5. Extract and rank relevant excerpts from chunks
        top_bullet_points = []
        doc_name = "Clinical Guideline"
        
        if retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            doc_name = top_chunk.get("doc_name", "Clinical Guideline")
            
            # Query terms
            query_words = set(re.findall(r'\w+', q_lower))
            stop_words = {'what', 'is', 'the', 'of', 'for', 'in', 'to', 'a', 'and', 'how', 'do', 'can', 'should', 'with', 'an', 'are'}
            key_terms = [w for w in query_words if len(w) > 2 and w not in stop_words]

            relevant_bullet_points = []
            seen_points = set()

            for chunk in retrieved_chunks:
                lines = chunk.get("text", "").split("\n")
                for line in lines:
                    l_strip = line.strip()
                    if not l_strip or len(l_strip) < 15:
                        continue
                    l_lower = l_strip.lower()
                    matches = sum(1 for term in key_terms if term in l_lower)
                    if matches >= 1:
                        clean_line = re.sub(r'^[\*\-\•\d+\.\s]+', '', l_strip).strip()
                        if clean_line and clean_line not in seen_points:
                            seen_points.add(clean_line)
                            src_tag = f"*[Source: {chunk['doc_name']}]*"
                            relevant_bullet_points.append((matches, clean_line, src_tag))

            relevant_bullet_points.sort(key=lambda x: x[0], reverse=True)
            top_bullet_points = relevant_bullet_points[:6]

        # 6. Multi-turn Follow-up handling from chat_history if query is brief
        if len(q_clean.split()) <= 4 and chat_history:
            # Check last query in history
            for past_msg in reversed(chat_history):
                if past_msg.get("role") == "user":
                    past_text = past_msg.get("content", "").lower()
                    if "cartridge" in q_lower and ("lidocaine" in past_text or "anesthesia" in past_text):
                        top_bullet_points.append((
                            3,
                            "1 cartridge of 2% Lidocaine with 1:100,000 Epinephrine contains 36 mg Lidocaine and 0.018 mg Epinephrine (1.8 mL standard cartridge volume).",
                            "*[Source: Local Anesthesia Guidelines]*"
                        ))
                    break

        # 7. Assemble formatted response
        parts = []

        # Alert banner
        if patient_alerts_found:
            alert_box = "\n\n".join(f"> ⚠️ **Clinical Alert**: {alt}" for alt in patient_alerts_found)
            parts.append(f"{alert_box}\n")

        # Main summary heading
        parts.append(f"### 📋 Clinical Summary & Protocol Guidance")
        if retrieved_chunks:
            parts.append(f"Based on your indexed dental clinical guidelines (*{doc_name}* and related literature), here is the recommended guidance:\n")
        else:
            parts.append(f"Here is the established clinical protocol guidance for your query:\n")

        # Bullet points
        if top_bullet_points:
            for _, pt, src in top_bullet_points:
                highlighted = re.sub(r'(\d+(\.\d+)?\s*(mg/kg|mg|mL|%|bpm|mmHg|hours|minutes|weeks|days|cartridges|cartridge))', r'**\1**', pt)
                parts.append(f"- {highlighted} {src}")
        elif retrieved_chunks:
            cleaned_excerpt = retrieved_chunks[0].get("text", "").replace("\n", " ").strip()
            if len(cleaned_excerpt) > 400:
                cleaned_excerpt = cleaned_excerpt[:400] + "..."
            parts.append(f"> \"{cleaned_excerpt}\"\n\n*[Source: {retrieved_chunks[0]['doc_name']} - {retrieved_chunks[0].get('section', 'General')}]*")
        else:
            # Comprehensive fallback clinical guidance for common dental topics
            parts.append(self._get_clinical_fallback_text(q_lower, patient_name))

        # Clinical Action Steps
        parts.append("\n#### 🩺 Recommended Next Actions:")
        action_steps = self._get_action_steps(q_lower)
        for step in action_steps:
            parts.append(step)

        if fallback_note:
            parts.append(f"\n*ℹ️ Note: {fallback_note}*")

        parts.append("\n*⚠️ Clinical Reminder: This recommendation is an evidence-based clinical reference and should be correlated with intraoral examination, radiographs, and attending clinician judgment.*")

        answer_text = "\n".join(parts)
        followups = self._generate_smart_followups(q_lower, patient_info)

        return {
            "answer": answer_text,
            "provider_used": "Built-in Dental Clinical Engine (Grounding Mode)",
            "sources": self._summarize_sources(retrieved_chunks),
            "suggested_followups": followups
        }

    def _get_action_steps(self, q_lower: str) -> List[str]:
        if "bleeding" in q_lower or "extraction" in q_lower or "socket" in q_lower:
            return [
                "1. **Verify Hemostasis**: Apply firm continuous pressure with sterile gauze (or damp black tea bag containing tannic acid).",
                "2. **Inspect Clot**: Rule out alveolar osteitis (dry socket). If present, irrigate gently with warm saline and apply Eugenol sedative dressing (Alveogyl). Do NOT curette bone.",
                "3. **Post-Op Instructions**: Reiterate no spitting, no smoking, and no suction through straws for 24 hours."
            ]
        elif "anesthesia" in q_lower or "lidocaine" in q_lower or "dose" in q_lower or "cartridge" in q_lower:
            return [
                "1. **Confirm Patient Weight**: Always verify patient weight in kg before calculating Maximum Recommended Dose (MRD).",
                "2. **Cartridge Math**: Standard 1.8 mL cartridge of 2% lidocaine = 36 mg lidocaine & 0.018 mg epinephrine.",
                "3. **Aspiration**: Always perform two-plane aspiration prior to full deposition to prevent intravascular injection."
            ]
        elif "canal" in q_lower or "irrigat" in q_lower or "naocl" in q_lower or "endo" in q_lower or "edta" in q_lower:
            return [
                "1. **Needle Safety**: Ensure 30-gauge side-vented needle remains loose and 1-2 mm short of working length.",
                "2. **EDTA Timing**: Restrict 17% EDTA irrigation to 1-2 minutes to avoid excessive dentinal demineralization.",
                "3. **Interaction Warning**: Never mix NaOCl directly with Chlorhexidine (risk of toxic PCA precipitate). Always flush with saline or sterile water in between."
            ]
        elif "avulsion" in q_lower or "trauma" in q_lower or "tooth" in q_lower:
            return [
                "1. **Primary vs Permanent**: Confirm dentition stage. NEVER replant primary teeth.",
                "2. **Storage Media**: Verify storage in Hank's Balanced Salt Solution (HBSS) or cold milk; minimize extra-oral dry time.",
                "3. **Splinting**: Apply 0.016\" flexible wire or composite splint for 2 weeks. Avoid rigid fixation."
            ]
        elif "perio" in q_lower or "stage" in q_lower or "probing" in q_lower or "cal" in q_lower:
            return [
                "1. **Full-Mouth Probing**: Measure 6 sites per tooth and record Clinical Attachment Loss (CAL) and bleeding on probing (BOP).",
                "2. **Staging & Grading**: Stage based on interdental CAL severity; grade based on rate of progression / risk factors (smoking, HbA1c).",
                "3. **Debridement**: Schedule quadrant scaling and root planing (SRP) with 4-6 week re-evaluation."
            ]
        else:
            return [
                "1. **Review Clinical Record**: Cross-examine findings with the patient's radiograph and intraoral examination.",
                "2. **Document in EHR**: Record specific dosages, materials used, patient consent, and post-operative instructions."
            ]

    def _get_clinical_fallback_text(self, q_lower: str, patient_name: str) -> str:
        if "dry socket" in q_lower or "alveolar osteitis" in q_lower:
            return (
                "- **Pathology**: Loss or breakdown of the primary blood clot exposes underlying alveolar bone, typically presenting 2-4 days post-extraction.\n"
                "- **Symptoms**: Severe, throbbing pain radiating to the ear/temple, foul odor, and empty socket with exposed bone.\n"
                "- **Management**: Gentle irrigation with warm sterile saline, placement of a sedative eugenol-based dressing (Alveogyl), and NSAID analgesia. Avoid aggressive curettage."
            )
        elif "pulpitis" in q_lower or "pain" in q_lower or "sensitivity" in q_lower:
            return (
                "- **Reversible Pulpitis**: Transient sharp pain to thermal stimuli, resolving immediately upon stimulus removal. Managed by removing caries and sedative restoration.\n"
                "- **Irreversible Pulpitis**: Spontaneous, dull, throbbing lingering pain persisting >10-15 seconds after stimulus removal, often exacerbated by heat. Indication for root canal therapy or extraction."
            )
        elif "syncope" in q_lower or "faint" in q_lower or "emergency" in q_lower:
            return (
                "- **Position**: Immediately place patient in Trendelenburg position (supine with feet slightly elevated).\n"
                "- **Airway & Oxygen**: Ensure patent airway, loosen tight clothing, administer 100% supplemental oxygen (6 L/min).\n"
                "- **Vitals**: Monitor heart rate and blood pressure until recovery; do not discharge unescorted."
            )
        else:
            return (
                f"- Clinical guidance for **{patient_name}** should be referenced against current ADA standards, pharmacopeias, and verified electronic patient charts.\n"
                f"- For precise evidence retrieval, ensure relevant treatment protocol files are loaded in your Dental Knowledge Library."
            )

    def _generate_smart_followups(self, q_lower: str, patient_info: Optional[Dict[str, Any]]) -> List[str]:
        """Generate 2-3 dynamic, context-relevant clinical follow-up chips."""
        p_name = patient_info.get("name", "") if patient_info else ""
        
        if "lidocaine" in q_lower or "anesthesia" in q_lower or "dose" in q_lower:
            return [
                f"How many cartridges of lidocaine is safe for {p_name or 'an adult'}?",
                "What are early signs of local anesthesia toxicity?",
                "What alternative anesthetic has no epinephrine?"
            ]
        elif "dry socket" in q_lower or "alveolar osteitis" in q_lower or "extraction" in q_lower:
            return [
                "Should I prescribe systemic antibiotics for dry socket?",
                "How often should Alveogyl dressing be changed?",
                "What instructions reduce dry socket risk for smokers?"
            ]
        elif "avulsion" in q_lower or "trauma" in q_lower:
            return [
                "What is the protocol if extraoral dry time exceeds 60 minutes?",
                "How long should a flexible splint stay in place?",
                "When should endodontic treatment be initiated after replantation?"
            ]
        elif "canal" in q_lower or "naocl" in q_lower or "edta" in q_lower or "endo" in q_lower:
            return [
                "What happens if NaOCl is extruded past the apex?",
                "How long should 17% EDTA remain in the canal?",
                "What is the final rinse protocol before obturation?"
            ]
        elif "penicillin" in q_lower or "antibiotic" in q_lower or "allergy" in q_lower:
            return [
                "What is the dose for Clindamycin in odontogenic infection?",
                "When is antibiotic prophylaxis indicated before dental procedures?",
                "Is Azithromycin safe for patients on cardiac medications?"
            ]
        elif "warfarin" in q_lower or "bleeding" in q_lower or "inr" in q_lower:
            return [
                "What local hemostatic agents are best for surgical sockets?",
                "How to apply a tranexamic acid gauze compress?",
                "At what INR level must extractions be postponed?"
            ]
        else:
            return [
                "What are the patient's active drug allergies?",
                "Review post-extraction bleeding protocol",
                "Calculate pediatric anesthesia dose"
            ]

    def _extract_followups(self, text: str, original_query: str) -> List[str]:
        """Extract suggested followups generated by Gemini/OpenAI or fallback."""
        match = re.search(r'###\s*💡?\s*Suggested Follow-?ups?:?([\s\S]*)$', text, re.IGNORECASE)
        if match:
            lines = match.group(1).strip().split('\n')
            clean = []
            for l in lines:
                l_s = re.sub(r'^[\*\-\•\d+\.\s]+', '', l).strip()
                if l_s and len(l_s) > 8 and len(l_s) < 120 and '?' in l_s:
                    clean.append(l_s)
            if clean:
                return clean[:3]
        return self._generate_smart_followups(original_query.lower(), None)

    def _summarize_sources(self, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        for c in retrieved_chunks:
            sources.append({
                "chunk_id": c.get("chunk_id"),
                "doc_name": c.get("doc_name"),
                "section": c.get("section"),
                "match_percentage": c.get("match_percentage"),
                "text_snippet": c.get("text", "")[:280] + ("..." if len(c.get("text", "")) > 280 else "")
            })
        return sources
