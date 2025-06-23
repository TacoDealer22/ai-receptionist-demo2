from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from elevenlabs import generate, save, set_api_key
import os
import shutil

app = Flask(__name__)
CORS(app)

# Load environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# Initialize clients
client = OpenAI(api_key=openai_api_key)
set_api_key(elevenlabs_api_key)

@app.route("/webhook", methods=["POST"])
def webhook():
    user_text = request.json.get("SpeechResult", "")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_text}]
    )

    reply = response.choices[0].message.content

    audio = generate(
        text=reply,
        voice="Rachel",
        model="eleven_monolingual_v1"
    )

    # Save to static folder
    os.makedirs("static", exist_ok=True)
    save(audio, "/tmp/response.mp3")
    shutil.copy("/tmp/response.mp3", "static/response.mp3")

    return {"reply": reply}

@app.route("/voice", methods=["GET"])
def voice():
    # Generate greeting audio
    greeting = generate(
        text="Hello and welcome to our AI receptionist! How can I assist you today?",
        voice="Rachel",
        model="eleven_monolingual_v1"
    )

    # Save to static folder
    os.makedirs("static", exist_ok=True)
    save(greeting, "/tmp/ai_greeting.mp3")
    shutil.copy("/tmp/ai_greeting.mp3", "static/ai_greeting.mp3")

    # Return TwiML for Twilio to play it
    xml = f"""
    <Response>
        <Play>https://ai-receptionist-demo2.onrender.com/static/ai_greeting.mp3</Play>
    </Response>
    """
    return Response(xml, mimetype="text/xml")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
