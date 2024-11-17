from PyQt5.QtWidgets import (QTextEdit, QSpinBox, QLabel, QFileDialog,
                             QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
                             QGroupBox, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt5.QtCore import Qt
from .base_dialog import BaseDialog

class SubtitleEditDialog(BaseDialog):
    """Dialog for editing subtitle files."""
    
    description = """Edit subtitle files with advanced features like timing adjustment,
                    text formatting, and style customization."""
    
    def __init__(self, parent=None):
        super().__init__("Edit Subtitles", parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Input file selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select subtitle file...")
        self.file_path.setReadOnly(True)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(QLabel("Subtitle File:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        self.content_layout.addLayout(file_layout)
        
        # Subtitle table
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setColumnCount(4)
        self.subtitle_table.setHorizontalHeaderLabels([
            "Index", "Start Time", "End Time", "Text"
        ])
        header = self.subtitle_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        self.content_layout.addWidget(self.subtitle_table)
        
        # Timing adjustment group
        timing_group = QGroupBox("Timing Adjustment")
        timing_layout = QVBoxLayout()
        
        # Global shift
        shift_layout = QHBoxLayout()
        self.time_shift = QSpinBox()
        self.time_shift.setRange(-999999, 999999)
        self.time_shift.setSuffix(" ms")
        
        shift_layout.addWidget(QLabel("Shift all subtitles:"))
        shift_layout.addWidget(self.time_shift)
        shift_layout.addStretch()
        timing_layout.addLayout(shift_layout)
        
        # Sync points
        sync_layout = QHBoxLayout()
        self.sync_start = QLineEdit()
        self.sync_start.setPlaceholderText("00:00:00,000")
        self.sync_end = QLineEdit()
        self.sync_end.setPlaceholderText("00:00:00,000")
        
        sync_layout.addWidget(QLabel("Sync from:"))
        sync_layout.addWidget(self.sync_start)
        sync_layout.addWidget(QLabel("to:"))
        sync_layout.addWidget(self.sync_end)
        sync_layout.addStretch()
        timing_layout.addLayout(sync_layout)
        
        timing_group.setLayout(timing_layout)
        self.content_layout.addWidget(timing_group)
        
        # Style settings group
        style_group = QGroupBox("Style Settings")
        style_layout = QVBoxLayout()
        
        # Font settings
        font_layout = QHBoxLayout()
        self.font_family = QComboBox()
        self.font_family.addItems([
            "Arial", "Helvetica", "Times New Roman", "Courier New"
        ])
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(16)
        
        font_layout.addWidget(QLabel("Font:"))
        font_layout.addWidget(self.font_family)
        font_layout.addWidget(QLabel("Size:"))
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()
        style_layout.addLayout(font_layout)
        
        # Color settings
        color_layout = QHBoxLayout()
        self.primary_color = QComboBox()
        self.primary_color.addItems([
            "White", "Yellow", "Green", "Cyan", "Blue", "Magenta", "Red"
        ])
        
        self.outline_color = QComboBox()
        self.outline_color.addItems([
            "Black", "Gray", "White", "Yellow", "Blue", "Red"
        ])
        
        color_layout.addWidget(QLabel("Text Color:"))
        color_layout.addWidget(self.primary_color)
        color_layout.addWidget(QLabel("Outline:"))
        color_layout.addWidget(self.outline_color)
        color_layout.addStretch()
        style_layout.addLayout(color_layout)
        
        style_group.setLayout(style_layout)
        self.content_layout.addWidget(style_group)
        
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Subtitle File",
            "",
            "Subtitle Files (*.srt *.ass *.vtt *.ssa);;All Files (*.*)"
        )
        if file_path:
            self.file_path.setText(file_path)
            # TODO: Load subtitle file content into table
            
    def get_values(self):
        """Get the dialog values as a dictionary."""
        return {
            'subtitle_file': self.file_path.text(),
            'timing': {
                'global_shift': self.time_shift.value(),
                'sync_start': self.sync_start.text(),
                'sync_end': self.sync_end.text()
            },
            'style': {
                'font_family': self.font_family.currentText(),
                'font_size': self.font_size.value(),
                'text_color': self.primary_color.currentText(),
                'outline_color': self.outline_color.currentText()
            }
        }
