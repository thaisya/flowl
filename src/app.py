"""FlowlApp orchestrates the audio engine, queues, workers, and models."""

import queue

from src.audio.engine import AudioEngine
from src.audio.workers import ASRWorker, MTWorker
from src.models.bundle import ModelBundle


class FlowlApp:
    def __init__(self):
        self.audio_q: queue.Queue[bytes] = queue.Queue(maxsize=100)
        self.events_q: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=200)

        self.models = ModelBundle()
        self.audio = AudioEngine(on_audio=self._on_audio)
        self.asr = ASRWorker(self.audio_q, self.events_q, self.models.recognizer)
        self.mt = MTWorker(self.events_q, self.models.translate)

    def _on_audio(self, in_data: bytes) -> None:
        self.audio_q.put_nowait(in_data)

    def start(self) -> None:
        self.audio.start()
        self.asr.start()
        self.mt.start()
        print("Audio engine started. You can talk now")

    def is_running(self) -> bool:
        return self.audio.is_active()

    def stop(self) -> None:
        # signal threads to stop and cleanup
        self.audio_q.put(None)  # ASRWorker exits on None
        self.events_q.put(("final", "exit"))  # MTWorker exits on this sentinel
        self.asr.join(timeout=1.0)
        self.mt.join(timeout=1.0)
        self.audio.stop()


