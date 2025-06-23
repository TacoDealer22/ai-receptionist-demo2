from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import openai
import requests
from elevenlabs import generate, save, set_api_key

app = Flask(__name__)
CORS(app)

# Set your API keys (DO NOT hardcode in production)
openai.api_key = os.getenv("OPENAI_API_KEY")
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Create a folder to store MP3s
os.makedirs("static", exist_ok=True)

@app.route('/webhook', methods=['POST'])
def webhook():
    user_input = request.form.get("SpeechResult", "")
    print(f"User said: {user_input}")

    # Step 1: Use OpenAI to generate response
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a friendly receptionist named Luna."},
            {"role": "user", "content": user_input}
        ]
    )
    assistant_text = response['choices'][0]['message']['content']
    print(f"Luna: {assistant_text}")

    # Step 2: Use ElevenLabs to generate audio
    audio = generate(text=assistant_text, voice="Rachel", model="eleven_monolingual_v1")

    # Step 3: Save MP3 to static folder
    filename = "luna_response.mp3"
    filepath = os.path.join("static", filename)
    save(audio, filepath)

    # Step 4: Return URL for Twilio
    audio_url = f"https://{request.host}/static/{filename}"
    return jsonify({"audio_url": audio_url})

# Serve static files (MP3)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
