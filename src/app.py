"""FlowlApp orchestrates the audio engine, queues, workers, and models."""

import threading
from collections import deque
from audio.engine import AudioEngine
from audio.workers import ASRWorker, MTWorker
from models.bundle import ModelBundle
from utils.device_manager import DeviceManager
from utils.settings import SettingsManager
from utils.logger import logger


class FlowlApp:
    def __init__(self, ui_callback=None, settings=None):
        self.mt = None
        self.asr = None
        self.audio_engine = None
        self.device_manager = None
        self.models = None
        self.audio_q: deque[bytes] = deque(maxlen=50)
        self.events_q: deque[tuple[str, str]] = deque(maxlen=100)
        
        # Load settings
        self.settings = settings or SettingsManager.load_from_file()
        
        # Create locks for thread-safe queue operations
        self._audio_lock = threading.Lock()
        self._events_lock = threading.Lock()
        self._ui_callback = ui_callback  # Store UI callback
        self.build_components()

    def build_components(self):
        self.models = ModelBundle(self.settings)
        
        # Initialize device manager and find device
        self.device_manager = DeviceManager(self.settings)
        try:
            device_index = self.device_manager.startup()
        except RuntimeError as e:
            logger.error(f"Audio init failed: {e}", "APP")
            device_index = None

        self.audio_engine = AudioEngine(
            on_audio=self._on_audio, 
            device_index=device_index,
            settings=self.settings,
            noise_reducer=None,
        )
        if device_index is not None:
            logger.info(f"Created audio engine (device: {device_index}) "
                       f"{"with noise cancelling" if self.models.get_noise_reducer() is not None else "without noise cancelling"}")

        self.asr = ASRWorker(self.audio_q, self.events_q, self.models.recognizer, self._audio_lock, self._events_lock, self.settings)
        self.mt = MTWorker(self.events_q, self.models.translate, self._events_lock, self._ui_callback, self.settings)


    def _on_audio(self, in_data: bytes) -> None:
        """Callback for audio data."""
        # deque with maxlen automatically handles overflow by removing the oldest items
        with self._audio_lock:
            self.audio_q.append(in_data)
    
    def start(self) -> None:
        # Start audio engine if available
        if self.audio_engine:
            self.audio_engine.start()
            logger.info("Audio engine started")
        
        # Start worker threads
        self.asr.start()
        self.mt.start()
        
        logger.info("Audio engine and workers started. You can talk now!")

    def restart(self) -> None:
        if self.is_running():
            logger.info("Restarting app with new settings...", "APP")
            self.stop()
            # Reload settings from file to get latest changes
            self.settings = SettingsManager.load_from_file()
            logger.info(f"Reloaded settings - device_index: {self.settings.device_index}", "APP")
            self.build_components()
            self.start()
            logger.info("App restart completed", "APP")
        return None

    def is_running(self) -> bool:
        return self.audio_engine.is_active() if self.audio_engine else False

    def stop(self) -> None:
        """Stop audio engine and worker threads gracefully."""
        logger.info("Stopping FlowlApp...")
        
        # Stop audio engine first to prevent new data from entering queues
        if self.audio_engine:
            self.audio_engine.stop()
            logger.info("Audio engine stopped")
        
        # Signal threads to stop by sending sentinel values
        try:
            with self._audio_lock:
                self.audio_q.append(None)
        except Exception as e:
            logger.warning(f"Error sending audio sentinel: {e}")
            
        try:
            with self._events_lock:
                self.events_q.append(("final", None))  # MTWorker exits on this sentinel
        except Exception as e:
            logger.warning(f"Error sending events sentinel: {e}")
        
        # Join worker threads with timeout
        threads_to_join = []
        if self.asr.is_alive():
            threads_to_join.append(("ASR", self.asr))
        if self.mt.is_alive():
            threads_to_join.append(("MT", self.mt))
        
        for thread_name, thread in threads_to_join:
            thread.join(timeout=2.0)
            if thread.is_alive():
                logger.warning(f"{thread_name} thread did not stop within timeout")
            else:
                logger.info(f"{thread_name} thread stopped")
        
        logger.info("FlowlApp stopped")
    
