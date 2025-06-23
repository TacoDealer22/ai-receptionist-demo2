# ai_receptionist_backend.py

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import tempfile

# === Load environment variables ===
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

openai.api_key = OPENAI_API_KEY
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# === Flask setup ===
app = Flask(__name__)
CORS(app)

# === Static answers ===
PRESETS = {
    "name of the company": "Omar's Ai demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 am to 5 pm",
    "where are you located": "Jordan, Amman",
    "what does your company do": "Offers AI receptionist services",
}

# === Generate response logic ===
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

# === Text-only Q&A for frontend ===
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

# === Voice webhook for Twilio ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        question = request.values.get("SpeechResult", "").strip()
        if not question:
            return jsonify({"error": "No speech input"}), 400

        answer = generate_answer(question)

        # ElevenLabs voice generation
        audio = client.text_to_speech.convert(
            text=answer,
            voice_id="EXAVITQu4vr4xnSDxMaL",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            temp_path = f.name

        return send_file(temp_path, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Run server ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
