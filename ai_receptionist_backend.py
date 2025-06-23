from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save  # for local testing (not needed in production)

load_dotenv()

# Set API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Preset Q&A
PRESETS = {
    "name of the company": "Omar's Ai demo",
    "who created you": "Omar Aljallad and As'ad Alalami",
    "what are your hours": "We're open from 9 am to 5 pm",
    "where are you located": "Jordan, Amman",
    "what does your company do": "Offers AI receptionist services",
}

def generate_answer(user_question):
    normalized = user_question.strip().lower()
    if normalized in PRESETS:
        return PRESETS[normalized]
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_question},
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return resp.choices[0].message.content.strip()

def text_to_speech(answer_text):
    # Replace with a voice_id from your ElevenLabs account
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    audio = eleven.text_to_speech.convert(
        text=answer_text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )
    return audio  # raw bytes of MP3

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    q = data.get("question", "")
    if not q:
        return jsonify({"error": "No question provided"}), 400
    answer = generate_answer(q)
    audio = text_to_speech(answer)
    # Optionally save during dev/testing:
    # save(audio, "out.mp3")
    return jsonify({"answer": answer, "audio_b64": audio.decode("latin1")})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
