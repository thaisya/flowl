import sounddevice as sd

class DeviceManager:
    def __init__(self):
        self._input_microphone_index = None
        self._input_loopback_index = None
        self._devices = sd.query_devices(kind="input")

    def get_input_microphone_index(self) -> int:
        if self._input_microphone_index is None:
            try:
                self._input_microphone_index = self._devices["index"]
            except Exception as e:
                print(f"Error getting input microphone index: {e}")
                self._input_microphone_index = None
        return self._input_microphone_index
    
    def get_input_loopback_index(self) -> int:
        if self._input_loopback_index is None:
            try:
                self._input_loopback_index = self._devices["index"] and self._devices["index"]["name"].lower() == "stereo mix"
            except Exception as e:
                print(f"Error getting input loopback index: {e}")
                self._input_loopback_index = None
        return self._input_loopback_index