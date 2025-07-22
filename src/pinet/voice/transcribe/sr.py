# pinet/voice/transcribe/sr.py

import asyncio
import speech_recognition as sr

class SpeechRecognitionTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8  # adjust if needed

    async def transcribe(self) -> str:
        loop = asyncio.get_event_loop()
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            audio = await loop.run_in_executor(None, self.recognizer.listen, source)
            try:
                return await loop.run_in_executor(None, self.recognizer.recognize_google, audio)
            except sr.UnknownValueError:
                return ""
            except Exception as e:
                print(f"🛑 Transcription error: {e}")
                return ""
