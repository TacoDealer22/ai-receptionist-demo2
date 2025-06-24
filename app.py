import os
import uuid
from flask import Flask, request, Response
import openai
import requests
from dotenv import load_dotenv

# Signature: Created by OMAR MAJDI MOHAMMAD ALJALLAD

load_dotenv()

app = Flask(__name__)

AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

openai.api_key = OPENAI_API_KEY

PREDEFINED_RESPONSES = {
    "what are your working hours": "We’re open from 9 AM to 6 PM, Sunday to Thursday.",
    "what are your business hours": "We operate Sunday through Thursday, from 9 in the morning to 6 in the evening.",
    "where are you located": "Our main office is located in Amman, Jordan.",
    "who created you": "I was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "what is your name": "My name is Luna. I’m your AI receptionist.",
    "who made luna": "Luna was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "are you an ai": "Yes, I’m an AI receptionist built to assist you quickly and clearly.",
    "what is the name of your company": "Omar's demo.",
    "what does your company do": "We provide AI Receptionist services through a subscription with our company.",
    "can i speak to someone": "I’ll forward your request. Please leave your name and message after the tone.",
    "can you call me back": "I’ll forward your request. Please leave your name and number after the tone.",
}

@app.route("/twiml", methods=["POST"])
def generate_twiml():
    user_input = request.form.get("SpeechResult", "").strip().lower()
    print("🎤 Twilio SpeechResult:", user_input)

    if not user_input:
        print("⚠️ No speech detected. Sending fallback.")
        fallback_text = "Sorry, I didn’t hear anything. Please try again later."
        fallback_audio = synthesize_speech(fallback_text)
        fallback_url = f"{request.url_root}static/audio/{fallback_audio}"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{fallback_url}</Play>
  <Redirect method="POST">/hangup</Redirect>
</Response>"""
        return Response(twiml, mimetype="text/xml")

    if any(kw in user_input for kw in ["goodbye", "bye", "thank you", "that's all", "no more questions"]):
        print("👋 Detected goodbye. Ending call.")
        goodbye_text = "Thank you for calling. Goodbye!"
        goodbye_audio = synthesize_speech(goodbye_text)
        goodbye_url = f"{request.url_root}static/audio/{goodbye_audio}"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{goodbye_url}</Play>
  <Hangup/>
</Response>"""
        return Response(twiml, mimetype="text/xml")

    answer = match_predefined_question(user_input)
    if answer:
        print("📌 Matched predefined question.")
        response_text = answer
    else:
        print("🧠 No match. Sending to GPT...")
        response_text = ask_gpt(user_input)

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
    audio_filename = synthesize_speech(prompt_text)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"
    print("🔁 Asking for another question.")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
</Response>"""
    return Response(twiml, mimetype="text/xml")

@app.route("/hangup", methods=["POST"])
def hangup_call():
    goodbye_text = "Thank you for calling. Goodbye!"
    audio_filename = synthesize_speech(goodbye_text)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"
    print("📞 Hanging up.")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
  <Hangup/>
</Response>"""
    return Response(twiml, mimetype="text/xml")

def ask_gpt(prompt):
    print("🔍 SENDING TO GPT:", prompt)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Luna, a helpful and polite AI receptionist who speaks clearly and naturally. "
                    "If someone asks who created you, respond with: 'I was created by OMAR MAJDI MOHAMMAD ALJALLAD.'"
                )
            },
            {"role": "user", "content": prompt}
        ]
    )
    gpt_reply = completion.choices[0].message["content"]
    print("✅ GPT replied:", gpt_reply)
    return gpt_reply

def match_predefined_question(user_input):
    normalized = user_input.lower().strip("?!.")
    for q, a in PREDEFINED_RESPONSES.items():
        if q in normalized:
            return a
    return None

def synthesize_speech(text):
    print("🎧 Synthesizing:", text[:60] + ("..." if len(text) > 60 else ""))
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

    print("✅ Audio saved as:", filename)
    return filename

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
