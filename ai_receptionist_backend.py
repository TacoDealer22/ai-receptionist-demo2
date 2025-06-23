# ai_receptionist_backend.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from elevenlabs import generate, Voice, VoiceSettings, set_api_key
import tempfile

# === Load environment variables ===
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

openai.api_key = OPENAI_API_KEY
set_api_key(ELEVENLABS_API_KEY)

app = Flask(__name__)
CORS(app)

# === Static Presets ===
PRESETS = {
    "name of the company": "Omar's Ai demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 am to 5 pm",
    "where are you located": "Jordan, Amman",
    "what does your company do": "Offers AI receptionist services",
}

# === Function to get answer ===
def generate_answer(user_question):
    normalized = user_question.strip().lower()
    if normalized in PRESETS:
        return PRESETS[normalized]
    
    # fallback to GPT
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_question},
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()

# === Route for frontend usage ===
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        question = data.get("question", "")
        if not question:
            return jsonify({"error": "No question provided"}), 400
        answer = generate_answer(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Route for Twilio webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        question = request.values.get("SpeechResult", "").strip()
        if not question:
            return jsonify({"error": "No speech detected"}), 400
        
        answer = generate_answer(question)

        # Generate voice using ElevenLabs
        audio = generate(
            text=answer,
            voice=Voice(
                voice_id="EXAVITQu4vr4xnSDxMaL",
                settings=VoiceSettings(stability=0.5, similarity_boost=0.5)
            )
        )

        # Save to temp file and return local file path URL
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            audio_path = f"/static/{os.path.basename(f.name)}"

        return jsonify({"audio_url": f"https://ai-receptionist-demo2.onrender.com{audio_path}"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Run the Flask app ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
