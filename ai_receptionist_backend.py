from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from elevenlabs import generate, save, set_api_key
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

openai.api_key = OPENAI_API_KEY
set_api_key(ELEVEN_API_KEY)

# Preset answers
PRESETS = {
    "name of the company": "Omar's AI demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 am to 5 pm",
    "where are you located": "Jordan, Amman",
    "what does your company do": "Offers AI receptionist services",
}

@app.route("/")
def home():
    return "AI Receptionist backend is running!"

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    question = data.get("SpeechResult", "").strip().lower()

    if not question:
        return Response("<Response><Say>I didn't catch that. Please repeat.</Say></Response>", mimetype="text/xml")

    # Answer logic
    answer = PRESETS.get(question)
    if not answer:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful AI receptionist."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            return Response(f"<Response><Say>Sorry, there was an error: {str(e)}</Say></Response>", mimetype="text/xml")

    # Generate audio with ElevenLabs
    filename = f"{uuid.uuid4()}.mp3"
    filepath = f"static/{filename}"
    try:
        audio = generate(text=answer, voice="Rachel", model="eleven_monolingual_v1")
        save(audio, filepath)
        audio_url = f"https://{request.host}/static/{filename}"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""
        return Response(twiml, mimetype="text/xml")
    except Exception as e:
        return Response(f"<Response><Say>Sorry, audio failed: {str(e)}</Say></Response>", mimetype="text/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
