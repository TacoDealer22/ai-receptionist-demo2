import os
from flask import Flask, request, session, send_from_directory, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather, Play, Pause
from utils import get_gpt_response, text_to_speech_elevenlabs, fallback_response, static_qa_answer
from dotenv import load_dotenv
from threading import Lock
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# In-memory conversation store (for demo)
conversations = {}
conv_lock = Lock()

KA_DYY_PROMPT = {
    "role": "system",
    "content": (
        "You are Ka-dyy, an intelligent AI receptionist created by OMAR MAJDI MOHAMMAD ALJALLAD. "
        "You greet callers naturally, answer questions clearly, and sound warm, kind, and human. "
        "You can explain services, answer general knowledge questions, and always end calls politely."
    )
}

AUDIO_DIR = os.path.join("static", "audio")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

@app.route("/voice", methods=["POST"])
def voice():
    call_sid = request.values.get("CallSid")
    with conv_lock:
        conversations[call_sid] = [KA_DYY_PROMPT]
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action=url_for("gather", _external=True),
        speechTimeout="auto",
        language="en-US"
    )
    gather.say("Hello! This is Ka-dyy, Omar's AI receptionist. How can I help you today?", voice="Polly.Joanna")
    resp.append(gather)
    resp.redirect(url_for("voice", _external=True))
    return str(resp)

@app.route("/gather", methods=["POST"])
def gather():
    call_sid = request.values.get("CallSid")
    user_text = request.values.get("SpeechResult", "")
    with conv_lock:
        history = conversations.get(call_sid, [KA_DYY_PROMPT])
        history.append({"role": "user", "content": user_text})
    # Check for static Q&A
    ai_text = static_qa_answer(user_text)
    if not ai_text:
        # Get AI response
        ai_text = get_gpt_response(history)
    if not ai_text:
        ai_text = fallback_response()
    with conv_lock:
        history.append({"role": "assistant", "content": ai_text})
        conversations[call_sid] = history
    # Synthesize audio
    audio_filename = f"{call_sid}_{uuid.uuid4().hex}.mp3"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)
    tts_success = text_to_speech_elevenlabs(ai_text, audio_path)
    resp = VoiceResponse()
    if tts_success:
        audio_url = f"{BASE_URL}/static/audio/{audio_filename}"
        resp.play(audio_url)
    else:
        resp.say(ai_text, voice="Polly.Joanna")
    # Continue conversation
    gather = Gather(
        input="speech",
        action=url_for("gather", _external=True),
        speechTimeout="auto",
        language="en-US"
    )
    gather.say("Is there anything else I can help you with?", voice="Polly.Joanna")
    resp.append(gather)
    resp.redirect(url_for("voice", _external=True))
    return str(resp)

@app.route("/static/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 
