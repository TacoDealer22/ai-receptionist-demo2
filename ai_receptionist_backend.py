import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

# Setup API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")

# ElevenLabs client
client = ElevenLabs(api_key=eleven_api_key)

# Flask setup
app = Flask(__name__)
CORS(app)

@app.route("/webhook", methods=["POST"])
def webhook():
    user_input = request.form.get("SpeechResult", "")

    # Build prompt
    prompt = f"""
    You are a friendly AI receptionist named Luna working for Omar's company in Jordan.
    You speak English and Arabic.
    Your job is to answer customer questions, guide them, and explain services.
    If someone asks who made you, say: Omar Majdi Mohammad Aljallad.
    Keep it short and helpful.
    User: {user_input}
    """

    # OpenAI response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": prompt }]
    )
    final_text = response.choices[0].message.content.strip()

    # ElevenLabs TTS
    audio = client.text_to_speech.convert(
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Default voice Alloy
        model_id="eleven_monolingual_v1",
        text=final_text,
        output_format="mp3_44100",
        optimize_streaming_latency="0"
    )

    # Save audio file
    output_path = "/tmp/response.mp3"
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Upload somewhere like S3 / use direct hosting service
    # For now, just return text only (Twilio Studio can’t stream directly from /tmp)
    return jsonify({
        "text": final_text,
        "audio_url": "NOT_IMPLEMENTED"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
