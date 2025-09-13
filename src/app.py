"""FlowlApp orchestrates the audio engine, queues, workers, and models."""

from collections import deque

from audio.engine import AudioEngine
from audio.workers import ASRWorker, MTWorker, MixerWorker
from models.bundle import ModelBundle
from utils.device_manager import DeviceManager


class FlowlApp:
    def __init__(self):
        self.audio_q: deque[bytes] = deque(maxlen=100)
        self.mic_q: deque[bytes] = deque(maxlen=100)
        self.loop_q: deque[bytes] = deque(maxlen=100)
        self.events_q: deque[tuple[str, str]] = deque(maxlen=200)

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
            print(f"✓ Created microphone audio engine (device: {mic_index})")
        
        if loopback_device:
            loop_index = loopback_device
            self.audio_loopback = AudioEngine(on_audio=self._on_audio_loopback, device_index=loop_index)
            print(f"✓ Created loopback audio engine (device: {loop_index})")
        
        self.asr = ASRWorker(self.audio_q, self.events_q, self.models.recognizer)
        self.mt = MTWorker(self.events_q, self.models.translate)
        self.mixer = None

    def _on_audio_mic(self, in_data: bytes) -> None:
        """Callback for microphone audio data."""
        # deque with maxlen automatically handles overflow by removing oldest items
        self.mic_q.append(in_data)
    
    def _on_audio_loopback(self, in_data: bytes) -> None:
        """Callback for loopback audio data."""
        # deque with maxlen automatically handles overflow by removing oldest items
        self.loop_q.append(in_data)
    
    def start(self) -> None:
        # Start both audio engines if available
        if self.audio_mic:
            self.audio_mic.start()
            # Device index is already stored in the audio engine
            print(f"✓ Microphone audio engine started")
        
        if self.audio_loopback:
            self.audio_loopback.start()
            # Device index is already stored in the audio engine
            print(f"✓ Loopback audio engine started")

        # Start mixer if at least one source exists
        #TODO not mine logic and will be deleted soon
        if self.audio_mic or self.audio_loopback:
            if self.audio_mic and self.audio_loopback:
                self.mixer = MixerWorker(self.mic_q, self.loop_q, self.audio_q)
            elif self.audio_mic:
                self.mixer = MixerWorker(self.mic_q, deque(maxlen=100), self.audio_q)
            else:
                self.mixer = MixerWorker(deque(maxlen=100), self.loop_q, self.audio_q)
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
        """Stop all audio engines and worker threads gracefully."""
        print("Stopping FlowlApp...")
        
        # Stop audio engines first to prevent new data from entering queues
        if self.audio_mic:
            self.audio_mic.stop()
            print("✓ Microphone audio engine stopped")
        if self.audio_loopback:
            self.audio_loopback.stop()
            print("✓ Loopback audio engine stopped")
        
        # Signal threads to stop by sending sentinel values
        try:
            self.mic_q.append(None)
        except Exception as e:
            print(f"Warning: Error sending mic sentinel: {e}")
            
        try:
            self.loop_q.append(None)
        except Exception as e:
            print(f"Warning: Error sending loopback sentinel: {e}")
            
        try:
            self.audio_q.append(None)  # in case mixer was not started
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
        if self.mixer and self.mixer.is_alive():
            threads_to_join.append(("Mixer", self.mixer))
        
        for thread_name, thread in threads_to_join:
            thread.join(timeout=2.0)
            if thread.is_alive():
                print(f"Warning: {thread_name} thread did not stop within timeout")
            else:
                print(f"✓ {thread_name} thread stopped")
        
        print("FlowlApp stopped")