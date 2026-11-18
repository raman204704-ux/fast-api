prompt = f"""
Analyze this interview answer.

Question:
{question}

Answer:
{answer}

Return JSON:

{{
    "score": 1-10,
    "topics_mentioned": [],
    "strengths": [],
    "weaknesses": [],
    "follow_up_needed": true/false,
    "follow_up_topic": ""
}}
"""