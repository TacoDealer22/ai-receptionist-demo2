from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import openai
from elevenlabs.client import ElevenLabs

# === Setup ===
app = Flask(__name__)
CORS(app)

# === Load API keys ===
openai.api_key = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
voice_client = ElevenLabs(api_key=ELEVEN_API_KEY)

# === Static responses ===
static_responses = {
    "who created you": "I was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "what are your working hours": "I’m available 24/7 to answer your questions.",
    "where are you located": "I’m hosted online and always available.",
    "who is your owner": "My creator is OMAR ALJALLAD.",
    "who made you": "OMAR ALJALLAD is my developer.",
    "what's your name": "My name is Luna, your AI receptionist."
}

@app.route("/")
def home():
    return "AI Receptionist Luna is running!"

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").lower()

    for key, answer in static_responses.items():
        if key in question:
            return jsonify({"answer": answer})

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Luna, an AI receptionist created by Omar Aljallad."},
                {"role": "user", "content": question}
            ]
        )
        answer = resp.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception:
        return jsonify({"answer": "Sorry, something went wrong."}), 500

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "Hello, how can I help you?")
    try:
        audio = voice_client.text_to_speech.stream(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            text=text
        )
        return Response(audio, content_type="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
import uuid
from flask import Response

@app.route("/voice", methods=["POST"])
def voice():
    text = "Hello! This is Luna, your AI receptionist. How can I help you today?"
    filename = f"static/audio_{uuid.uuid4().hex}.mp3"
    
    audio = voice_client.text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        text=text
    )

    with open(filename, "wb") as f:
        f.write(audio)

    domain = os.getenv("RENDER_EXTERNAL_URL").rstrip("/")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{domain}/{filename}</Play>
</Response>
"""
    return Response(twiml, mimetype="text/xml")
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
