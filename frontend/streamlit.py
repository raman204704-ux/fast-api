import streamlit as st
import requests
import json
from streamlit_mic_recorder import mic_recorder

# Configure the page
st.set_page_config(page_title="AI Interviewer", page_icon="🤖", layout="wide")

# Backend URL
API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state variables if they don't exist
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'interview_active' not in st.session_state:
    st.session_state.interview_active = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'interview_completed' not in st.session_state:
    st.session_state.interview_completed = False

# ==========================
# Sidebar: Upload & Setup
# ==========================
st.sidebar.title("🤖 AI Interviewer")
st.sidebar.markdown("Upload your resume to begin the interview process.")

uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

if st.sidebar.button("Create Interview Session"):
    if uploaded_file is not None:
        try:
            with st.spinner("Uploading resume..."):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                upload_res = requests.post(f"{API_BASE_URL}/api/upload-resume", files=files)
                upload_res.raise_for_status()
                file_name = upload_res.json().get("file_name")

            with st.spinner("Parsing resume and creating session..."):
                session_res = requests.post(
                    f"{API_BASE_URL}/api/create-session",
                    params={"file_path": file_name}
                )
                session_res.raise_for_status()
                st.session_state.session_id = session_res.json().get("session_id")
                st.session_state.interview_active = False
                st.session_state.chat_history = []
                st.session_state.interview_completed = False
                st.sidebar.success("Session Created Successfully!")
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Please upload a file first.")

# Display Session ID if available
if st.session_state.session_id:
    st.sidebar.info(f"**Session ID:**\n`{st.session_state.session_id}`")

# ==========================
# Main Area: Interview Chat
# ==========================
st.title("Interview Session")

# 3. Start Interview Button
if st.session_state.session_id and not st.session_state.interview_active and not st.session_state.interview_completed:
    if st.button("Start Interview"):
        with st.spinner("Generating first question..."):
            try:
                start_res = requests.post(f"{API_BASE_URL}/api/start-interview/{st.session_state.session_id}")
                start_res.raise_for_status()
                data = start_res.json()

                st.session_state.chat_history.append({"role": "assistant", "content": data["question"]})
                st.session_state.interview_active = True
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to start interview: {e}")

# Display Chat History (This loop ONLY displays messages, no input boxes!)
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================
# 4. Voice Answer Input (Outside the chat history loop!)
# ==========================
if st.session_state.interview_active and not st.session_state.interview_completed:

    st.subheader("🎤 Record Your Answer")

    # Create a dynamic key based on the chat history length (changes per question)
    widget_key = f"answer_textbox_{len(st.session_state.chat_history)}"

    # Initialize the widget state for this specific question if it doesn't exist
    if widget_key not in st.session_state:
        st.session_state[widget_key] = ""

    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=True,
        key=f"recorder_{len(st.session_state.chat_history)}"
    )

    # Step 1: Transcribe Audio
    if audio and audio.get("bytes"):
        with st.spinner("Converting speech to text..."):
            try:
                files = {
                    "file": (
                        "answer.webm",
                        audio["bytes"],
                        "audio/webm"
                    )
                }
                transcribe_res = requests.post(
                    f"{API_BASE_URL}/api/transcribe-audio", files=files
                )
                transcribe_res.raise_for_status()
                transcribe_data = transcribe_res.json()

                if not transcribe_data.get("success", False):
                    st.error(f"Transcription failed: {transcribe_data.get('error', 'Unknown error')}")
                else:
                    transcript = transcribe_data.get("transcription", "").strip()
                    if not transcript:
                        st.warning("Could not understand speech. Please try again.")
                    else:
                        # Write directly into the dynamic widget's session key
                        st.session_state[widget_key] = transcript
                        st.success("Speech converted to text successfully!")
                        st.rerun()  # Force refresh so textbox shows the new text

            except Exception as e:
                st.error(f"Transcription Error: {e}")

    # Step 2: Editable Textbox (NO `value=` param, key controls state)
    user_answer = st.text_area(
        "Transcribed Answer (you can edit before submitting)",
        height=200,
        key=widget_key
    )

    # Step 3: Submit Text Answer
    if st.button("Submit Answer"):
        if not user_answer.strip():
            st.warning("Please provide an answer.")
        else:
            with st.spinner("Evaluating answer..."):
                try:
                    payload = {"answer": user_answer}
                    submit_res = requests.post(
                        f"{API_BASE_URL}/api/submit-answer/{st.session_state.session_id}",
                        json=payload
                    )
                    submit_res.raise_for_status()
                    data = submit_res.json()

                    st.session_state.chat_history.append(
                        {"role": "user", "content": user_answer}
                    )

                    if data.get("status") == "completed":
                        st.session_state.interview_completed = True
                        st.session_state.interview_active = False
                        st.success("🎉 Interview Completed!")
                    else:
                        evaluation_text = (
                            f"**Score:** {data.get('score', 'N/A')} \n\n"
                            f"**Feedback:** {data.get('feedback', 'No feedback')}"
                        )
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": evaluation_text}
                        )
                        st.session_state.chat_history.append(
                            {"role": "assistant",
                             "content": data.get("next_question", "No next question generated.")}
                        )

                    st.rerun()

                except Exception as e:
                    st.error(f"Evaluation Error: {e}")

# ==========================
# 5. Generate Final Report
# ==========================
if st.session_state.interview_completed:
    st.divider()
    st.subheader("📊 Final Interview Report")

    if st.button("Generate Full Report"):
        with st.spinner("Generating comprehensive report..."):
            try:
                report_res = requests.get(f"{API_BASE_URL}/api/interview-report/{st.session_state.session_id}")
                report_res.raise_for_status()
                report_data = report_res.json()

                candidate_name = report_data.get("candidate_name", "Unknown")
                report_content = report_data.get("report", "No report generated.")

                st.markdown(f"**Candidate Name:** {candidate_name}")
                st.markdown("---")

                if isinstance(report_content, dict):
                    st.json(report_content)
                else:
                    st.markdown(report_content)

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to generate report: {e}")

# ==========================
# Reset Interview
# ==========================
if st.session_state.interview_completed:
    if st.button("Start New Interview"):
        st.session_state.session_id = None
        st.session_state.interview_active = False
        st.session_state.chat_history = []
        st.session_state.interview_completed = False
        st.rerun()