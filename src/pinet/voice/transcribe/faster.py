import asyncio
import sounddevice as sd
import numpy as np
import webrtcvad
from faster_whisper import WhisperModel

class FasterWhisperTranscriber:
    def __init__(self, model_size="base", device="cpu"):
        self.model = WhisperModel(model_size, device=device)
        self.vad = webrtcvad.Vad(2)
        self.sample_rate = 16000
        self.block_duration_ms = 30
        self.block_size = int(self.sample_rate * self.block_duration_ms / 1000)

    async def transcribe_audio_chunk(self, audio: np.ndarray) -> str:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        segments, _ = await asyncio.to_thread(
            self.model.transcribe, audio, language="en"
        )
        return " ".join(seg.text.strip() for seg in segments)
    

    async def transcribe(self) -> str:
        print("🎙️ Listening (until silence)...")

        recording = []
        silence_count = 0
        max_initial_silence = 50  # Allow 1.5s before speech starts
        max_post_speech_silence = 33  # ~1s of silence after speech
        speech_started = False

        def is_speech(frame_bytes):
            return self.vad.is_speech(frame_bytes, self.sample_rate)

        def record_until_user_finishes():
            nonlocal recording, silence_count, speech_started
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.block_size,
            ) as stream:
                print("🎧 Stream started")
                while True:
                    block, _ = stream.read(self.block_size)
                    block = block.flatten()
                    frame_bytes = (block * 32767).astype(np.int16).tobytes()

                    if is_speech(frame_bytes):
                        if not speech_started:
                            print("🗣️ Speech started")
                        speech_started = True
                        silence_count = 0
                        recording.append(block)
                    else:
                        if not speech_started:
                            silence_count += 1
                            if silence_count > max_initial_silence:
                                print("🛑 No speech detected.")
                                break
                        else:
                            silence_count += 1
                            if silence_count > max_post_speech_silence:
                                print("⏹️ Speech ended")
                                break

        await asyncio.to_thread(record_until_user_finishes)

        if not recording:
            return ""

        audio = np.concatenate(recording).flatten()
        segments, _ = await asyncio.to_thread(
            self.model.transcribe, audio, language="en"
        )
        text = " ".join(seg.text.strip() for seg in segments)
        print(f"📝 Transcript: {text}")
        return text
