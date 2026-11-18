import json


from backend.services.llm_services import call_llm


def generate_interview_plan(resume_text: str):

    prompt = f"""
    You are an experience technical interviewer. 
    Based on the candidate's resume, generate exatly 10 interview questions.
    Rules:
    -2 HR questions
    -4 Techincal questions
    -2 project base questions
    -1 problem-based questions
    -1 Behavioral questions

    question should become progressively harder.

    Return ONLY valid JSON (no markdown, no code fences).
    JSON format:
    {{
    "HR":["Q1","Q2"],
    "Tech":["Q3","Q4","Q5","Q6"],
    "Project":["Q7","Q8"],
    "Problem":["Q9"],
    "Behavioral":["Q10"],
    }}
    Resume:
    {resume_text}
    """

    messages=[
        {"role": "system", "content": "You are a planner agent that designs interview questions."},
        {"role": "user", "content": prompt}
    ]

    result=call_llm(messages)
    if "choices" not in result:
        return{
            "error": "Groq API did not return choices",
             "details": result
        }

    raw_output = result["choices"][0]["message"]["content"]

    clean_output = raw_output.strip()
    if clean_output.startswith("```"):
        clean_output = clean_output.replace("`")
        clean_output = clean_output.replace("json\n", "").replace("json", "", 1).strip()

    try:
        return json.loads(clean_output)
    except json.decoder.JSONDecodeError:
        return {"error": "Invalid Json returned", "details": result}
