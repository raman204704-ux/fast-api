import os
from dotenv import load_dotenv
from groq import Groq
import json

# Load .env file
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print("GROQ_API_KEY configured:", bool(api_key))

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")
client = Groq(api_key=api_key)

def resume_parser_agent(resume_text):
    """
    Parse resume text and extract structured candidate information.
    """

    prompt = f"""
You are an expert Resume Parser.

Analyze the resume and extract the following information.

Return ONLY valid JSON.

JSON Format:

{{
    "candidate_name": "",
    "skills": [],
    "projects": [],
    "experience": [],
    "education": [],
    "certifications": []
}}

Resume:

{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parsing expert. Return ONLY valid JSON. Do not include explanations, markdown, or code fences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        result = response.choices[0].message.content.strip()

        # Remove markdown code fences if present
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        print("\n===== RAW LLM RESPONSE =====")
        print(result)
        print("============================\n")

        return json.loads(result)

    except json.JSONDecodeError as e:
        print("\n===== JSON PARSE ERROR =====")
        print("Error:", str(e))
        print("Response received:")
        print(result if 'result' in locals() else "No response")
        print("============================\n")

        return {
            "error": "Invalid JSON returned by model",
            "details": str(e),
            "raw_response": result if 'result' in locals() else ""
        }

    except Exception as e:
        print("\n===== GENERAL ERROR =====")
        print(str(e))
        print("=========================\n")

        return {
            "error": str(e),
            "candidate_name": "",
            "skills": [],
            "projects": [],
            "experience": [],
            "education": [],
            "certifications": []
        }