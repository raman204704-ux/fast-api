from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.services.resume_parser import extract_resume_text
from backend.agents.parser_agent import resume_parser_agent
from backend.agents.generate_question_agent import generate_first_question
from backend.agents.generate_next_question_agent import generate_next_question
from database.session import interview_sessions, ResumeProfile,AnswerRequest
from backend.services.interview_storage import create_interview_file
from backend.services.interview_storage import (load_interview,save_interview)
from backend.agents.evaluation_agent import evaluate_answer

from backend.agents.report_agent import generate_interview_report
from backend.services.STT import transcribe_audio_file
from backend.services.tts_service import speak
import tempfile
# import soundfile as sf

import os
import uuid
import speech_recognition as sr
from pydantic import BaseModel

class AnswerRequest(BaseModel):
    answer: str

app = FastAPI()
ANSWER_FOLDER = "interview_answers"
os.makedirs(ANSWER_FOLDER, exist_ok=True)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================
# Upload Resume
# ==========================
@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "status": "success",
        "message": "Resume uploaded successfully",
        "file_name": file.filename,
        "file_path": file_path
    }


# ==========================
# Parse Resume
# ==========================
@app.post("/api/parse-resume")
async def parse_resume_endpoint(file_path: str):

    file_path = os.path.join(UPLOAD_FOLDER, file_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Resume not found: {file_path}"
        )

    resume_text = extract_resume_text(file_path)

    parsed_profile = resume_parser_agent(resume_text)

    return {
        "status": "success",
        "resume_profile": parsed_profile
    }


# ==========================
# Create Interview Session
# ==========================
@app.post("/api/create-session")
async def create_session(file_path: str):

    file_path = os.path.join(UPLOAD_FOLDER, file_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Resume not found: {file_path}"
        )

    resume_text = extract_resume_text(file_path)

    parsed_profile = resume_parser_agent(resume_text)

    session_id = str(uuid.uuid4())

    interview_sessions[session_id] = {
        "resume_profile": parsed_profile,
        "questions": [],
        "answers": [],
        "question_count": 0,
        "status": "created"
    }

    print("\n============================")
    print("Created Session ID:", session_id)
    print("Current Sessions:", list(interview_sessions.keys()))
    print("============================\n")

    return {
        "status": "success",
        "session_id": session_id,
        # "resume_profile": parsed_profile
    }


# ==========================
# Start Interview
# ==========================
@app.post("/api/start-interview/{session_id}")
async def start_interview(session_id: str):

    print("\n============================")
    print("Received Session ID:", repr(session_id))
    print("Available Sessions:", list(interview_sessions.keys()))
    print("============================\n")

    if session_id not in interview_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session = interview_sessions[session_id]

    first_question = generate_first_question(
        session["resume_profile"]
    )

    await speak(first_question)

    create_interview_file(
        session_id,
        session["resume_profile"],
        first_question
    )

    session["questions"].append(first_question)
    session["question_count"] = 1
    session["status"] = "active"

    return {
        "status": "success",
        "session_id": session_id,
        "question_number": 1,
        "question": first_question
    }
@app.post("/api/submit-answer/{session_id}")
async def submit_answer(
    session_id: str,
    request: AnswerRequest
):

    # Check session exists
    if session_id not in interview_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session = interview_sessions[session_id]

    # Candidate answer
    answer = request.answer

    # Load interview JSON file
    interview_data = load_interview(session_id)

    # Get current question
    current_question = interview_data["interview_history"][-1]["question"]


    # Evaluate answer
    evaluation = evaluate_answer(
        current_question,
        answer
    )

    # Store answer and evaluation
    interview_data["interview_history"][-1]["answer"] = answer

    interview_data["interview_history"][-1]["evaluation"] = {
        "score": evaluation["score"],
        "feedback": evaluation["feedback"]
    }

    question_count = session["question_count"]

    # Check if interview is complete
    if question_count >= 10:

        session["status"] = "completed"
        interview_data["status"] = "completed"

        save_interview(session_id, interview_data)

        return {
            "status": "completed",
            "message": "Interview Finished",
            "final_score": evaluation["score"],
            "final_feedback": evaluation["feedback"]
        }

    # Generate next question
    next_question = generate_next_question(
        session["resume_profile"],
        current_question,
        answer
    )

    await speak(next_question)



    # Update in-memory session
    session["answers"].append(answer)
    session["questions"].append(next_question)
    session["question_count"] += 1

    # Store next question in JSON
    interview_data["interview_history"].append(
        {
            "question_number": session["question_count"],
            "question": next_question,
            "answer": None,
            "evaluation": None
        }
    )

    # Save updated interview file
    save_interview(session_id, interview_data)

    return {
        "status": "success",
        "session_id": session_id,
        "question_number": session["question_count"],
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "next_question": next_question
    }

@app.get("/api/interview-report/{session_id}")
async def get_interview_report(session_id: str):

    interview_data = load_interview(session_id)

    if not interview_data:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

    # Generate report if it doesn't already exist
    if "final_report" not in interview_data:

        report = generate_interview_report(
            interview_data["interview_history"]
        )

        interview_data["final_report"] = report

        save_interview(
            session_id,
            interview_data
        )

    return {
        "status": "success",
        "session_id": session_id,
        "candidate_name": interview_data["resume_profile"].get(
            "candidate_name",
            "Unknown"
        ),
        "report": interview_data["final_report"]
    }


@app.post("/api/speech-to-text")
async def speech_to_text(
    file: UploadFile = File(...)
):

    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    text = transcribe_audio_file(temp_path)

    os.remove(temp_path)

    return {
        "status": "success",
        "transcription": text
    }


import io
from pydub import AudioSegment


@app.post("/api/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # 1. Read the incoming audio bytes
        audio_bytes = await file.read()

        # 2. Load into pydub (auto-detects webm/opus format)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))

        # 3. Convert to mono, 16kHz (optimal for speech recognition)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

        # 4. Export as WAV to a temporary file
        temp_wav_path = f"temp_{uuid.uuid4()}.wav"
        audio_segment.export(temp_wav_path, format="wav")

        # 5. Pass the WAV file to your speech recognition function
        text = transcribe_audio_file(temp_wav_path)

        # 6. Clean up the temporary file
        os.remove(temp_wav_path)

        if not text or text.strip() == "":
            return {
                "success": False,
                "error": "No speech detected in audio"
            }

        return {
            "success": True,
            "transcription": text
        }

    except Exception as e:
        print(f"Transcription Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/submit-audio-answer/{session_id}")
async def submit_audio_answer(
    session_id: str,
    file: UploadFile = File(...)
):
    try:

        # ----------------------------
        # Check Session
        # ----------------------------
        if session_id not in interview_sessions:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        session = interview_sessions[session_id]

        print("File received:", file.filename)
        print("Content type:", file.content_type)

        # ----------------------------
        # Create Audio Folder
        # ----------------------------
        ANSWER_FOLDER = "interview_answers"
        os.makedirs(ANSWER_FOLDER, exist_ok=True)

        question_no = session["question_count"]

        audio_filename = (
            f"{session_id}_q{question_no}.wav"
        )

        audio_path = os.path.join(
            ANSWER_FOLDER,
            audio_filename
        )

        # ----------------------------
        # Save Audio
        # ----------------------------
        with open(audio_path, "wb") as buffer:
            buffer.write(await file.read())

        print("Saved audio:", audio_path)

        # ----------------------------
        # Speech To Text
        # ----------------------------
        answer = transcribe_audio_file(audio_path)

        print("Transcript:", repr(answer))

        if not answer or answer.strip() == "":
            return {
                "status": "error",
                "message": "Could not transcribe audio",
                "answer": "",
                "score": 0,
                "feedback": "Speech not detected"
            }

        # ----------------------------
        # Load Interview Data
        # ----------------------------
        interview_data = load_interview(session_id)

        current_question = (
            interview_data["interview_history"][-1]["question"]
        )

        # ----------------------------
        # Evaluate Answer
        # ----------------------------
        evaluation = evaluate_answer(
            current_question,
            answer
        )

        # ----------------------------
        # Save Current Answer
        # ----------------------------
        interview_data["interview_history"][-1]["answer"] = answer

        interview_data["interview_history"][-1]["audio_file"] = audio_path

        interview_data["interview_history"][-1]["evaluation"] = {
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get(
                "feedback",
                "No feedback generated"
            )
        }

        # ----------------------------
        # Interview Complete?
        # ----------------------------
        if session["question_count"] >= 10:

            session["status"] = "completed"

            interview_data["status"] = "completed"

            save_interview(
                session_id,
                interview_data
            )

            return {
                "status": "completed",
                "answer": answer,
                "audio_file": audio_path,
                "score": evaluation.get("score", 0),
                "feedback": evaluation.get(
                    "feedback",
                    "Interview completed"
                )
            }

        # ----------------------------
        # Generate Next Question
        # ----------------------------
        next_question = generate_next_question(
            session["resume_profile"],
            current_question,
            answer
        )

        # ----------------------------
        # Speak Next Question
        # ----------------------------
        try:
            await speak(next_question)
        except Exception as tts_error:
            print("TTS Error:", tts_error)

        # ----------------------------
        # Update Session
        # ----------------------------
        session["answers"].append(answer)

        session["questions"].append(
            next_question
        )

        session["question_count"] += 1

        # ----------------------------
        # Store Next Question
        # ----------------------------
        interview_data["interview_history"].append(
            {
                "question_number":
                    session["question_count"],
                "question":
                    next_question,
                "answer":
                    None,
                "audio_file":
                    None,
                "evaluation":
                    None
            }
        )

        save_interview(
            session_id,
            interview_data
        )

        # ----------------------------
        # Response
        # ----------------------------
        return {
            "status": "success",
            "session_id": session_id,
            "answer": answer,
            "audio_file": audio_path,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get(
                "feedback",
                "No feedback generated"
            ),
            "question_number":
                session["question_count"],
            "next_question":
                next_question
        }

    except Exception as e:

        print("Submit Audio Error:", str(e))

        return {
            "status": "error",
            "message": str(e),
            "answer": "",
            "score": 0,
            "feedback": "Processing failed"
        }