from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QGroupBox, QSpinBox, QComboBox, QCheckBox, 
                               QPushButton, QLabel, QLineEdit, QTabWidget, QWidget, QMessageBox)
from PySide6.QtCore import Qt
from utils.settings import SettingsManager
from utils.device_manager import devices_query

class SettingsTab(QDialog):
    def __init__(self, on_saved):
        super().__init__()
        self.setWindowTitle("Flowl Settings")
        self.setGeometry(100, 100, 600, 500)
        self.setModal(True)
        
        # Load current settings
        self.settings = SettingsManager.load_from_file()
        
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Audio Settings Tab
        audio_tab = self.create_audio_tab()
        tab_widget.addTab(audio_tab, "Audio")
        
        # Language Settings Tab
        language_tab = self.create_language_tab()
        tab_widget.addTab(language_tab, "Language")
        
        # Device Settings Tab
        device_tab = self.create_device_tab()
        tab_widget.addTab(device_tab, "Device")
        
        # Advanced Settings Tab
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # Load current values
        self.load_current_values()

        self._on_saved = on_saved
    
    def create_audio_tab(self):
        """Create the audio settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Audio Rate
        rate_group = QGroupBox("Audio Configuration")
        rate_layout = QFormLayout()
        
        self.rate_combobox = QComboBox()
        self.rate_combobox.addItems(["8000 Hz", "16000 Hz - recommended", "22050 Hz", "44100 Hz", "48000 Hz"])
        rate_layout.addRow("Sample Rate:", self.rate_combobox)
        
        self.frames_combobox = QComboBox()
        self.frames_combobox.addItems(["512", "1024", "2048", "4096", "8192"])
        rate_layout.addRow("Frames per Buffer:", self.frames_combobox)
        
        self.throttle_spinbox = QSpinBox()
        self.throttle_spinbox.setRange(10, 100)
        self.throttle_spinbox.setSuffix(" ms")
        rate_layout.addRow("Throttle Time:", self.throttle_spinbox)
        
        rate_group.setLayout(rate_layout)
        layout.addWidget(rate_group)
        
        # Partial Text Settings
        partial_group = QGroupBox("Partial Text Settings")
        partial_layout = QFormLayout()
        
        self.max_part_words_spinbox = QSpinBox()
        self.max_part_words_spinbox.setRange(1, 100)
        partial_layout.addRow("Max Partial Words:", self.max_part_words_spinbox)
        
        self.min_part_words_spinbox = QSpinBox()
        self.min_part_words_spinbox.setRange(1, 50)
        partial_layout.addRow("Min Partial Words:", self.min_part_words_spinbox)
        
        self.min_part_chars_spinbox = QSpinBox()
        self.min_part_chars_spinbox.setRange(1, 100)
        partial_layout.addRow("Min Partial Characters:", self.min_part_chars_spinbox)
        
        partial_group.setLayout(partial_layout)
        layout.addWidget(partial_group)
        
        layout.addStretch()
        return widget
    
    def create_language_tab(self):
        """Create the language settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Language Selection
        lang_group = QGroupBox("Language Configuration")
        lang_layout = QFormLayout()
        
        self.from_lang_combo = QComboBox()
        self.from_lang_combo.addItems(["English (en)", "Russian (ru)"])
        lang_layout.addRow("From Language:", self.from_lang_combo)
        
        self.to_lang_combo = QComboBox()
        self.to_lang_combo.addItems(["Russian (ru)", "English (en)"])
        lang_layout.addRow("To Language:", self.to_lang_combo)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Model Paths (Read-only display)
        model_group = QGroupBox("Model Paths (Auto-generated)")
        model_layout = QFormLayout()
        
        self.asr_model_label = QLabel()
        self.asr_model_label.setWordWrap(True)
        model_layout.addRow("ASR Model:", self.asr_model_label)
        
        self.mt_model_label = QLabel()
        self.mt_model_label.setWordWrap(True)
        model_layout.addRow("MT Model:", self.mt_model_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        layout.addStretch()
        return widget
    
    def create_device_tab(self):
        """Create the device settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Input Device
        device_group = QGroupBox("Input Device")
        device_layout = QFormLayout()
        
        self.device_select = QComboBox()
        device_dict = devices_query()
        device_items = []
        name_counts = {}

        # Check for duplicate names
        for idx, name in device_dict.items():
            name_counts[name] = name_counts.get(name, 0) + 1

        # Build display items
        for idx, name in device_dict.items():
            if name_counts[name] > 1:
                display_name = f"{name} (#{idx})"
            else:
                display_name = name
            device_items.append((idx, display_name))

        # Populate combobox
        for i, (idx, display_name) in enumerate(device_items):
            if i == 0:
                display_name = f"{display_name} - DEFAULT"
            self.device_select.addItem(display_name, idx)
        
        device_layout.addRow("Device Select:", self.device_select)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_tab(self):
        """Create the advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Information display
        info_group = QGroupBox("Current Configuration")
        info_layout = QFormLayout()
        
        self.config_info = QLabel()
        self.config_info.setWordWrap(True)
        info_layout.addRow("Settings:", self.config_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        return widget
    
    def load_current_values(self):
        """Load current settings values into the form."""
        # Audio settings
        rate_text = f"{self.settings.rate} Hz"
        rate_index = self.rate_combobox.findText(rate_text)
        if rate_index >= 0:
            self.rate_combobox.setCurrentIndex(rate_index)
        else:
            for i in range(self.rate_combobox.count()):
                if rate_text in self.rate_combobox.itemText(i):
                    self.rate_combobox.setCurrentIndex(i)
                    break
        
        frames_text = str(self.settings.frames_per_buffer)
        frames_index = self.frames_combobox.findText(frames_text)
        if frames_index >= 0:
            self.frames_combobox.setCurrentIndex(frames_index)
        self.throttle_spinbox.setValue(self.settings.throttle_ms)
        self.max_part_words_spinbox.setValue(self.settings.max_part_words)
        self.min_part_words_spinbox.setValue(self.settings.min_part_words)
        self.min_part_chars_spinbox.setValue(self.settings.min_part_chars)
        
        # Language settings
        self.from_lang_combo.setCurrentText("English (en)" if self.settings.from_code == "en" else "Russian (ru)")
        self.to_lang_combo.setCurrentText("Russian (ru)" if self.settings.to_code == "ru" else "English (en)")
        
        # Device settings
        # Load saved device
        if self.settings.device_index is not None:
            # Find and select the device in combobox by index
            for i in range(self.device_select.count()):
                if self.device_select.itemData(i) == self.settings.device_index:
                    self.device_select.setCurrentIndex(i)
                    break
        
        # Update model paths
        self.update_model_paths()
        
        # Update config info
        self.update_config_info()
    
    def update_model_paths(self):
        """Update the model path labels."""
        self.asr_model_label.setText(self.settings.model_path)
        self.mt_model_label.setText(self.settings.mt_model_path)
    
    def update_config_info(self):
        """Update the configuration information."""
        info = f"Rate: {self.settings.rate}Hz | "
        info += f"Frames: {self.settings.frames_per_buffer} | "
        info += f"Throttle: {self.settings.throttle_ms}ms | "
        info += f"Languages: {self.settings.from_code}→{self.settings.to_code} | "
        info += f"Device: {self.settings.device_index if self.settings.device_index is not None else 'Auto'}"
        self.config_info.setText(info)
    
    def save_settings(self):
        """Save the current form values to settings."""
        try:
            # Audio settings
            rate_text = self.rate_combobox.currentText()
            self.settings.rate = int(rate_text.split()[0])
            self.settings.frames_per_buffer = int(self.frames_combobox.currentText())
            self.settings.throttle_ms = self.throttle_spinbox.value()
            self.settings.max_part_words = self.max_part_words_spinbox.value()
            self.settings.min_part_words = self.min_part_words_spinbox.value()
            self.settings.min_part_chars = self.min_part_chars_spinbox.value()
            
            # Language settings
            self.settings.from_code = "en" if "English" in self.from_lang_combo.currentText() else "ru"
            self.settings.to_code = "ru" if "Russian" in self.to_lang_combo.currentText() else "en"
            
            # Device settings
            # Save selected device index from combobox userData
            selected_index = self.device_select.currentIndex()
            if selected_index >= 0:
                self.settings.device_index = self.device_select.itemData(selected_index)
            else:
                self.settings.device_index = None
            self.settings.device_name = self.device_select.currentText()

            # Validate settings
            self.validate()

            # Save settings to file
            self.settings.save_to_file()
            self._on_saved()
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Settings", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            return

    def validate(self):
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

        if self.settings.from_code not in ["en", "ru"]:
            raise ValueError(f"Invalid from_code: {self.settings.from_code}")

        if self.settings.to_code not in ["en", "ru"]:
            raise ValueError(f"Invalid to_code: {self.settings.to_code}")
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        from utils.settings import SettingsManager
        default_settings = SettingsManager()
        
        self.rate_combobox.setCurrentIndex(1)
        self.frames_combobox.setCurrentIndex(2)
        self.throttle_spinbox.setValue(default_settings.throttle_ms)
        self.max_part_words_spinbox.setValue(default_settings.max_part_words)
        self.min_part_words_spinbox.setValue(default_settings.min_part_words)
        self.min_part_chars_spinbox.setValue(default_settings.min_part_chars)
        
        self.from_lang_combo.setCurrentText("English (en)")
        self.to_lang_combo.setCurrentText("Russian (ru)")
                
        self.update_model_paths()
        self.update_config_info()