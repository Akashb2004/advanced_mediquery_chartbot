import os
import sqlite3
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import google.generativeai as genai
except Exception:  # Library may not be installed yet during first read
    genai = None  # type: ignore

try:
    from dotenv import load_dotenv
    # Explicitly load .env from the backend directory regardless of CWD
    _ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
except Exception:
    # dotenv is optional; environment variables can be set via OS
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "mediquery.db")


def ensure_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_chat(user_message: str, bot_reply: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chats (timestamp, user_message, bot_reply) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), user_message, bot_reply),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 100) -> list[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, user_message, bot_reply FROM chats ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "user_message": r[2],
            "bot_reply": r[3],
        }
        for r in rows
    ]


TRIAGE_KEYWORDS = [
    "chest pain",
    "shortness of breath",
    "severe headache",
    "difficulty breathing",
    "loss of consciousness",
    "stroke",
    "heart attack",
    "uncontrolled bleeding",
]


DISCLAIMER = (
    "\n\n⚠️ This is not medical advice. Please consult a doctor."
)


def triage_prefix(message: str) -> str:
    lower = message.lower()
    for kw in TRIAGE_KEYWORDS:
        if kw in lower:
            return (
                "⚠️ Potentially serious symptoms detected. If this is an emergency, seek urgent medical care immediately.\n\n"
            )
    return ""


def suggest_specialist(message: str) -> str:
    """Very simple keyword-based specialist suggestion."""
    m = message.lower()
    if any(k in m for k in [
        "chest pain", "heart attack", "palpitations", "chest tightness", "angina",
        "heart", "cardiac", "pressure in chest", "radiating to arm"
    ]):
        return "Cardiologist"
    if any(k in m for k in ["shortness of breath", "wheezing", "asthma", "breathless", "breath difficulty"]):
        return "Pulmonologist"
    if any(k in m for k in ["severe headache", "stroke", "seizure", "numbness", "weakness on one side"]):
        return "Neurologist"
    if any(k in m for k in ["abdominal pain", "stomach pain", "vomit", "diarrhea", "acid reflux", "nausea"]):
        return "Gastroenterologist"
    if any(k in m for k in ["fever", "cough", "sore throat", "cold", "flu"]):
        return "General Physician"
    if any(k in m for k in ["rash", "itching", "acne", "eczema"]):
        return "Dermatologist"
    if any(k in m for k in [
        "joint pain", "arthritis", "back pain", "knee pain", "leg pain", "ankle pain",
        "bone pain", "fracture", "sprain", "fell", "fall", "injury", "swelling",
        "bruising", "tenderness", "limp", "hurt my leg", "hurt my arm"
    ]):
        return "Orthopedist"
    if any(k in m for k in ["burning urination", "urinary", "kidney stone"]):
        return "Urologist"
    if any(k in m for k in ["anxiety", "depression", "panic", "mental health"]):
        return "Psychiatrist"
    if any(k in m for k in ["eye pain", "vision loss", "blurry vision"]):
        return "Ophthalmologist"
    if any(k in m for k in ["tooth", "gum", "dental", "cavity", "toothache"]):
        return "Dentist"
    if any(k in m for k in ["ear pain", "throat", "sinus", "nose bleed", "ear ringing"]):
        return "ENT"
    return "General Physician"


def build_recommendations(message: str, urgent: bool) -> str:
    specialist = suggest_specialist(message)
    emergency_line = "Emergency: call 108 (India) or your local emergency number."
    next_steps = (
        "Next steps: rest the affected area, avoid heavy activity, use cold compress for 15-20 minutes, and consider OTC pain relief if safe."
    )
    lines = [f"Recommended specialist: {specialist}", next_steps, emergency_line]
    # If urgent, put emergency line first
    if urgent:
        lines = [emergency_line, f"Recommended specialist: {specialist}", next_steps]
    return "\n".join(lines)


# Basic medium-severity symptom keywords
MEDICAL_SYMPTOM_KEYWORDS = {
    "pain", "fever", "cough", "cold", "flu", "rash", "itch", "vomit", "nausea",
    "diarrhea", "breath", "wheezing", "headache", "dizzy", "dizziness", "sore throat",
    "infection", "swelling", "injury", "sprain", "fracture", "bleeding", "burn",
    "urination", "tooth", "gum", "acne", "eczema", "anxiety", "depression",
    "palpitations", "abdominal", "stomach", "chest", "back pain", "knee pain",
    "leg", "ankle", "bone", "fell", "fall"
}

# Non-medical greetings or chit-chat
NON_MEDICAL_GREETINGS = {
    "hi", "hello", "hey", "good morning", "good evening", "good night", "thanks",
    "thank you", "ok", "okay", "how are you", "what can you do", "who are you"
}


def should_include_recommendations(message: str, urgent: bool) -> bool:
    if urgent:
        return True
    text = message.lower().strip()
    # If it's clearly a greeting/chit-chat, skip
    for phrase in NON_MEDICAL_GREETINGS:
        if phrase in text and len(text) <= max(40, len(phrase) + 10):
            return False
    # Include if any medium-severity medical keywords appear
    return any(k in text for k in MEDICAL_SYMPTOM_KEYWORDS)


def classify_with_ai(model, message: str) -> dict:
    """Ask Gemini to classify severity and specialist based on the user's message.
    Returns a dict like {"severity": "minor|medium|severe|none", "specialist": "..."}
    """
    try:
        schema_prompt = (
            "Classify the user's medical concern. "
            "Respond ONLY in strict JSON with keys: severity, specialist.\n"
            "- severity: one of ['none','minor','medium','severe']\n"
            "- specialist: choose the most appropriate specialty from this list: "
            "['General Physician','Cardiologist','Pulmonologist','Neurologist','Gastroenterologist',"
            "'Dermatologist','Orthopedist','Urologist','Psychiatrist','Ophthalmologist','Dentist','ENT']\n"
            "For greetings or non-medical text, use severity='none' and specialist='General Physician'.\n\n"
            f"User: {message}"
        )
        resp = model.generate_content(schema_prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        # Attempt fallback extraction from candidates if needed
        if not raw and getattr(resp, "candidates", None):
            try:
                raw = resp.candidates[0].content.parts[0].text  # type: ignore
            except Exception:
                raw = "{}"
        import json
        data = json.loads(raw)
        sev = str(data.get("severity", "")).lower()
        spec = str(data.get("specialist", "")).strip() or "General Physician"
        if sev not in {"none", "minor", "medium", "severe"}:
            sev = "none"
        return {"severity": sev, "specialist": spec}
    except Exception:
        return {"severity": "none", "specialist": "General Physician"}


def build_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable"
        )
    if genai is None:
        raise RuntimeError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        )
    genai.configure(api_key=api_key)
    # Default reasonably capable text model
    return genai.GenerativeModel("gemini-1.5-flash")


app = Flask(__name__)
CORS(app)


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_message = (data or {}).get("message", "").strip()
        if not user_message:
            return jsonify({"error": "message is required"}), 400

        urgent_note = triage_prefix(user_message)

        model = build_gemini_client()
        # Get AI-based classification for better specialist mapping
        ai_cls = classify_with_ai(model, user_message)
        prompt = (
            "You are MediQuery, a helpful and cautious medical assistant. "
            "Provide concise, clear, and empathetic answers. "
            "If symptoms are serious, remind to seek urgent care. "
            "Avoid definitive diagnoses and avoid prescribing medications.\n\n"
            f"User: {user_message}"
        )
        response = model.generate_content(prompt)
        gemini_text = (getattr(response, "text", None) or "").strip()
        if not gemini_text and getattr(response, "candidates", None):
            # Fallback attempt extracting from candidates if needed
            try:
                gemini_text = response.candidates[0].content.parts[0].text  # type: ignore
            except Exception:
                gemini_text = "I'm sorry, I couldn't generate a response right now."

        is_urgent = urgent_note != "" or ai_cls.get("severity") == "severe"
        if should_include_recommendations(user_message, is_urgent) or ai_cls.get("severity") in {"medium", "severe"}:
            # Choose the most specific specialist: keyword rule overrides GP
            rule_spec = suggest_specialist(user_message)
            ai_spec = (ai_cls.get("specialist") or "General Physician").strip()
            specialist = rule_spec if rule_spec != "General Physician" else ai_spec
            emergency_line = "Emergency: call 108 (India) or your local emergency number."
            next_steps = "Suggested next steps: monitor symptoms, rest, stay hydrated, and seek in-person care if worsening."
            lines = [f"Suggested specialist: {specialist}", next_steps, emergency_line]
            if is_urgent:
                lines = [emergency_line, f"Suggested specialist: {specialist}", next_steps]
            recs = "\n".join(lines)
            full_reply = f"{urgent_note}{gemini_text}\n\n{recs}{DISCLAIMER}"
        else:
            full_reply = f"{urgent_note}{gemini_text}{DISCLAIMER}"

        save_chat(user_message, full_reply)

        return jsonify({"reply": full_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    try:
        limit = request.args.get("limit", default="100")
        try:
            limit_int = max(1, min(500, int(limit)))
        except ValueError:
            limit_int = 100
        items = get_history(limit_int)
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    ensure_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)



