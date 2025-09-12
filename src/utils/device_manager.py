import sounddevice as sd

class DeviceManager:
    def __init__(self):
        self._input_microphone_index = None
        self._input_loopback_index = None
        self._devices = sd.query_devices(kind="input")

    def get_input_microphone_index(self) -> int:
        if self._input_microphone_index is None:
            try:
                # Find the first available microphone device
                for device in self._devices:
                    if device['max_input_channels'] > 0:
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
                    device_name = device['name'].lower()
                    if 'stereo mix' in device_name or 'loopback' in device_name or 'what u hear' in device_name:
                        self._input_loopback_index = device['index']
                        break
                
                if self._input_loopback_index is None:
                    print("No loopback device found (Stereo Mix, etc.)")
            except Exception as e:
                print(f"Error getting input loopback index: {e}")
                self._input_loopback_index = None
        return self._input_loopback_index