"""FlowlApp orchestrates the audio engine, queues, workers, and models."""

from collections import deque

from audio.engine import AudioEngine
from audio.workers import ASRWorker, MTWorker
from models.bundle import ModelBundle
from utils.device_manager import DeviceManager


class FlowlApp:
    def __init__(self):
        self.audio_q: deque[bytes] = deque(maxlen=100)
        self.events_q: deque[tuple[str, str]] = deque(maxlen=200)

        self.models = ModelBundle()
        
        # Initialize device manager and find device
        self.device_manager = DeviceManager()
        device_index = self.device_manager.startup()

        self.audio_engine = AudioEngine(on_audio=self._on_audio, device_index=device_index)
        if device_index is not None:
            print(f"✓ Created audio engine (device: {device_index})")

        self.asr = ASRWorker(self.audio_q, self.events_q, self.models.recognizer)
        self.mt = MTWorker(self.events_q, self.models.translate)

    def _on_audio(self, in_data: bytes) -> None:
        """Callback for audio data."""
        # deque with maxlen automatically handles overflow by removing oldest items
        self.audio_q.append(in_data)
    
    def start(self) -> None:
        # Start audio engine if available
        if self.audio_engine:
            self.audio_engine.start()
            print(f"✓ Audio engine started")
        
        # Start worker threads
        self.asr.start()
        self.mt.start()
        
        print("✓ Audio engine and workers started. You can talk now!")

    def is_running(self) -> bool:
        return self.audio_engine.is_active() if self.audio_engine else False

    def stop(self) -> None:
        """Stop audio engine and worker threads gracefully."""
        print("Stopping FlowlApp...")
        
        # Stop audio engine first to prevent new data from entering queues
        if self.audio_engine:
            self.audio_engine.stop()
            print("✓ Audio engine stopped")
        
        # Signal threads to stop by sending sentinel values
        try:
            self.audio_q.append(None)
        except Exception as e:
            print(f"Warning: Error sending audio sentinel: {e}")
            
        try:
            self.events_q.append(("final", "exit"))  # MTWorker exits on this sentinel
        except Exception as e:
            print(f"Warning: Error sending events sentinel: {e}")
        
        # Join worker threads with timeout
        threads_to_join = []
        if self.asr.is_alive():
            threads_to_join.append(("ASR", self.asr))
        if self.mt.is_alive():
            threads_to_join.append(("MT", self.mt))
        
        for thread_name, thread in threads_to_join:
            thread.join(timeout=2.0)
            if thread.is_alive():
                print(f"Warning: {thread_name} thread did not stop within timeout")
            else:
                print(f"✓ {thread_name} thread stopped")
        
        print("FlowlApp stopped")