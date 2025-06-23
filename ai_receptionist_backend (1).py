
import os
from flask import Flask, request, jsonify, send_from_directory
import openai
from elevenlabs import generate, save, set_api_key

app = Flask(__name__)

# Set API Keys
openai.api_key = os.getenv("OPENAI_API_KEY")
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Ensure static folder exists for audio
if not os.path.exists("static"):
    os.makedirs("static")

@app.route("/webhook", methods=["POST"])
def webhook():
    user_input = request.form.get("SpeechResult", "")

    if not user_input:
        return jsonify({"response": "Sorry, I didn't hear anything."})

    try:
        # Generate GPT response
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful and polite AI receptionist."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion.choices[0].message["content"]

        # Convert text to speech
        audio = generate(
            text=reply,
            voice="Rachel",
            model="eleven_monolingual_v1"
        )

        # Save audio file
        audio_path = "static/response.mp3"
        save(audio, audio_path)

        # Return audio URL to Twilio
        return jsonify({"response": reply, "audio_url": f"{request.url_root}static/response.mp3"})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

@app.route("/static/<path:filename>")
def serve_audio(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True)
