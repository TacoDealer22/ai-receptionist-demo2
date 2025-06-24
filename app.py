import os
import uuid
from flask import Flask, request, Response
import openai
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

openai.api_key = OPENAI_API_KEY

PREDEFINED_QA = {
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
    "can you call me back": "I’ll forward your request. Please leave your name and number after the tone."
}

@app.route("/", methods=["GET"])
def home():
    return "Luna is live."

@app.route("/twiml", methods=["POST"])
def generate_twiml():
    user_input = request.form.get("SpeechResult", "").strip().lower()
    print(f"🎤 Twilio SpeechResult: {user_input}")

    if not user_input:
        print("⚠️ No input received — using fallback response.")
        fallback_text = "Sorry, I didn’t hear anything. If you have more questions, please call again."
        fallback_audio = synthesize_speech(fallback_text)
        audio_url = f"{request.url_root}static/audio/{fallback_audio}"
        return twiml_play_and_redirect(audio_url, "/hangup")

    for question, answer in PREDEFINED_QA.items():
        if question in user_input:
            print(f"📌 Matched predefined Q&A: {question}")
            audio_filename = synthesize_speech(answer)
            audio_url = f"{request.url_root}static/audio/{audio_filename}"
            return twiml_play_and_redirect(audio_url, "/next")

    print("💬 Sending to OpenAI (fallback)...")
    try:
        gpt_answer = ask_gpt(user_input)
        audio_filename = synthesize_speech(gpt_answer)
        audio_url = f"{request.url_root}static/audio/{audio_filename}"
        return twiml_play_and_redirect(audio_url, "/next")
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        error_audio = synthesize_speech("Sorry, something went wrong. Please try again later.")
        audio_url = f"{request.url_root}static/audio/{error_audio}"
        return twiml_play_and_redirect(audio_url, "/hangup")

@app.route("/next", methods=["POST"])
def next_question():
    prompt = "You can ask another question, or say goodbye to end the call."
    audio_filename = synthesize_speech(prompt)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"
    return twiml_play_and_redirect(audio_url, "/twiml")

@app.route("/hangup", methods=["POST"])
def hangup():
    goodbye = "Thank you for calling. Goodbye!"
    audio_filename = synthesize_speech(goodbye)
    audio_url = f"{request.url_root}static/audio/{audio_filename}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
  <Hangup/>
</Response>"""
    return Response(twiml, mimetype="text/xml")

def twiml_play_and_redirect(audio_url, next_path):
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{audio_url}</Play>
  <Redirect method="POST">{next_path}</Redirect>
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
    gpt_response = completion.choices[0].message["content"]
    print("🧠 GPT response:", gpt_response)
    return gpt_response

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
    print(f"✅ Audio saved as: {filename}")
    return filename

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
