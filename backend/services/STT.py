import speech_recognition as sr
import os
import io
from pydub import AudioSegment


def transcribe_audio_file(audio_file_path):
    """
    Convert audio file to text using Google Speech Recognition.
    Handles webm/mp3/wav by converting to WAV in-memory using pydub.
    """
    recognizer = sr.Recognizer()

    try:
        # Check file exists
        if not os.path.exists(audio_file_path):
            print(f"File not found: {audio_file_path}")
            return ""

        file_size = os.path.getsize(audio_file_path)
        print(f"Processing file: {audio_file_path}")
        print(f"File size: {file_size} bytes")

        if file_size == 0:
            print("Audio file is empty.")
            return ""

        # --- NEW: Convert audio to WAV format in-memory ---
        # pydub automatically detects the format (webm, mp4, mp3, wav) from the file
        audio_segment = AudioSegment.from_file(audio_file_path)

        # Standardize to mono, 16kHz for best Google Speech API results
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

        # Export to an in-memory WAV buffer
        wav_buffer = io.BytesIO()
        audio_segment.export(wav_buffer, format="wav")
        wav_buffer.seek(0)  # Rewind the buffer for reading
        # --------------------------------------------------

        # Use the in-memory WAV buffer instead of the raw file path
        with sr.AudioFile(wav_buffer) as source:
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)
        print(f"Detected Speech: {text}")
        return text

    except sr.UnknownValueError:
        print("Google could not understand the audio.")
        return ""

    except sr.RequestError as e:
        print(f"Google Speech API Error: {e}")
        return ""

    except ValueError as e:
        print(f"Audio format error: {e}")
        return ""

    except Exception as e:
        print(f"STT Error: {type(e).__name__}: {e}")
        return ""


def listen_from_microphone(timeout=10, phrase_time_limit=60):
    """
    Listen from microphone and convert speech to text.
    (Used for local testing, not needed for the Streamlit app)
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        text = recognizer.recognize_google(audio)
        print(f"Candidate Said: {text}")
        return text

    except sr.WaitTimeoutError:
        print("No speech detected.")
        return ""

    except sr.UnknownValueError:
        print("Could not understand speech.")
        return ""

    except sr.RequestError as e:
        print(f"Speech API Error: {e}")
        return ""

    except Exception as e:
        print(f"Microphone Error: {type(e).__name__}: {e}")
        return ""