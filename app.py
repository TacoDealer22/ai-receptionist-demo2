import os
import uuid
from flask import Flask, request, Response, jsonify
import requests
from dotenv import load_dotenv
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from flask_cors import CORS
import openai
print("✅ OpenAI SDK Version:", openai.__version__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY = os.getenv("TWILIO_API_KEY")
TWILIO_API_SECRET = os.getenv("TWILIO_API_SECRET")
TWILIO_TWIML_APP_SID = os.getenv("TWILIO_TWIML_APP_SID")

# ✅ Init OpenAI
openai.api_key = OPENAI_API_KEY

# Static Q&A
STATIC_RESPONSES = {
    "what are your working hours?": "We’re open from 9 AM to 6 PM, Sunday to Thursday.",
    "what are your business hours?": "We operate Sunday through Thursday, from 9 in the morning to 6 in the evening.",
    "where are you located?": "Our main office is located in Amman, Jordan.",
    "who created you?": "I was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "who made luna?": "Luna was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "what is your name?": "My name is Luna. I’m your AI receptionist.",
    "are you an ai?": "Yes, I’m an AI receptionist built to assist you quickly and clearly.",
    "what is the name of your company?": "Omar's demo.",
    "what does your company do?": "We provide AI Receptionist services through a subscription with our company.",
    "can i speak to someone?": "I’ll forward your request. Please leave your name and message after the tone.",
    "can you call me back?": "I’ll forward your request. Please leave your name and number after the tone."
}

@app.route("/voice", methods=["POST"])
def handle_voice():
    greeting = "Hi, this is Luna, your AI receptionist. How can I help you today?"
    audio_file = synthesize_speech(greeting)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{request.url_root}static/audio/{audio_file}</Play>
    <Gather input="speech" action="/twiml" method="POST" timeout="300" speechTimeout="auto"/>
</Response>"""

@app.route("/twiml", methods=["POST"])
def generate_twiml():
    user_input = request.form.get("SpeechResult", "").strip()
    print(f"\n🎤 Twilio SpeechResult: {user_input}")

    if not user_input:
        fallback = "I didn’t catch that. You can ask again or say goodbye to end the call."
        audio_file = synthesize_speech(fallback)
        return twiml_response(audio_file)

    user_question = user_input.lower()
    if any(bye in user_question for bye in ["bye", "goodbye", "see you", "ma3 alsalama"]):
        goodbye = "Thank you for calling. Goodbye!"
        audio_file = synthesize_speech(goodbye)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{request.url_root}static/audio/{audio_file}</Play>
    <Hangup/>
</Response>"""

    if user_question in STATIC_RESPONSES:
        answer = STATIC_RESPONSES[user_question]
    else:
        answer = ask_gpt(user_input)

    audio_file = synthesize_speech(answer)
    return twiml_response(audio_file)

@app.route("/token", methods=["GET"])
def generate_token():
    identity = "browser_user"
    token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY,
        TWILIO_API_SECRET,
        identity=identity
    )
    voice_grant = VoiceGrant(
        outgoing_application_sid=TWILIO_TWIML_APP_SID,
        incoming_allow=True
    )
    token.add_grant(voice_grant)
    return jsonify({"token": token.to_jwt()})

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Luna, a helpful, natural, friendly AI receptionist. Answer clearly and kindly. If the user asks about services or general knowledge, answer like a real assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return "I'm sorry, I couldn't answer that at the moment. Please try again later."

AUDIO_CACHE = {}
def synthesize_speech(text):
    if text in AUDIO_CACHE:
        return AUDIO_CACHE[text]

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
        print("❌ ElevenLabs API error:", response.text)
        raise Exception("ElevenLabs failed")

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(AUDIO_DIR, filename)
    with open(path, "wb") as f:
        f.write(response.content)

    AUDIO_CACHE[text] = filename
    return filename

def twiml_response(filename):
    url = f"{request.url_root}static/audio/{filename}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{url}</Play>
    <Gather input="speech" action="/twiml" method="POST" timeout="300" speechTimeout="auto"/>
</Response>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
