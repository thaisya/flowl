import sounddevice as sd
from .utils import AUDIO_RATE, MIC_MODE


class DeviceManager:
    def __init__(self):
        self._input_microphone_index = None
        self._input_loopback_index = None
        self._devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
        self._working_microphone_index = None
        self._working_loopback_index = None

    def _is_device_working(self, device_index: int) -> bool:
        """Test if a specific device can be opened."""
        try:
            test_stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=AUDIO_RATE,
                dtype='int16',
            )
            test_stream.close()
            return True
        except Exception as e:
            print(f"Device is not working: {e}")
            return False

    def _is_loopback_device(self, device: dict) -> bool:
        """Check if a device is a loopback device based on its name."""
        device_name = device['name'].lower()
        return ('stereo mix' in device_name or 'loopback' in device_name or 
                'what u hear' in device_name)

    def startup(self) -> int | None:
        """Find and return a working audio input device based on MIC_MODE setting."""
        active_device = None

        if MIC_MODE:
            for device in self._devices:
                if not self._is_loopback_device(device) and self._is_device_working(device['index']):
                    active_device = device
                    print(f"✓ Found microphone device: {device['name']} (index: {device['index']})")
                    break
        else:
            for device in self._devices:
                if self._is_loopback_device(device) and self._is_device_working(device['index']):
                    active_device = device
                    print(f"✓ Found loopback device: {device['name']} (index: {device['index']})")
                    break

        device_result = active_device['index'] if active_device else None
        if not device_result:
            raise RuntimeError("No working audio input devices found. Please check your audio settings.")

        return device_result


    def startup_dual(self) -> tuple[int | None, int | None]:
        """
        Startup method that finds both microphone and loopback devices.
        Returns (mic_index, loopback_index).
        Either can be None if not available.
        NOTE! Do not use in current implementation.
        """
        mic_device = None
        loopback_device = None
        
        # Find microphone device
        for device in self._devices:
            if not self._is_loopback_device(device) and self._is_device_working(device['index']):
                mic_device = device
                self._working_microphone_index = device['index']
                self._input_microphone_index = device['index']
                print(f"✓ Found microphone device: {device['name']} (index: {device['index']})")
                break
        
        # Find loopback device
        for device in self._devices:
            if self._is_loopback_device(device) and self._is_device_working(device['index']):
                loopback_device = device
                self._working_loopback_index = device['index']
                self._input_loopback_index = device['index']
                print(f"✓ Found loopback device: {device['name']} (index: {device['index']})")
                break
        
        # Return both devices (can be None if not found)
        mic_result = mic_device['index'] if mic_device else None
        loopback_result = loopback_device['index'] if loopback_device else None
        
        if not mic_device and not loopback_device:
            raise RuntimeError("No working audio input devices found. Please check your audio settings.")
        
        #return mic_result, loopback_result
        return None

    def get_working_microphone(self) -> tuple[str, int] | None:
        """Get the working microphone device type and index."""
        if self._working_microphone_index is None:
            return None
        return 'microphone', self._working_microphone_index

    def get_working_loopback(self) -> tuple[str, int] | None:
        """Get the working loopback device type and index."""
        if self._working_loopback_index is None:
            return None
        return 'loopback', self._working_loopback_index

    def get_input_microphone_index(self) -> int:
        if self._input_microphone_index is None:
            try:
                # Find the first available microphone device (exclude loopback)
                for device in self._devices:
                    if not self._is_loopback_device(device) and device['max_input_channels'] > 0:
                        self._input_microphone_index = device['index']
                        break
                
                if self._input_microphone_index is None:
                    print("No microphone device found")
            except Exception as e:
                print(f"Error getting input microphone index: {e}")
                self._input_microphone_index = None
        return self._input_microphone_index
    
    def get_input_loopback_index(self) -> int:
        if self._input_loopback_index is None:
            try:
                # Look for stereo mix or similar loopback device
                for device in self._devices:
                    if self._is_loopback_device(device):
                        self._input_loopback_index = device['index']
                        break
                
                if self._input_loopback_index is None:
                    print("No loopback device found (Stereo Mix, etc.)")
            except Exception as e:
                print(f"Error getting input loopback index: {e}")
                self._input_loopback_index = None
        return self._input_loopback_index
