"""Application entry point for Flowl real-time translator."""

import sys
from ui import create_ui_app

def main():
    """Start the Flowl UI application."""
    try:
        # Create and run the UI application
        app, window = create_ui_app()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("Manual exit")

def console_mode():
    """Run in console mode (for backward compatibility)."""
    import time
    from app import FlowlApp
    
    app = FlowlApp()
    try:
        app.start()
        while app.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Manual exit")
    finally:
        app.stop()

if __name__ == "__main__":
    # Check if user wants console mode
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        console_mode()
    else:
        main()
