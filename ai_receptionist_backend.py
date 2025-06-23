import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv
from elevenlabs import generate, stream, set_api_key

# Load environment variables
load_dotenv()

# Setup keys
openai.api_key = os.getenv("OPENAI_API_KEY")
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Flask setup
app = Flask(__name__)
CORS(app)

# Basic info
COMPANY_NAME = "Omar's demo"
LOCATION = "Jordan"

@app.route("/webhook", methods=["POST"])
def webhook():
    user_input = request.form.get("SpeechResult", "")

    # Build the GPT prompt
    prompt = f"""
    You are an AI receptionist for {COMPANY_NAME}, based in {LOCATION}.
    If asked who created you, say "Omar Majdi Mohammad Aljallad and Asa'd Alalami."
    You work 9am to 5pm. You help clients by answering their questions about business services.
    You also mention that you support Arabic. Reply naturally:
    User: {user_input}
    """

    # Get GPT-3.5 reply
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": prompt }]
    )
    final_text = response.choices[0].message.content.strip()

    # Generate ElevenLabs audio
    audio = generate(
        text=final_text,
        voice="alloy",
        model="eleven_monolingual_v1",
        stream=False
    )

    return jsonify({
        "text": final_text,
        "audio_url": audio["audio_url"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
