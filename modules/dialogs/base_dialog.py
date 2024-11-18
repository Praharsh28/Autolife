from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt
import logging

class BaseDialog(QDialog):
    """Base dialog class for all tool dialogs."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Add description label if provided
        if hasattr(self, 'description'):
            desc_label = QLabel(self.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666;")
            self.layout.addWidget(desc_label)
            
            # Add separator
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #e0e0e0;")
            self.layout.addWidget(line)
        
        # Content area (to be filled by subclasses)
        self.content_layout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        self.layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QPushButton {
                padding: 6px 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
            QPushButton:pressed {
                background: #e0e0e0;
            }
            QPushButton[default="true"] {
                background: #2196F3;
                color: white;
                border: none;
            }
            QPushButton[default="true"]:hover {
                background: #1E88E5;
            }
            QPushButton[default="true"]:pressed {
                background: #1976D2;
            }
        """)
        
    def setup_ui(self):
        """Setup the dialog's UI. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement setup_ui()")
        
    def get_values(self):
        """Get the dialog's values. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_values()")
