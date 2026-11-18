from backend.services.llm_services import call_llm


def generate_first_question(profile):

    prompt = f"""
You are an expert technical interviewer.

Candidate Profile:

{profile}

Generate ONE interview question.

Rules:
1. Ask only one question.
2. Focus on the candidate's strongest project or skill.
3. Return only the question text.
4. Do not add numbering.
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = call_llm(messages)

    question = response["choices"][0]["message"]["content"].strip()

    return question