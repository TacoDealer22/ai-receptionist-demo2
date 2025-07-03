import os
os.environ["OPENAI_PYTHON_HTTP_CLIENT"] = "requests"
for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ[var] = ""
print("==== ENVIRONMENT VARIABLES ====")
for k, v in os.environ.items():
    if "proxy" in k.lower() or "openai" in k.lower():
        print(f"{k}={v}")
print("===============================" )
import uuid
from flask import Flask, request, Response, jsonify, send_file
import requests
from dotenv import load_dotenv
from flask_cors import CORS
import openai
from utils import get_gpt_response, text_to_speech_elevenlabs, fallback_response, static_qa_answer
from twilio.rest import Client
import io
import tempfile
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Greeting
GREETING = "Hello! This is caddy, Omar's AI receptionist. How can I help you today?"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

required_vars = [
    "OPENAI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    # Add Twilio vars if you use them
]
for var in required_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Missing required environment variable: {var}")

print("[DEBUG] OpenAI loaded from:", openai.__file__)
print("[DEBUG] OpenAI version:", openai.__version__)

print("TwiML App SID:", os.getenv("TWILIO_TWIML_APP_SID"))

@app.route("/voice", methods=["POST"])
def voice():
    greeting_audio = synthesize_and_cache(GREETING)
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Response>\n    <Play>{request.url_root}static/audio/{greeting_audio}</Play>\n    <Gather input=\"speech\" action=\"/twiml\" method=\"POST\" timeout=\"300\" speechTimeout=\"auto\"/>\n</Response>"""
    return Response(twiml, mimetype="text/xml")

@app.route("/twiml", methods=["POST"])
def twiml():
    user_input = request.form.get("SpeechResult", "").strip()
    print(f"\n🎤 Twilio SpeechResult: {user_input}")

    if not user_input:
        fallback = "I didn't catch that. You can ask again or say goodbye to end the call."
        return twiml_response(synthesize_and_cache(fallback))

    if any(bye in user_input.lower() for bye in ["bye", "goodbye", "see you", "ma3 alsalama"]):
        bye_audio = synthesize_and_cache("Thank you for calling. Goodbye!")
        twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Response>\n    <Play>{request.url_root}static/audio/{bye_audio}</Play>\n    <Hangup/>\n</Response>"""
        return Response(twiml, mimetype="text/xml")

    # Static Q&A
    answer = static_qa_answer(user_input)
    if not answer:
        # AI response
        answer = get_gpt_response([
            {"role": "system", "content": "You are caddy, an intelligent AI receptionist created by OMAR MAJDI MOHAMMAD ALJALLAD. You greet callers naturally, answer questions clearly, and sound warm, kind, and human. You can explain services, answer general knowledge questions, and always end calls politely."},
            {"role": "user", "content": user_input}
        ])
    if not answer:
        answer = fallback_response()
    return twiml_response(synthesize_and_cache(answer))

@app.route("/call", methods=["POST"])
def call():
    data = request.get_json()
    to_number = data.get("to")
    message = data.get("message", GREETING)
    if not to_number:
        return jsonify({"error": "Missing 'to' phone number."}), 400
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER):
        return jsonify({"error": "Twilio environment variables not set."}), 500
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{request.url_root}voice"  # This should point to your /voice endpoint
        )
        return jsonify({"status": "initiated", "call_sid": call.sid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/web-greet", methods=["GET"])
def web_greet():
    """Returns a greeting audio file for the web widget."""
    greeting_audio = synthesize_and_cache(GREETING)
    audio_path = os.path.join(AUDIO_DIR, greeting_audio)
    return send_file(audio_path, mimetype="audio/mpeg")

@app.route("/web-voice", methods=["POST"])
def web_voice():
    """Receives user audio (webm or wav), transcribes, gets GPT response, TTS, returns audio."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded."}), 400
    audio_file = request.files["audio"]
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
        audio_file.save(temp_audio)
        temp_audio_path = temp_audio.name
    # Transcribe with OpenAI Whisper
    with open(temp_audio_path, "rb") as af:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=af
        )
    user_text = transcript.text.strip()
    print(f"[WEB] User said: {user_text}")
    # Get AI response
    answer = static_qa_answer(user_text)
    if not answer:
        answer = get_gpt_response([
            {"role": "system", "content": "You are caddy, an intelligent AI receptionist created by OMAR MAJDI MOHAMMAD ALJALLAD. You greet callers naturally, answer questions clearly, and sound warm, kind, and human. You can explain services, answer general knowledge questions, and always end calls politely."},
            {"role": "user", "content": user_text}
        ])
    if not answer:
        answer = fallback_response()
    # Synthesize with ElevenLabs
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_out:
        text_to_speech_elevenlabs(answer, temp_out.name)
        temp_out.seek(0)
        audio_bytes = temp_out.read()
    # Return audio as response
    return Response(audio_bytes, mimetype="audio/mpeg")

@app.route("/token", methods=["GET"])
def token():
    try:
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_api_key = os.getenv("TWILIO_API_KEY")
        twilio_api_secret = os.getenv("TWILIO_API_SECRET")
        twilio_app_sid = os.getenv("TWILIO_TWIML_APP_SID")
        identity = "user"

        print("TWILIO_ACCOUNT_SID:", twilio_account_sid)
        print("TWILIO_API_KEY:", twilio_api_key)
        print("TWILIO_API_SECRET:", twilio_api_secret)
        print("TWILIO_TWIML_APP_SID:", twilio_app_sid)

        if not all([twilio_account_sid, twilio_api_key, twilio_api_secret, twilio_app_sid]):
            return jsonify({"error": "Missing Twilio environment variables"}), 500

        token = AccessToken(
            twilio_account_sid,
            twilio_api_key,
            twilio_api_secret,
            identity=identity
        )
        voice_grant = VoiceGrant(
            outgoing_application_sid=twilio_app_sid,
            incoming_allow=True
        )
        token.add_grant(voice_grant)
        return jsonify(token=token.to_jwt())
    except Exception as e:
        print("Error in /token:", str(e))
        return jsonify({"error": str(e)}), 500

def synthesize_and_cache(text):
    # Use a simple cache to avoid regenerating the same audio
    filename = f"{uuid.uuid5(uuid.NAMESPACE_DNS, text)}.mp3"
    path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(path):
        text_to_speech_elevenlabs(text, path)
    return filename

def twiml_response(filename):
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Response>\n    <Play>{request.url_root}static/audio/{filename}</Play>\n    <Gather input=\"speech\" action=\"/twiml\" method=\"POST\" timeout=\"300\" speechTimeout=\"auto\"/>\n</Response>"""
    return Response(twiml, mimetype="text/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 
