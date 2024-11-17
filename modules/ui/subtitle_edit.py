from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QSpinBox, QTimeEdit,
    QGroupBox, QFormLayout, QDialogButtonBox,
    QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QTextCharFormat, QColor

class SubtitleEditDialog(QDialog):
    """Dialog for editing subtitle text and timing."""
    
    subtitleChanged = pyqtSignal(dict)  # Emitted when subtitle is changed
    
    def __init__(self, subtitle: dict, parent=None):
        super().__init__(parent)
        self.subtitle = subtitle.copy()  # Work on a copy
        self.setup_ui()
        self.load_subtitle()
        
    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Edit Subtitle")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Timing group
        timing_group = QGroupBox("Timing")
        timing_layout = QFormLayout()
        
        # Start time
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm:ss.zzz")
        timing_layout.addRow("Start Time:", self.start_time)
        
        # Duration
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(100, 10000)  # 0.1s to 10s
        self.duration_spin.setSingleStep(100)
        self.duration_spin.setSuffix(" ms")
        timing_layout.addRow("Duration:", self.duration_spin)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Text group
        text_group = QGroupBox("Text")
        text_layout = QVBoxLayout()
        
        # Original text (read-only)
        original_label = QLabel("Original:")
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setMaximumHeight(100)
        text_layout.addWidget(original_label)
        text_layout.addWidget(self.original_text)
        
        # Translated text
        translated_label = QLabel("Translation:")
        self.translated_text = QTextEdit()
        text_layout.addWidget(translated_label)
        text_layout.addWidget(self.translated_text)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # Formatting group
        format_group = QGroupBox("Formatting")
        format_layout = QHBoxLayout()
        
        # Font style
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Normal", "Bold", "Italic"])
        format_layout.addWidget(QLabel("Style:"))
        format_layout.addWidget(self.style_combo)
        
        # Color
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Yellow", "Green", "Cyan"])
        format_layout.addWidget(QLabel("Color:"))
        format_layout.addWidget(self.color_combo)
        
        # Position
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Bottom", "Top", "Middle"])
        format_layout.addWidget(QLabel("Position:"))
        format_layout.addWidget(self.position_combo)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout()
        
        self.spell_check = QCheckBox("Spell Check")
        self.auto_break = QCheckBox("Auto Line Break")
        self.sync_timing = QCheckBox("Sync with Original")
        
        options_layout.addWidget(self.spell_check)
        options_layout.addWidget(self.auto_break)
        options_layout.addWidget(self.sync_timing)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Preview button
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self.preview_changes)
        button_box.addButton(preview_btn, QDialogButtonBox.ActionRole)
        
        layout.addWidget(button_box)
        
    def load_subtitle(self):
        """Load subtitle data into UI."""
        # Set timing
        start_time = QTime.fromString(self.subtitle['start_time'], "HH:mm:ss.zzz")
        self.start_time.setTime(start_time)
        self.duration_spin.setValue(int(float(self.subtitle['duration']) * 1000))
        
        # Set text
        self.original_text.setText(self.subtitle.get('original_text', ''))
        self.translated_text.setText(self.subtitle['text'])
        
        # Set formatting
        style = self.subtitle.get('style', 'Normal')
        self.style_combo.setCurrentText(style)
        
        color = self.subtitle.get('color', 'White')
        self.color_combo.setCurrentText(color)
        
        position = self.subtitle.get('position', 'Bottom')
        self.position_combo.setCurrentText(position)
        
        # Set options
        self.spell_check.setChecked(self.subtitle.get('spell_check', True))
        self.auto_break.setChecked(self.subtitle.get('auto_break', True))
        self.sync_timing.setChecked(self.subtitle.get('sync_timing', True))
        
    def get_subtitle_data(self) -> dict:
        """Get updated subtitle data."""
        return {
            'start_time': self.start_time.time().toString("HH:mm:ss.zzz"),
            'duration': self.duration_spin.value() / 1000.0,
            'text': self.translated_text.toPlainText(),
            'style': self.style_combo.currentText(),
            'color': self.color_combo.currentText(),
            'position': self.position_combo.currentText(),
            'spell_check': self.spell_check.isChecked(),
            'auto_break': self.auto_break.isChecked(),
            'sync_timing': self.sync_timing.isChecked()
        }
        
    def accept(self):
        """Handle dialog acceptance."""
        updated_data = self.get_subtitle_data()
        self.subtitleChanged.emit(updated_data)
        super().accept()
        
    def preview_changes(self):
        """Preview subtitle changes."""
        # This would show a preview window with the video frame
        # and the updated subtitle overlay
        pass
        
    def apply_formatting(self):
        """Apply text formatting to preview."""
        format = QTextCharFormat()
        
        # Apply style
        style = self.style_combo.currentText()
        font = QFont()
        if style == "Bold":
            font.setBold(True)
        elif style == "Italic":
            font.setItalic(True)
        format.setFont(font)
        
        # Apply color
        color = self.color_combo.currentText()
        format.setForeground(QColor(color))
        
        self.translated_text.setCurrentCharFormat(format)
