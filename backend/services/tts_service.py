import edge_tts
import pygame
import uuid

VOICE = "en-US-AriaNeural"


async def generate_speech(text, output_file="question.mp3"):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE
    )

    await communicate.save(output_file)

    return output_file


def play_audio(audio_file):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pass


async def speak(text):

    output_file = f"question_{uuid.uuid4().hex}.mp3"

    await generate_speech(text, output_file)

    play_audio(output_file)

    print(f"AI: {text}")