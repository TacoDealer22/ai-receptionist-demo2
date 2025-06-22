from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key (read from environment variable for safety)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form
    user_input = data.get('SpeechResult') or data.get('Body') or 'No input provided.'

    # Define system message for company context
    system_message = (
        "You are an AI receptionist for a company named Omar's Demo. "
        "The company is located in Jordan and operates from 9 AM to 5 PM. "
        "You were created by Omar Aljallad and Asa'd Alalami. "
        "You offer AI receptionist services. "
        "Answer any incoming questions naturally and helpfully. If you are asked: "
        "- 'What are your working hours?' or anything similar, answer 'Our working hours are from 9 AM to 5 PM.' "
        "- 'Where are you located?' answer 'We are located in Jordan.' "
        "- 'Who created you?' answer 'I was created by Omar Aljallad and Asa'd Alalami.' "
        "- 'What do you offer?' answer 'We offer AI receptionist services.' "
        "- 'What is your company name?' answer 'Our company is called Omar's Demo.' "
        "If the question doesn't match any of those, try your best to respond using your general knowledge."
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )

        ai_response = completion.choices[0].message['content'].strip()

        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"response": "Sorry, there was an error: {}".format(str(e))})

if __name__ == '__main__':
    app.run(debug=True)
