
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
CORS(app)

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
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful AI receptionist."},
            {"role": "user", "content": user_question},
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        question = data.get("question", "")
        if not question:
            return jsonify({"error": "No question provided"}), 400
        answer = generate_answer(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/twiml", methods=["POST"])
def twiml():
    try:
        speech = request.form.get("SpeechResult") or request.args.get("SpeechResult")
        if not speech:
            return Response("<Response><Say>No speech input detected</Say></Response>", mimetype="text/xml")

        answer = generate_answer(speech)

        # Convert text to mp3 (this assumes you already handle ElevenLabs part externally)
        # For now we'll simulate a static audio file URL returned per request
        audio_url = "https://your-real-elevenlabs-audio-file-url.com/output.mp3"

        twiml_response = f"""
        <?xml version='1.0' encoding='UTF-8'?>
        <Response>
            <Play>{audio_url}</Play>
        </Response>
        """
        return Response(twiml_response, mimetype="text/xml")

    except Exception as e:
        return Response(f"<Response><Say>Error: {str(e)}</Say></Response>", mimetype="text/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
