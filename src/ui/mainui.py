"""Flet-based UI with sliding text window for Flowl translation."""

import flet as ft
import queue
import threading

from app import FlowlApp
from .settings_tab import SettingsTab
from utils.settings import SettingsManager
from utils.logger import logger


class SlidingTextWindow:
    """Main UI window using Flet framework."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Flowl Translation"
        self.page.window.width = 600
        self.page.window.height = 400
        self.page.window.left = 200
        self.page.window.top = 200
        
        # Queue for thread-safe UI updates from worker threads
        self._update_queue = queue.Queue()
        
        # Translation display
        self.translation_display_before = ft.Text(
            size=20,
            opacity=0.5,
            text_align=ft.TextAlign.CENTER,
        )

        self.translation_display_after = ft.Text(
            size=60,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Log display
        self.log_display = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        # Settings button
        settings_button = ft.ElevatedButton(
            "Open Settings",
            on_click=self.open_settings,
        )
        
        # Create tabs
        translation_tab = ft.Tab(
            text="Translations",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.translation_display_before,
                        self.translation_display_after,
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),  
                padding=10,
                expand=True,
            ),
        )
        
        log_tab = ft.Tab(
            text="Logs",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.log_display,
                        ft.ElevatedButton(
                            "Clear Logs",
                            on_click=self.clear_logs,
                        ),
                    ],
                    expand=True,
                ),
                padding=10,
                expand=True,
            ),
        )
        
        tabs = ft.Tabs(
            tabs=[translation_tab, log_tab],
            expand=True,
        )
        
        # Main layout
        self.page.add(
            ft.Text(
                "Real-time Translation",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            settings_button,
            tabs,
        )
        
        # Set up the global logger to use our UI callback
        logger.set_ui_callback(self.on_log_event, self)
        
        # Load settings and initialize FlowlApp with our callbacks
        settings = SettingsManager.load_from_file()
        self.app = FlowlApp(ui_callback=self.on_translation_event, settings=settings)
        
        # Start update processor
        self._start_update_processor()
        
        # Start the app
        self.app.start()
    
    def _start_update_processor(self):
        """Start processing queued updates on background thread."""
        def update_loop():
            while True:
                # Process all queued updates
                updated = False
                while True:
                    try:
                        update_func = self._update_queue.get_nowait()
                        update_func()
                        updated = True
                    except queue.Empty:
                        break
                
                if updated:
                    try:
                        self.page.update()
                    except Exception:
                        pass
                
                time.sleep(0.05)  # Check every 50ms
        
        import time
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def on_translation_event(self, event_type: str, data: dict):
        """Handle translation events from FlowlApp (called from worker thread)."""
        # Queue the update
        self._update_queue.put(lambda: self._update_translation(event_type, data))
    
    def on_log_event(self, level: str, message: str):
        """Handle log events from FlowlApp (called from worker thread)."""
        # Queue the update
        self._update_queue.put(lambda: self._update_log(level, message))
    
    def _update_translation(self, event_type: str, data: dict):
        """Update the translation display."""
        original = data.get('original', '')
        translated = data.get('translated', '')
        
        if event_type == "final" or event_type == "partial":
            self.translation_display_before.value = f"{original}"
            self.translation_display_after.value = f"{translated}"
    
    def _update_log(self, level: str, message: str):
        """Update the log display."""
        # Set color based on log level
        color_map = {
            "ERROR": "#DC143C",    # Crimson Red
            "WARNING": "#FF8C00",  # Dark Orange
            "INFO": "#0066CC",     # Blue
            "DEBUG": "#696969",    # Dim Gray
        }
        color = color_map.get(level, "#000000")
        
        # Create colored text widget
        log_text = ft.Text(
            message,
            color=color,
            size=12,
            selectable=True,
        )
        
        # Add to log display
        self.log_display.controls.append(log_text)
        
        # Limit log entries to prevent memory issues
        if len(self.log_display.controls) > 1000:
            self.log_display.controls.pop(0)
    
    def clear_logs(self, e):
        """Clear the log display."""
        self.log_display.controls.clear()
        self.page.update()
    
    def open_settings(self, e):
        """Open the settings dialog."""
        def on_saved():
            self.restart_app()
        
        # Create and show settings dialog
        settings_dialog = SettingsTab(self.page, on_saved)
        settings_dialog.show()
    
    def restart_app(self):
        """Restart the app with new settings."""
        try:
            self.app.restart()
            logger.info("App restarted with new settings", "UI")
        except Exception as e:
            logger.error(f"Error restarting app: {e}", "UI")
    
    def close_app(self):
        """Handle window close event with proper cleanup."""
        self.app.stop()


def main(page: ft.Page):
    """Main entry point for Flet app."""
    window = SlidingTextWindow(page)
    
    # Handle window close
    def on_window_event(e):
        if e.data == "close":
            window.close_app()
    
    page.window.on_event = on_window_event


def create_ui_app():
    """Create and return the UI application."""
    return main
