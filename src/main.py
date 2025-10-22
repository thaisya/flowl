"""Application entry point for Flowl real-time translator."""

import sys
from utils.settings import get_console_mode
from utils.logger import logger

def main():
    """Start the Flowl UI application."""
    from ui import create_ui_app
    try:
        # Create and run the UI application
        app, window = create_ui_app()
        app.exec()
    except KeyboardInterrupt:
        logger.info("Manual exit")

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
        logger.info("Manual exit")
    finally:
        app.stop()

if __name__ == "__main__":
    # Check if user wants console mode
    if get_console_mode():
        console_mode()
    else:
        main()
