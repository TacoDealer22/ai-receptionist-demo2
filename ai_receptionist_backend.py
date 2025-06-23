from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import openai
from elevenlabs import ElevenLabs, Voice, VoiceSettings

app = Flask(__name__)
CORS(app)

# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

@app.route('/webhook', methods=['POST'])
def webhook():
    user_input = request.form.get("SpeechResult", "")
    if not user_input:
        return jsonify({"error": "Missing SpeechResult"}), 400

    try:
        # Step 1: Get AI response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly AI receptionist named Luna. Speak clearly and help the caller."},
                {"role": "user", "content": user_input}
            ]
        )
        assistant_text = response['choices'][0]['message']['content']

        # Step 2: Generate audio from ElevenLabs
        audio = client.generate(
            text=assistant_text,
            voice=Voice(voice_id="EXAVITQu4vr4xnSDxMaL"),  # Rachel voice
            model="eleven_monolingual_v1",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.5)
        )

        # Step 3: Save MP3
        os.makedirs("static", exist_ok=True)
        output_path = os.path.join("static", "luna_response.mp3")
        with open(output_path, "wb") as f:
            f.write(audio)

        # Step 4: Return audio file path
        return jsonify({"audio_url": f"https://{request.host}/static/luna_response.mp3"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def serve_audio(filename):
    return send_from_directory("static", filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
