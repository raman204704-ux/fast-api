import json
import os

INTERVIEW_FOLDER = "interviews"
os.makedirs(INTERVIEW_FOLDER, exist_ok=True)


def create_interview_file(session_id, profile, first_question):

    file_path = os.path.join(
        INTERVIEW_FOLDER,
        f"{session_id}.json"
    )

    data = {
        "session_id": session_id,
        "status": "active",
        "resume_profile": profile,
        "interview_history": [
            {
                "question_number": 1,
                "question": first_question,
                "answer": None
            }
        ]
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return file_path


def load_interview(session_id):

    file_path = os.path.join(
        INTERVIEW_FOLDER,
        f"{session_id}.json"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_interview(session_id, data):

    file_path = os.path.join(
        INTERVIEW_FOLDER,
        f"{session_id}.json"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)