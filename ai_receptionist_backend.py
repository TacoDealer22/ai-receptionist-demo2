import os
import uuid
from flask import Flask, request, Response
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Ensure audio directory exists
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

openai.api_key = OPENAI_API_KEY

@app.route("/twiml", methods=["POST"])
def generate_twiml():
    user_input = request.form.get("SpeechResult", "").strip()

    if not user_input:
        fallback_text = "Sorry, I didn’t hear anything. If you have more questions, please call again."
        fallback_text += "\n\nThis AI receptionist was created by OMAR MAJDI MOHAMMAD ALJALLAD."
        fallback_audio = synthesize_speech(fallback_text)
        fallback_url = f"{request.url_root}static/audio/{fallback_audio}"

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{fallback_url}</Play>
  <Redirect method="POST">/hangup</Redirect>
</Response>"""
        return Response(twiml, mimetype="text/xml")

    response_text = ask_gpt(user_input)
    response_text += "\n\nThis AI receptionist was created by OMAR MAJDI MOHAMMAD ALJALLAD."

    audio_filename = synthesize_speech(response_text)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
  <Redirect method="POST">/next</Redirect>
</Response>"""
    return Response(twiml, mimetype="text/xml")

@app.route("/next", methods=["POST"])
def prompt_next_question():
    prompt_text = "You can ask another question, or say goodbye to end the call."
    prompt_text += "\n\nThis AI receptionist was created by OMAR MAJDI MOHAMMAD ALJALLAD."
    audio_filename = synthesize_speech(prompt_text)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
</Response>"""
    return Response(twiml, mimetype="text/xml")

@app.route("/hangup", methods=["POST"])
def hangup_call():
    goodbye_text = "Thank you for calling. Goodbye!"
    goodbye_text += "\n\nThis AI receptionist was created by OMAR MAJDI MOHAMMAD ALJALLAD."
    audio_filename = synthesize_speech(goodbye_text)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
  <Hangup/>
</Response>"""
    return Response(twiml, mimetype="text/xml")

def ask_gpt(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are Luna, a helpful and polite AI receptionist who speaks clearly and naturally."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]

def synthesize_speech(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"ElevenLabs API error: {response.text}")

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(AUDIO_DIR, filename)
    with open(path, "wb") as f:
        f.write(response.content)

    return filename

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
