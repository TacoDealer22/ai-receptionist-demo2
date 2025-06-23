from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
from elevenlabs import generate, stream, set_api_key

# === Basic Setup ===
app = Flask(__name__)
CORS(app)

# === Load API keys from environment ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
set_api_key(ELEVEN_API_KEY)

# === Static Responses for Known Questions ===
static_responses = {
    "who created you": "I was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
    "what are your working hours": "I’m available 24/7 to answer your questions.",
    "where are you located": "I’m hosted online and always available.",
    "who is your owner": "My creator is OMAR ALJALLAD.",
    "who made you": "OMAR ALJALLAD is my developer.",
    "what's your name": "My name is Luna, your AI receptionist."
}

@app.route("/")
def home():
    return "AI Receptionist Luna is running!"

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").lower()

    # Check for static responses
    for key, answer in static_responses.items():
        if key in question:
            return jsonify({"answer": answer})

    # Otherwise, use GPT to generate answer
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI receptionist named Luna created by OMAR MAJDI MOHAMMAD ALJALLAD. Answer politely and helpfully."},
                {"role": "user", "content": question}
            ]
        )
        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": "Sorry, something went wrong."}), 500

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "Hello, how can I help you?")
    try:
        audio_stream = generate(text=text, voice="Rachel", stream=True)
        return stream(audio_stream)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
