from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS
import openai
from elevenlabs import save
from elevenlabs.client import ElevenLabs
import os
import shutil

app = Flask(__name__)
CORS(app)

# Load API keys from env
openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# ElevenLabs client
tts = ElevenLabs(api_key=elevenlabs_api_key)

@app.route("/webhook", methods=["POST"])
def webhook():
    user_text = request.json.get("SpeechResult", "")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_text}]
    )

    reply = response['choices'][0]['message']['content']

    audio = tts.generate(
        text=reply,
        voice="Rachel",
        model="eleven_monolingual_v1"
    )

    os.makedirs("static", exist_ok=True)
    save(audio, "/tmp/response.mp3")
    shutil.copy("/tmp/response.mp3", "static/response.mp3")

    return {"reply": reply}

@app.route("/voice", methods=["GET"])
def voice():
    audio = tts.generate(
        text="Hello and welcome to our AI receptionist! How can I assist you today?",
        voice="Rachel",
        model="eleven_monolingual_v1"
    )

    os.makedirs("static", exist_ok=True)
    save(audio, "/tmp/ai_greeting.mp3")
    shutil.copy("/tmp/ai_greeting.mp3", "static/ai_greeting.mp3")

    xml = f"""
    <Response>
        <Play>https://ai-receptionist-demo2.onrender.com/static/ai_greeting.mp3</Play>
    </Response>
    """
    return Response(xml, mimetype="text/xml")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

iif __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
