"""FlowlApp orchestrates the audio engine, queues, workers, and models."""

import queue

from audio.engine import AudioEngine
from audio.workers import ASRWorker, MTWorker, MixerWorker
from models.bundle import ModelBundle
from utils.device_manager import DeviceManager
from utils import AUDIO_RATE


class FlowlApp:
    def __init__(self):
        self.audio_q: queue.Queue[bytes] = queue.Queue(maxsize=100)
        self.mic_q: queue.Queue[bytes] = queue.Queue(maxsize=100)
        self.loop_q: queue.Queue[bytes] = queue.Queue(maxsize=100)
        self.events_q: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=200)

        self.models = ModelBundle()
        
        # Initialize device manager and find both devices
        self.device_manager = DeviceManager()
        mic_device, loopback_device = self.device_manager.startup_dual()
        
        # Create separate audio engines for microphone and loopback
        self.audio_mic = None
        self.audio_loopback = None
        
        if mic_device:
            mic_index = mic_device
            self.audio_mic = AudioEngine(on_audio=self._on_audio_mic, device_index=mic_index)
            print(f"✓ Created microphone audio engine")
        
        if loopback_device:
            loop_index = loopback_device
            self.audio_loopback = AudioEngine(on_audio=self._on_audio_loopback, device_index=loop_index)
            print(f"✓ Created loopback audio engine")
        
        self.asr = ASRWorker(self.audio_q, self.events_q, self.models.recognizer)
        self.mt = MTWorker(self.events_q, self.models.translate)
        self.mixer = None

    def _on_audio_mic(self, in_data: bytes) -> None:
        """Callback for microphone audio data."""
        self.mic_q.put_nowait(in_data)
    
    def _on_audio_loopback(self, in_data: bytes) -> None:
        """Callback for loopback audio data."""
        self.loop_q.put_nowait(in_data)
    
    def start(self) -> None:
        # Start both audio engines if available
        if self.audio_mic:
            self.audio_mic.start()
            mic_info = self.device_manager.get_working_microphone()
            mic_index = mic_info[1] if isinstance(mic_info, tuple) else self.device_manager.get_input_microphone_index()
            print(f"✓ Microphone audio engine started (index: {mic_index})")
        
        if self.audio_loopback:
            self.audio_loopback.start()
            loop_info = self.device_manager.get_working_loopback()
            loop_index = loop_info[1] if isinstance(loop_info, tuple) else self.device_manager.get_input_loopback_index()
            print(f"✓ Loopback audio engine started (index: {loop_index})")

        # Start mixer if at least one source exists
        if self.audio_mic or self.audio_loopback:
            if self.audio_mic and self.audio_loopback:
                self.mixer = MixerWorker(self.mic_q, self.loop_q, self.audio_q)
            elif self.audio_mic:
                self.mixer = MixerWorker(self.mic_q, queue.Queue(), self.audio_q)
            else:
                self.mixer = MixerWorker(queue.Queue(), self.loop_q, self.audio_q)
            self.mixer.start()
        
        # Start worker threads
        self.asr.start()
        self.mt.start()
        
        print("✓ All audio engines and workers started. You can talk now!")

    def is_running(self) -> bool:
        mic_active = self.audio_mic.is_active() if self.audio_mic else False
        loopback_active = self.audio_loopback.is_active() if self.audio_loopback else False
        return mic_active or loopback_active

    def stop(self) -> None:
        # signal threads to stop and cleanup
        # propagate sentinel to mixer inputs
        try:
            self.mic_q.put_nowait(None)
        except Exception:
            pass
        try:
            self.loop_q.put_nowait(None)
        except Exception:
            pass
        self.audio_q.put(None)  # in case mixer was not started
        self.events_q.put(("final", "exit"))  # MTWorker exits on this sentinel
        
        # Only join threads that are actually running
        if self.asr.is_alive():
            self.asr.join(timeout=1.0)
        if self.mt.is_alive():
            self.mt.join(timeout=1.0)
        
        # Stop both audio engines
        if self.audio_mic:
            self.audio_mic.stop()
        if self.audio_loopback:
            self.audio_loopback.stop()

        # Join mixer thread
        if self.mixer and self.mixer.is_alive():
            self.mixer.join(timeout=1.0)