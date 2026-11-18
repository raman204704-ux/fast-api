import json

from backend.services.llm_services import call_llm


def generate_interview_report(interview_history):

    prompt = f"""
You are a senior technical interviewer.

Analyze the complete interview history and generate a final hiring assessment.

Interview History:

{json.dumps(interview_history, indent=2)}

Return ONLY valid JSON in the following format:

{{
    "overall_score": 0,
    "strengths": [],
    "weaknesses": [],
    "communication_skills": "",
    "technical_skills": "",
    "recommendation": ""
}}

Rules:
- overall_score must be between 0 and 100
- strengths should be a list
- weaknesses should be a list
- recommendation should be one of:
  - Strong Hire
  - Hire
  - Consider
  - Reject
"""

    response = call_llm(
        [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["choices"][0]["message"]["content"]

    try:
        return json.loads(content)

    except Exception:

        return {
            "overall_score": 0,
            "strengths": [],
            "weaknesses": [],
            "communication_skills": "Unable to evaluate",
            "technical_skills": "Unable to evaluate",
            "recommendation": "Consider"
        }