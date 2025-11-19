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
        self.translation_display = ft.TextField(
            read_only=True,
            multiline=True,
            min_lines=10,
            max_lines=20,
            expand=True,
            hint_text="Translation results will appear here...",
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
                content=self.translation_display,
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
        """Start processing queued updates on main thread."""
        # Create a hidden control that we'll update to trigger processing
        self._update_counter = 0
        self._update_trigger = ft.TextField(
            value="0",
            width=0,
            height=0,
            opacity=0,
            visible=False,
        )
        self.page.add(self._update_trigger)
        
        def process_updates(e=None):
            """Process queued updates - runs on main thread via control event."""
            try:
                # Process all queued updates
                while True:
                    try:
                        update_func = self._update_queue.get_nowait()
                        update_func()
                    except queue.Empty:
                        break
                
                # Update the page
                self.page.update()
            except Exception:
                pass  # Silently fail to prevent recursion
        
        # Set up the trigger control's on_change
        self._update_trigger.on_change = process_updates
        
        # Background thread to trigger updates when queue has items
        def trigger_loop():
            while True:
                if not self._update_queue.empty():
                    # Toggle value to trigger on_change (runs on main thread)
                    self._update_counter += 1
                    new_value = str(self._update_counter % 2)
                    # Schedule update on main thread
                    try:
                        # Use page's update method to schedule the change
                        self.page.run_task(lambda: self._set_trigger_value(new_value))
                    except AttributeError:
                        # Fallback if run_task doesn't exist
                        try:
                            self._update_trigger.value = new_value
                            self.page.update()
                        except:
                            pass
                threading.Event().wait(0.05)  # Check every 50ms
        
        trigger_thread = threading.Thread(target=trigger_loop, daemon=True)
        trigger_thread.start()
    
    def _set_trigger_value(self, value):
        """Set trigger value on main thread."""
        self._update_trigger.value = value
        self.page.update()
    
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
            self.translation_display.value = f"{original} → {translated}"
    
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
