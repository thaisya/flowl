"""Flet-based settings dialog for Flowl application."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from utils.settings import SettingsManager
from utils.device_manager import devices_query
from utils.logger import logger
from typing import Callable


class SettingsTab:
    """Manages the settings tab UI and logic."""
    def __init__(self, page: ft.Page, on_saved: Callable[[], None] = None, on_close: Callable[[], None] = None, active_device_index: int = None):
        self.page = page
        self.settings = SettingsManager.load_from_file()
        self._on_saved = on_saved
        self._on_close_callback = on_close
        self.active_device_index = active_device_index
        
        try:
            logger.info("Initializing SettingsTab controls...")
            self._create_controls()
            self.content = self._create_content()
            logger.info("SettingsTab initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SettingsTab: {e}")
            import traceback
            traceback.print_exc()
            self._show_error("Initialization Error", str(e))
    
    def _create_controls(self):
        """Create all form controls."""
        # Audio settings
        self.rate_dropdown = ft.Dropdown(
            label="Sample Rate",
            options=[
                ft.dropdown.Option("8000", "8000 Hz"),
                ft.dropdown.Option("16000", "16000 Hz - recommended"),
                ft.dropdown.Option("22050", "22050 Hz"),
                ft.dropdown.Option("44100", "44100 Hz"),
                ft.dropdown.Option("48000", "48000 Hz"),
            ],
            value=str(self.settings.rate),
            width=300,
        )
        
        self.frames_dropdown = ft.Dropdown(
            label="Frames per Buffer",
            options=[
                ft.dropdown.Option("512", "512"),
                ft.dropdown.Option("1024", "1024"),
                ft.dropdown.Option("2048", "2048"),
                ft.dropdown.Option("4096", "4096"),
                ft.dropdown.Option("8192", "8192"),
            ],
            value=str(self.settings.frames_per_buffer),
            width=300,
        )
        
        self.throttle_field = ft.TextField(
            label="Throttle Time (ms)",
            value=str(self.settings.throttle_ms),
            input_filter=ft.NumbersOnlyInputFilter(),
            width=300,
        )
        
        self.max_part_words_field = ft.TextField(
            label="Max Partial Words",
            value=str(self.settings.max_part_words),
            input_filter=ft.NumbersOnlyInputFilter(),
            width=300,
        )
        
        self.min_part_words_field = ft.TextField(
            label="Min Partial Words",
            value=str(self.settings.min_part_words),
            input_filter=ft.NumbersOnlyInputFilter(),
            width=300,
        )
        
        self.min_part_chars_field = ft.TextField(
            label="Min Partial Characters",
            value=str(self.settings.min_part_chars),
            input_filter=ft.NumbersOnlyInputFilter(),
            width=300,
        )
        
        # Language settings
        self.from_lang_dropdown = ft.Dropdown(
            label="From Language",
            options=[
                ft.dropdown.Option("en", "English (en)"),
                ft.dropdown.Option("ru", "Russian (ru)"),
                ft.dropdown.Option("ko", "Korean (ko)"),
            ],
            value=self.settings.from_code,
            on_change=self._on_language_change,
            width=300,
        )
        
        self.to_lang_dropdown = ft.Dropdown(
            label="To Language",
            options=[
                ft.dropdown.Option("ru", "Russian (ru)"),
                ft.dropdown.Option("en", "English (en)"),
                ft.dropdown.Option("ko", "Korean (ko)"),
            ],
            value=self.settings.to_code,
            on_change=self._on_language_change,
            width=300,
        )
        
        self.asr_model_label = ft.TextField(
            label="ASR Model Path",
            value=self.settings.model_path,
            width=400,
        )
        
        self.mt_model_label = ft.TextField(
            label="MT Model Path",
            value=self.settings.mt_model_path,
            width=400,
        )
        
        # Device settings
        logger.info("Querying devices...")
        try:
            device_dict = devices_query(current_device_index=self.active_device_index, test_rate=self.settings.rate)
            logger.info(f"Found {len(device_dict)} devices")
        except Exception as e:
            logger.error(f"Error querying devices: {e}")
            device_dict = {}
        
        device_options = []
        name_counts = {}

        for idx, name in device_dict.items():
            name_counts[name] = name_counts.get(name, 0) + 1

        for idx, name in device_dict.items():
            if name_counts[name] > 1:
                display_name = f"{name} (#{idx})"
            else:
                display_name = name
            if idx == list(device_dict.keys())[0]:
                display_name = f"{display_name} - DEFAULT"
            device_options.append(ft.dropdown.Option(str(idx), display_name))
        
        self.device_dropdown = ft.Dropdown(
            label="Input Device",
            options=device_options,
            value=str(self.settings.device_index) if self.settings.device_index is not None else None,
            width=400,
        )
        
        # Keybind settings
        self.lock_hotkey_field = ft.TextField(
            label="Lock Screen Hotkey",
            value=self.settings.lock_hotkey,
            hint_text="e.g. ctrl+alt+l",
            width=300,
        )
        
        self.max_screen_words_field = ft.TextField(
            label="Max Screen Words (0 to disable)",
            value=str(self.settings.max_screen_words),
            input_filter=ft.NumbersOnlyInputFilter(),
            width=300,
        )
        
        # Config info
        self.config_info = ft.Text(
            value=self._get_config_info(),
            selectable=True,
            width=500,
        )
    
    def _create_content(self):
        """Create the main content with tabs."""
        # Audio tab
        audio_tab = ft.Tab(
            text="Audio",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Audio Configuration", size=16, weight=ft.FontWeight.BOLD),
                        self.rate_dropdown,
                        self.frames_dropdown,
                        self.throttle_field,
                        ft.Divider(),
                        ft.Text("Partial Text Settings", size=16, weight=ft.FontWeight.BOLD),
                        self.max_part_words_field,
                        self.min_part_words_field,
                        self.min_part_chars_field,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
                padding=10,
            ),
        )
        
        # Language tab
        language_tab = ft.Tab(
            text="Language",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Language Configuration", size=16, weight=ft.FontWeight.BOLD),
                        self.from_lang_dropdown,
                        self.to_lang_dropdown,
                        ft.Divider(),
                        ft.Text("Model Paths", size=16, weight=ft.FontWeight.BOLD),
                        self.asr_model_label,
                        self.mt_model_label,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
                padding=10,
            ),
        )
        
        # Device tab
        device_tab = ft.Tab(
            text="Device",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Input Device", size=16, weight=ft.FontWeight.BOLD),
                        self.device_dropdown,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
                padding=10,
            ),
        )
        
        # Advanced tab
        advanced_tab = ft.Tab(
            text="Advanced",
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Keybind Settings", size=16, weight=ft.FontWeight.BOLD),
                        self.lock_hotkey_field,
                        ft.Divider(),
                        ft.Text("Display Settings", size=16, weight=ft.FontWeight.BOLD),
                        self.max_screen_words_field,
                        ft.Divider(),
                        ft.Text("Current Configuration", size=16, weight=ft.FontWeight.BOLD),
                        self.config_info,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
                padding=10,
            ),
        )
        
        return ft.Tabs(
            tabs=[audio_tab, language_tab, device_tab, advanced_tab],
            expand=True,
            scrollable=False,
        )
    
    def _get_config_info(self) -> str:
        """Get configuration info string."""
        info = f"Rate: {self.settings.rate}Hz | "
        info += f"Frames: {self.settings.frames_per_buffer} | "
        info += f"Throttle: {self.settings.throttle_ms}ms | "
        info += f"Languages: {self.settings.from_code}→{self.settings.to_code} | "
        info += f"Device: {self.settings.device_index if self.settings.device_index is not None else 'Auto'} | "
        info += f"Lock Hotkey: {self.settings.lock_hotkey}"
        return info
    
    def _update_model_paths(self):
        """Update the model path labels."""
        self.asr_model_label.value = self.settings.model_path
        self.mt_model_label.value = self.settings.mt_model_path
    
    def _update_config_info(self):
        """Update the configuration information."""
        self.config_info.value = self._get_config_info()
    
    def _on_language_change(self, e):
        """Handle language dropdown changes to update model paths."""
        self.settings.from_code = self.from_lang_dropdown.value
        self.settings.to_code = self.to_lang_dropdown.value
        self._update_model_paths()
        self._update_config_info()
        self.page.update()
    
    def reset_to_defaults(self, e):
        """Reset all settings to default values."""
        default_settings = SettingsManager()
        
        self.rate_dropdown.value = str(default_settings.rate)
        self.frames_dropdown.value = str(default_settings.frames_per_buffer)
        self.throttle_field.value = str(default_settings.throttle_ms)
        self.max_part_words_field.value = str(default_settings.max_part_words)
        self.min_part_words_field.value = str(default_settings.min_part_words)
        self.min_part_chars_field.value = str(default_settings.min_part_chars)
        
        self.from_lang_dropdown.value = default_settings.from_code
        self.to_lang_dropdown.value = default_settings.to_code
        
        self.lock_hotkey_field.value = default_settings.lock_hotkey
        self.max_screen_words_field.value = str(default_settings.max_screen_words)
        
        self.settings = default_settings
        self._update_model_paths()
        self._update_config_info()
        self.page.update()
    
    def save_settings(self, e):
        """Save the current form values to settings."""
        try:
            # Audio settings
            self.settings.rate = int(self.rate_dropdown.value)
            self.settings.frames_per_buffer = int(self.frames_dropdown.value)
            self.settings.throttle_ms = int(self.throttle_field.value)
            self.settings.max_part_words = int(self.max_part_words_field.value)
            self.settings.min_part_words = int(self.min_part_words_field.value)
            self.settings.min_part_chars = int(self.min_part_chars_field.value)
            
            # Language settings
            self.settings.from_code = self.from_lang_dropdown.value
            self.settings.to_code = self.to_lang_dropdown.value
            
            # Update paths dictionaries with custom user input
            self.settings.asr_model_paths[self.settings.from_code] = self.asr_model_label.value
            pair = f"{self.settings.from_code}-{self.settings.to_code}"
            self.settings.mt_model_paths[pair] = self.mt_model_label.value
            
            # Device settings
            if self.device_dropdown.value:
                self.settings.device_index = int(self.device_dropdown.value)
                for option in self.device_dropdown.options:
                    if option.key == self.device_dropdown.value:
                        self.settings.device_name = option.text
                        break
            else:
                self.settings.device_index = None
                self.settings.device_name = None

            # Keybind settings
            self.settings.lock_hotkey = self.lock_hotkey_field.value.strip()

            # Display settings
            self.settings.max_screen_words = int(self.max_screen_words_field.value)

            # Validate settings
            self._validate()

            # Save settings to file
            self.settings.save_to_file()
            if self._on_saved:
                self._on_saved()
            self._close_actions()
            
        except ValueError as ve:
            self._show_error("Invalid Settings", str(ve))
        except Exception as ex:
            self._show_error("Error", f"An unexpected error occurred: {str(ex)}")
    
    def _validate(self):
        """Validate settings values."""
        if self.settings.rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(f"Invalid audio rate: {self.settings.rate}")

        if self.settings.frames_per_buffer not in [512, 1024, 2048, 4096, 8192]:
            raise ValueError(f"Invalid frames_per_buffer: {self.settings.frames_per_buffer}")

        if self.settings.throttle_ms <= 0:
            raise ValueError(f"Invalid throttle_ms: {self.settings.throttle_ms}")

        if self.settings.max_part_words <= 0:
            raise ValueError(f"Invalid max_part_words: {self.settings.max_part_words}")

        if self.settings.min_part_words <= 0:
            raise ValueError(f"Invalid min_part_words: {self.settings.min_part_words}")

        if self.settings.min_part_chars <= 0:
            raise ValueError(f"Invalid min_part_chars: {self.settings.min_part_chars}")
            
        if self.settings.max_screen_words < 0:
            raise ValueError(f"Invalid max_screen_words: {self.settings.max_screen_words}")

        if self.settings.from_code not in ["en", "ru", "ko"]:
            raise ValueError(f"Invalid from_code: {self.settings.from_code}")

        if self.settings.to_code not in ["en", "ru", "ko"]:
            raise ValueError(f"Invalid to_code: {self.settings.to_code}")
    
    def _show_error(self, title: str, message: str):
        """Show an error dialog."""
        error_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda e: self.page.close_dialog())],
        )
        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()
    
    def _close_actions(self, e=None):
        if self._on_close_callback:
            self._on_close_callback()
            
            
if __name__ == "__main__":
    import sys
    
    def main(page: ft.Page):
        page.title = "Flowl Settings"
        page.window.width = 600
        page.window.height = 550
        page.window.center()
        
        def on_save_success():
            # Exit 0 means user saved successfully
            page.window.destroy()
            sys.exit(0)
            
        def on_close():
            # Exit 1 means user canceled
            page.window.destroy()
            sys.exit(1)
            
        settings_app = SettingsTab(page, on_saved=on_save_success, on_close=on_close)
        
        # Build the standalone UI container
        page.add(
            ft.Column(
                [
                    ft.Row(
                        [ft.Text("Flowl Settings", size=24, weight=ft.FontWeight.BOLD)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=settings_app.content,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.TextButton("Reset", on_click=settings_app.reset_to_defaults),
                            ft.TextButton("Cancel", on_click=settings_app._close_actions),
                            ft.ElevatedButton("Save", on_click=settings_app.save_settings),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    )
                ],
                expand=True
            )
        )
        page.update()
        
    ft.app(target=main)
