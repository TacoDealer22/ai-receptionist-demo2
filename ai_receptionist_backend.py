import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from elevenlabs.client import ElevenLabs
from elevenlabs import save  # you can also import other functions if needed
from openai import OpenAI
import requests

app = Flask(__name__)
CORS(app)

# config
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", "5000"))

# initialize clients
eleven = ElevenLabs(api_key=ELEVEN_API_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# preset Q&A
PRESETS = {
    "name of the company": "Omar's Ai demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 am to 5 pm",
    "where are you located": "Jordan, Amman",
    "what does your company do": "We offer AI receptionist services",
}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    question = data.get("text", "").strip().lower()
    answer = PRESETS.get(question)
    
    if not answer:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}]
        )
        answer = resp.choices[0].message.content.strip()
    
    # generate voice audio
    audio = eleven.generate(text=answer, voice="Bella")
    file_path = f"response_{int(time.time())}.mp3"
    save(audio, file_path)
    
    # return link to audio (assuming your domain / static folder serves files)
    url = request.url_root.rstrip("/") + "/static/" + os.path.basename(file_path)
    return jsonify({"answer": answer, "audio_url": url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
