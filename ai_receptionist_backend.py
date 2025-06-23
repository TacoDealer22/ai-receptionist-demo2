import os
import uuid
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import requests

app = Flask(__name__)
CORS(app)

# ====== SET YOUR KEYS AS ENV VARIABLES ======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = "Rachel"  # Change to another ElevenLabs voice if needed
# ============================================

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/webhook", methods=["POST"])
def handle_call():
    speech_text = request.form.get("SpeechResult", "")
    if not speech_text:
        return "No speech received", 400

    print(f"[+] Incoming speech: {speech_text}")

    # Step 1: Get AI response
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a friendly and helpful AI receptionist named Luna. Company name is Omar's demo. We are located in Jordan. We offer AI receptionist services. The working hours are from 9 AM to 5 PM. If asked who created you, say Omar Aljallad and Asa'd Alalami."},
            {"role": "user", "content": speech_text}
        ]
    )
    ai_reply = response.choices[0].message.content.strip()
    print(f"[+] GPT reply: {ai_reply}")

    # Step 2: Convert text to speech using ElevenLabs
    audio_url = generate_elevenlabs_audio(ai_reply)
    if not audio_url:
        return "Error generating audio", 500

    # Step 3: Return TwiML to Twilio
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Pause length="2"/>
    <Redirect>/webhook</Redirect>
</Response>"""

    return twiml, 200, {'Content-Type': 'application/xml'}

def generate_elevenlabs_audio(text):
    try:
        filename = f"{uuid.uuid4()}.mp3"
        filepath = f"static/{filename}"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"

        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            print(f"ElevenLabs Error: {response.text}")
            return None

        with open(filepath, "wb") as f:
            f.write(response.content)

        return f"https://ai-receptionist-demo2.onrender.com/static/{filename}"

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

@app.route('/static/<path:filename>')
def serve_audio(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)
