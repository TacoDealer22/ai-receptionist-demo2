
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key here
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form or request.get_json()
    user_input = data.get("SpeechResult") or data.get("Body") or ""

    # Predefined answers
    faq_answers = {
        "what is your company name": "Our company is called Omar's demo.",
        "where are you located": "We are located in Jordan.",
        "who created you": "I was created by Omar Aljallad and Asa'd Alalami.",
        "what are your working hours": "Our working hours are from 9 AM to 5 PM.",
        "what services do you offer": "We offer AI receptionist services.",
        "can i speak arabic": "Yes, I can understand and speak Arabic as well!",
        "can you send me a brochure": "Sure! Please provide your email or WhatsApp number.",
        "how do i get started": "Just let me know your company name and we'll set up a custom assistant for you."
    }

    # Normalize input for matching
    normalized = user_input.strip().lower()

    for q, a in faq_answers.items():
        if q in normalized:
            return jsonify({"response": a})

    # If no match, use OpenAI to generate answer
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI receptionist for Omar's demo, a company based in Jordan."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.6
        )
        answer = completion.choices[0].message["content"].strip()
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"response": "Sorry, I couldn’t process that. Please try again later."})

if __name__ == "__main__":
    # Bind to 0.0.0.0 for Render compatibility
    app.run(host="0.0.0.0", port=5000, debug=True)
