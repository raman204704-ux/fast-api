from dotenv import load_dotenv
import os
import requests
load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_llm(messages, model="llama-3.3-70b-versatile", temperature=0.0):
    """
    Centralized function to call Groq LLM API.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Groq API Error: {response.status_code} - {response.text}"
        )
    result = response.json()

    return result
