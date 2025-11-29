import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import speech_recognition as sr
from gtts import gTTS
from pathlib import Path


def audio_to_text_mic(duration: int = 5, samplerate: int = 16000) -> str:
    recognizer = sr.Recognizer()
    print(f"🎙️ Recording... please speak clearly for {duration} seconds")

    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        write(tmp_wav.name, samplerate, recording)
        tmp_path = tmp_wav.name

    with sr.AudioFile(tmp_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"✅ Recognized: {text}")
        except sr.UnknownValueError:
            text = "❌ Could not understand the audio."
            print(text)
        except sr.RequestError as e:
            text = f"⚠️ Speech recognition service unavailable: {e}"
            print(text)

    return text


def text_to_audio(text: str) -> Path:
    """Convert chatbot reply text to an audio file (MP3)."""
    tts = gTTS(text)
    temp_path = Path(tempfile.gettempdir()) / "bot_reply.mp3"
    tts.save(str(temp_path))
    return temp_path