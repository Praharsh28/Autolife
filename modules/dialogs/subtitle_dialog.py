"""
Dialog for subtitle generation configuration.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QPushButton, QGroupBox
)
from PyQt5.QtCore import Qt
import logging

class SubtitleGenerationDialog(QDialog):
    """Dialog for configuring subtitle generation settings."""
    
    def __init__(self, parent=None):
        """Initialize the subtitle generation dialog."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        try:
            self.init_ui()
        except Exception as e:
            self.logger.error(f"Failed to initialize dialog: {str(e)}")
            raise
    
    def init_ui(self):
        """Initialize the dialog UI."""
        # Set window properties
        self.setWindowTitle("Subtitle Generation Settings")
        self.setModal(True)
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Language selection
        lang_group = QGroupBox("Language Settings")
        lang_layout = QVBoxLayout()
        
        lang_label = QLabel("Target Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Spanish", "French", "German", "Italian", "Japanese", "Korean", "Chinese"])
        self.lang_combo.setCurrentText("English")
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Output format
        format_group = QGroupBox("Output Format")
        format_layout = QVBoxLayout()
        
        format_label = QLabel("Subtitle Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["srt", "ass", "vtt"])
        self.format_combo.setCurrentText("srt")
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout()
        
        # Word timing
        self.word_timing_check = QCheckBox("Enable Word-Level Timing")
        self.word_timing_check.setToolTip("Generate timestamps for individual words")
        advanced_layout.addWidget(self.word_timing_check)
        
        # Speaker diarization
        self.diarization_check = QCheckBox("Enable Speaker Diarization")
        self.diarization_check.setToolTip("Identify different speakers in the audio")
        advanced_layout.addWidget(self.diarization_check)
        
        # Max speakers
        speakers_layout = QHBoxLayout()
        speakers_label = QLabel("Maximum Speakers:")
        self.max_speakers_spin = QSpinBox()
        self.max_speakers_spin.setRange(1, 10)
        self.max_speakers_spin.setValue(2)
        self.max_speakers_spin.setEnabled(False)
        speakers_layout.addWidget(speakers_label)
        speakers_layout.addWidget(self.max_speakers_spin)
        advanced_layout.addLayout(speakers_layout)
        
        # Connect diarization checkbox to max speakers spinbox
        self.diarization_check.toggled.connect(self.max_speakers_spin.setEnabled)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        """
        Get the dialog values.
        
        Returns:
            dict: Dictionary containing the dialog values
        """
        return {
            'language': self.lang_combo.currentText().lower(),
            'output_format': self.format_combo.currentText(),
            'word_timing': self.word_timing_check.isChecked(),
            'speaker_diarization': self.diarization_check.isChecked(),
            'max_speakers': self.max_speakers_spin.value() if self.diarization_check.isChecked() else 1
        }
