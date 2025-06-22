from flask import Flask, request, Response
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")  # API key is set in hosting dashboard

@app.route("/webhook", methods=["POST"])
def webhook():
    speech_text = request.values.get("SpeechResult", "")

    if not speech_text:
        return Response("<Response><Say>Sorry, I didn't catch that. Can you please repeat?</Say></Response>", mimetype='text/xml')

    prompt = f"""
    You are a friendly and professional virtual receptionist that speaks Arabic and English fluently.
    You help people with:
    1. Booking or rescheduling appointments
    2. Answering service questions
    3. Providing office hours and location
    4. Taking messages when needed

    Always respond clearly and politely. If you're not sure, ask the user to clarify. Here’s the question:

    {speech_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful AI receptionist that speaks Arabic and English."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response["choices"][0]["message"]["content"]

        return Response(f"<Response><Say>{reply}</Say></Response>", mimetype='text/xml')

    except Exception as e:
        print("Error from OpenAI:", e)
        return Response("<Response><Say>Sorry, something went wrong on our side.</Say></Response>", mimetype='text/xml')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
