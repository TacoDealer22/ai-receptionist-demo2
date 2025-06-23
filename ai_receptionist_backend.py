from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from elevenlabs import generate, save, set_api_key
import openai
import os

# Load env vars
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
set_api_key(os.getenv("ELEVEN_API_KEY"))

app = Flask(__name__)
CORS(app)

# Q&A preset
PRESET_QA = {
    "name of the company": "Omar's AI demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 AM to 5 PM.",
    "where are you located": "Jordan, Amman.",
    "what does your company do": "We offer AI receptionist services."
}

def check_for_preset(user_input):
    lower_input = user_input.lower()
    for question, answer in PRESET_QA.items():
        if question in lower_input:
            return answer
    return None

@app.route("/voice", methods=["POST"])
def voice():
    return jsonify({
        "actions": [
            {
                "say": {
                    "text": "Hi! I'm Omar's AI receptionist. How can I help you today?"
                }
            },
            {
                "listen": True
            }
        ]
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    user_input = data.get("SpeechResult", "")

    response_text = check_for_preset(user_input)

    if not response_text:
        gpt_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI receptionist."},
                {"role": "user", "content": user_input}
            ]
        )
        response_text = gpt_response.choices[0].message.content

    audio = generate(text=response_text, voice="Bella", model="eleven_multilingual_v2")
    save(audio, "static/response.mp3")

    return jsonify({"audio_url": request.host_url + "static/response.mp3"})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
