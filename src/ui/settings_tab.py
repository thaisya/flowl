"""Flet-based settings dialog for Flowl application."""

import flet as ft
from utils.settings import SettingsManager
from utils.device_manager import devices_query


class SettingsTab:
    """Settings dialog using Flet AlertDialog."""
    
    def __init__(self, page: ft.Page, on_saved):
        self.page = page
        self._on_saved = on_saved
        self.settings = SettingsManager.load_from_file()
        try:
            print("Initializing SettingsTab controls...")
            self._create_controls()
            print("Initializing SettingsTab dialog...")
            self._create_dialog()
            print("SettingsTab initialized successfully")
        except Exception as e:
            print(f"Error initializing SettingsTab: {e}")
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
            ],
            value=self.settings.to_code,
            on_change=self._on_language_change,
            width=300,
        )
        
        self.asr_model_label = ft.Text(
            value=self.settings.model_path,
            selectable=True,
            width=400,
        )
        
        self.mt_model_label = ft.Text(
            value=self.settings.mt_model_path,
            selectable=True,
            width=400,
        )
        
        # Device settings
        print("Querying devices...")
        try:
            device_dict = devices_query()
            print(f"Found {len(device_dict)} devices")
        except Exception as e:
            print(f"Error querying devices: {e}")
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
                        ft.Text("Model Paths (Auto-generated)", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                ft.Text("ASR Model:", width=150),
                                self.asr_model_label,
                            ],
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("MT Model:", width=150),
                                self.mt_model_label,
                            ],
                        ),
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
        )
    
    def _create_dialog(self):
        """Create the settings dialog."""
        self.dialog = ft.AlertDialog(
            title=ft.Text("Flowl Settings"),
            content=ft.Container(
                content=self._create_content(),
                width=600,
                height=500,
                padding=10,
            ),
            actions=[
                ft.TextButton("Reset to Defaults", on_click=self.reset_to_defaults),
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ft.ElevatedButton("Save", on_click=self.save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _get_config_info(self) -> str:
        """Get configuration info string."""
        info = f"Rate: {self.settings.rate}Hz | "
        info += f"Frames: {self.settings.frames_per_buffer} | "
        info += f"Throttle: {self.settings.throttle_ms}ms | "
        info += f"Languages: {self.settings.from_code}→{self.settings.to_code} | "
        info += f"Device: {self.settings.device_index if self.settings.device_index is not None else 'Auto'}"
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

            # Validate settings
            self._validate()

            # Save settings to file
            self.settings.save_to_file()
            self._on_saved()
            self._close_dialog(e)
            
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

        if self.settings.min_part_words == 4:
            raise ValueError(f"Invalid min_part_words: {self.settings.min_part_words}")

        if self.settings.min_part_chars <= 0:
            raise ValueError(f"Invalid min_part_chars: {self.settings.min_part_chars}")

        if self.settings.from_code not in ["en", "ru"]:
            raise ValueError(f"Invalid from_code: {self.settings.from_code}")

        if self.settings.to_code not in ["en", "ru"]:
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
    
    def _close_dialog(self, e):
        """Close the settings dialog."""
        self.page.close(self.dialog)
        self.page.update()
    
    def show(self):
        """Show the settings dialog."""
        self.page.open(self.dialog)
        self.page.update()
