import os
import requests
import openai

# Debug: Print proxy-related environment variables
for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    if os.getenv(var):
        print(f"[DEBUG] Proxy env var set: {var}={os.getenv(var)}")

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt_response(messages, timeout=10):
    try:
        # Ensure no proxies argument is ever passed
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.6,
            timeout=timeout
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

def text_to_speech_elevenlabs(text, filename):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }
    try:
        r = requests.post(url, headers=headers, json=data, stream=True, timeout=15)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
            return True
        else:
            print(f"ElevenLabs error: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return False

def fallback_response():
    return "I'm sorry, I'm having trouble answering right now. Please try again later or call back soon!"

def static_qa_answer(user_text):
    # Lowercase for case-insensitive matching
    q = user_text.strip().lower()
    static_answers = {
        "what are your working hours?": "We're open from 9 AM to 6 PM, Sunday to Thursday.",
        "what are your business hours?": "We operate Sunday through Thursday, from 9 in the morning to 6 in the evening.",
        "where are you located?": "Our main office is located in Amman, Jordan.",
        "who created you?": "I was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
        "who made caddy?": "caddy was created by OMAR MAJDI MOHAMMAD ALJALLAD.",
        "what is your name?": "My name is caddy. I'm your AI receptionist.",
        "are you an ai?": "Yes, I'm an AI receptionist built to assist you quickly and clearly.",
        "what is the name of your company?": "Omar's demo.",
        "what does your company do?": "We provide AI Receptionist services through a subscription with our company.",
        "can i speak to someone?": "I'll forward your request. Please leave your name and message after the tone.",
        "can you call me back?": "I'll forward your request. Please leave your name and number after the tone."
    }
    # Try exact match
    if q in static_answers:
        return static_answers[q]
    # Try partial match (for more natural questions)
    for k, v in static_answers.items():
        if k.replace('?', '') in q:
            return v
    return None 
