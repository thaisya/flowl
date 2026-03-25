import sounddevice as sd
from typing import Dict
from .logger import logger


class DeviceManager:
    def __init__(self, settings):
        self.settings = settings
        self._devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]

    def _is_device_working(self, device_index: int) -> bool:
        """Test if a specific device can be opened."""
        test_stream = None
        try:
            test_stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self.settings.rate,
                dtype='int16',
            )
            return True
        except Exception as e:
            device_name = "Unknown"
            for device in self._devices:
                if device['index'] == device_index:
                    device_name = device['name']
                    break
            logger.warning(f"Device '{device_name}' (index {device_index}) is not working: {e}", "DEVICE")
            return False
        finally:
            if test_stream:
                test_stream.close()

    def startup(self) -> int | None:
        """Return device from settings or fallback to first working device."""
        # Try to use saved device_index if exists
        if self.settings.device_index is not None:
            if self._is_device_working(self.settings.device_index):
                logger.info(f"Using saved device index: {self.settings.device_index}", "DEVICE")
                return self.settings.device_index
            else:
                logger.warning(f"Saved device {self.settings.device_index} not available, falling back", "DEVICE")

        # Fallback: find first working input device
        for device in self._devices:
            if self._is_device_working(device['index']):
                logger.info(f"Using fallback device: {device['name']} (index: {device['index']})", "DEVICE")
                return device['index']
        
        raise RuntimeError("No working audio input devices found.")


def devices_query(current_device_index: int = None, test_rate: int = 16000) -> Dict[int, str]:
    """Get dict of working input devices {index: name}."""
    devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
    working_devices = {}
    
    for device in devices:
        index = device['index']
        # Skip testing if it's our currently used device because we know it works
        # and opening it again might throw a PortAudio error or lock it.
        if index == current_device_index:
            working_devices[index] = device['name']
            continue
            
        # Test if device is working
        try:
            test_stream = sd.InputStream(
                device=index,
                channels=1,
                samplerate=test_rate,
                dtype='int16',
            )
            test_stream.close()
            working_devices[index] = device['name']
        except:
            pass  # Skip non-working devices
    
    return working_devices

