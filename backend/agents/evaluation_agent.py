import json

from backend.services.llm_services import call_llm


def evaluate_answer(question, answer):

    prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY valid JSON.

{{
    "score": 0,
    "feedback": ""
}}
"""

    response = call_llm([
        {
            "role": "user",
            "content": prompt
        }
    ])

    content = response["choices"][0]["message"]["content"]

    try:
        return json.loads(content)

    except:
        return {
            "score": 5,
            "feedback": "Unable to evaluate answer."
        }