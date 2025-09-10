"""Application entry point for Flowl real-time translator."""

import time
from app import FlowlApp

def main():
    """Create the app, start it, and keep alive until interrupted."""
    app = FlowlApp()
    try:
        app.start()
        while app.is_running():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Manual exit")
    finally:
        app.stop()

def shutdown():
    """Deprecated: kept for backward compatibility; use FlowlApp.stop()."""
    pass

if __name__ == "__main__":
    main()

