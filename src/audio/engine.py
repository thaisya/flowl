"""Audio engine: manages sounddevice and pushes frames to a queue via callback."""

from typing import Callable
import sounddevice as sd
import numpy as np
import torch

from utils import AUDIO_RATE, FRAMES_PER_BUFFER

class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None], device_index: int, noise_reducer=None, device="cpu"):
        self._on_audio = on_audio
        self._stream = None
        self._input_device_index = device_index
        self._noise_reducer = noise_reducer
        self._device = device

    def _callback(self, in_data: np.ndarray, frame_count: int, time_info, status) -> None:
        if status:
            print(f"Audio callback Status: {status}")

        # Validate input data
        if in_data is None or len(in_data) == 0:
            return  # Skip processing empty audio data

        try:
            # Apply noise reduction if available
            if self._noise_reducer is not None:
                try:
                    # Convert to float32 for noise reduction
                    audio_float = in_data.astype(np.float32) / 32768.0

                    # Applying noise reduction filter through tensor
                    tensor_data = torch.from_numpy(audio_float).to(self._device)
                    if tensor_data.ndim == 1:
                        tensor_data = tensor_data.unsqueeze(0)
                    denoised_data = self._noise_reducer(tensor_data)

                    # Convert back to int16
                    in_data = (denoised_data.cpu().numpy() * 32768).astype(np.int16)[0]
                except Exception as nr_error:
                    print(f"[AUDIO WARNING] Noise reduction failed: {nr_error}")
                    # Continue with original audio if noise reduction fails

            # in_data is int16 ndarray; forward raw PCM s16le bytes
            self._on_audio(in_data.tobytes())
        except Exception as e:
            print(f"[AUDIO ERROR] Callback error: {e}")

    def start(self) -> None:
        if self._input_device_index is None:
            print("[AUDIO WARNING] No device index provided, cannot start audio engine")
            return None
            
        try:
            if self._stream is None:
                self._stream = sd.InputStream(
                    device=self._input_device_index,
                    blocksize=FRAMES_PER_BUFFER,
                    samplerate=AUDIO_RATE,
                    channels=1,
                    dtype='int16',
                    callback=self._callback,
                )
            self._stream.start()
            print(f"[AUDIO] Audio engine started on device {self._input_device_index}")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to start audio engine: {e}")
            self._stream = None

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    def stop(self) -> None:
        if self._stream is not None:
            try:
                if self._stream.active:
                    self._stream.stop()
                self._stream.close()
                print("[AUDIO] Audio engine stopped")
            except Exception as e:
                print(f"[AUDIO ERROR] Error stopping audio engine: {e}")
            finally:
                self._stream = None


