import io
import asyncio
import soundfile as sf
import sounddevice as sd
from edge_tts import Communicate
from scipy.signal import resample  # <- Add this
from pinet.voice.transcribe.faster import FasterWhisperTranscriber
from pinet.voice.transcribe.sr import SpeechRecognitionTranscriber


class VoiceIO:
    def __init__(self, transcriber_type="faster", whisper_model="base", device="cpu", is_running=lambda: True):
        if transcriber_type == "faster":
            self.transcriber = FasterWhisperTranscriber(model_size=whisper_model, device=device)
        elif transcriber_type == "sr":
            self.transcriber = SpeechRecognitionTranscriber()
        else:
            raise ValueError(f"Unknown transcriber_type: {transcriber_type}")
        self.sample_rate = 16000
        self.is_running = is_running

    async def listen_async(self) -> str:
        text = await self.transcriber.transcribe()
        return text.strip()

    async def speak_async(self, text: str):
        print(f"🗣️ Speaking: {text}")
        communicate = Communicate(text, voice="en-US-JennyNeural")

        audio_bytes = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])

        # Decode and resample if needed
        buffer = io.BytesIO(audio_bytes)
        data, rate = sf.read(buffer, dtype='float32')

        # Resample to 16kHz if needed
        if rate != self.sample_rate:
            print(f"⚠️ Resampling from {rate}Hz to {self.sample_rate}Hz")
            num_samples = int(len(data) * self.sample_rate / rate)
            data = resample(data, num_samples)

        # Convert stereo to mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        sd.play(data, samplerate=self.sample_rate)
        await asyncio.sleep(len(data) / self.sample_rate)
        sd.stop()
