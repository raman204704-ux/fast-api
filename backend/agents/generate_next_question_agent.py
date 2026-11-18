from backend.services.llm_services import call_llm

def generate_next_question(profile, previous_question, answer):

    prompt = f"""
You are an expert interviewer.

Candidate Profile:
{profile}

Previous Question:
{previous_question}

Candidate Answer:
{answer}

Generate ONE follow-up interview question.

Return only the question text.
"""

    response = call_llm([
        {
            "role": "user",
            "content": prompt
        }
    ])

    return response["choices"][0]["message"]["content"].strip()