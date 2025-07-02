import os
import uuid
from flask import Flask, request, Response
import requests
from dotenv import load_dotenv
from flask_cors import CORS
import openai
from utils import get_gpt_response, text_to_speech_elevenlabs, fallback_response, static_qa_answer

load_dotenv()

app = Flask(__name__)
CORS(app)

AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Greeting
GREETING = "Hello! This is ka-dyy, Omar's AI receptionist. How can I help you today?"

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
            {"role": "system", "content": "You are ka-dyy, an intelligent AI receptionist created by OMAR MAJDI MOHAMMAD ALJALLAD. You greet callers naturally, answer questions clearly, and sound warm, kind, and human. You can explain services, answer general knowledge questions, and always end calls politely."},
            {"role": "user", "content": user_input}
        ])
    if not answer:
        answer = fallback_response()
    return twiml_response(synthesize_and_cache(answer))

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
