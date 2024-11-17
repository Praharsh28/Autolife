from PyQt5.QtWidgets import (QComboBox, QSpinBox, QLabel, QFileDialog,
                             QLineEdit, QPushButton, QHBoxLayout, QCheckBox,
                             QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt
from .base_dialog import BaseDialog

class FormatConversionDialog(BaseDialog):
    """Dialog for format conversion settings."""
    
    description = """Convert media files between different formats with customizable
                    quality settings and encoding options."""
    
    def __init__(self, parent=None):
        super().__init__("Format Conversion", parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Input file selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select input file...")
        self.file_path.setReadOnly(True)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(QLabel("Input File:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        self.content_layout.addLayout(file_layout)
        
        # Output format
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP4", "MKV", "AVI", "MOV",  # Video formats
            "MP3", "WAV", "AAC", "FLAC",  # Audio formats
            "SRT", "ASS", "VTT", "SSA"    # Subtitle formats
        ])
        
        format_layout.addWidget(QLabel("Output Format:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        self.content_layout.addLayout(format_layout)
        
        # Video settings group
        video_group = QGroupBox("Video Settings")
        video_layout = QGridLayout()
        
        # Video codec
        self.video_codec = QComboBox()
        self.video_codec.addItems(["H.264", "H.265/HEVC", "VP9", "AV1"])
        video_layout.addWidget(QLabel("Codec:"), 0, 0)
        video_layout.addWidget(self.video_codec, 0, 1)
        
        # Video quality
        self.video_quality = QSpinBox()
        self.video_quality.setRange(1, 51)  # CRF scale
        self.video_quality.setValue(23)  # Default CRF value
        self.video_quality.setToolTip("Lower values = higher quality (18-28 recommended)")
        video_layout.addWidget(QLabel("Quality (CRF):"), 1, 0)
        video_layout.addWidget(self.video_quality, 1, 1)
        
        # Resolution
        self.resolution = QComboBox()
        self.resolution.addItems([
            "Original", "4K (3840x2160)", "1080p", "720p", "480p"
        ])
        video_layout.addWidget(QLabel("Resolution:"), 2, 0)
        video_layout.addWidget(self.resolution, 2, 1)
        
        video_group.setLayout(video_layout)
        self.content_layout.addWidget(video_group)
        
        # Audio settings group
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QGridLayout()
        
        # Audio codec
        self.audio_codec = QComboBox()
        self.audio_codec.addItems(["AAC", "MP3", "FLAC", "Opus"])
        audio_layout.addWidget(QLabel("Codec:"), 0, 0)
        audio_layout.addWidget(self.audio_codec, 0, 1)
        
        # Audio bitrate
        self.audio_bitrate = QComboBox()
        self.audio_bitrate.addItems([
            "Original", "320k", "256k", "192k", "128k", "96k"
        ])
        audio_layout.addWidget(QLabel("Bitrate:"), 1, 0)
        audio_layout.addWidget(self.audio_bitrate, 1, 1)
        
        # Sample rate
        self.sample_rate = QComboBox()
        self.sample_rate.addItems([
            "Original", "48000 Hz", "44100 Hz", "32000 Hz", "22050 Hz"
        ])
        audio_layout.addWidget(QLabel("Sample Rate:"), 2, 0)
        audio_layout.addWidget(self.sample_rate, 2, 1)
        
        audio_group.setLayout(audio_layout)
        self.content_layout.addWidget(audio_group)
        
        # Additional options
        options_layout = QHBoxLayout()
        self.preserve_metadata = QCheckBox("Preserve metadata")
        self.preserve_metadata.setChecked(True)
        options_layout.addWidget(self.preserve_metadata)
        
        self.hardware_accel = QCheckBox("Use hardware acceleration")
        self.hardware_accel.setChecked(True)
        options_layout.addWidget(self.hardware_accel)
        
        options_layout.addStretch()
        self.content_layout.addLayout(options_layout)
        
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input File",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.srt *.ass *.vtt);;All Files (*.*)"
        )
        if file_path:
            self.file_path.setText(file_path)
            
    def get_values(self):
        """Get the dialog values as a dictionary."""
        return {
            'input_file': self.file_path.text(),
            'output_format': self.format_combo.currentText(),
            'video': {
                'codec': self.video_codec.currentText(),
                'quality': self.video_quality.value(),
                'resolution': self.resolution.currentText()
            },
            'audio': {
                'codec': self.audio_codec.currentText(),
                'bitrate': self.audio_bitrate.currentText(),
                'sample_rate': self.sample_rate.currentText()
            },
            'preserve_metadata': self.preserve_metadata.isChecked(),
            'hardware_acceleration': self.hardware_accel.isChecked()
        }
