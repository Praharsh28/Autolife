from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QScrollArea,
                             QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import logging

class ToolButton(QPushButton):
    def __init__(self, name, description, parent=None):
        super().__init__(name, parent)
        self.setToolTip(description)
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

class ToolCategory(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        
        # Category title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        
        layout.addWidget(title_label)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                margin: 5px;
            }
        """)

class ToolsWindow(QMainWindow):
    tool_selected = pyqtSignal(str)  # Signal emitted when a tool is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Media Processing Tools")
        self.setMinimumSize(400, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for categories
        container = QWidget()
        self.categories_layout = QVBoxLayout(container)
        self.categories_layout.setSpacing(15)
        scroll.setWidget(container)
        
        # Add categories
        self.add_frequently_used_tools()
        self.add_subtitle_tools()
        self.add_conversion_tools()
        self.add_additional_tools()

        main_layout.addWidget(scroll)

    def add_frequently_used_tools(self):
        category = ToolCategory("📌 Frequently Used")
        layout = category.layout()
        
        # Add frequently used tools
        tools = [
            ("Generate Subtitles", "Generate subtitles from video/audio files"),
            ("Convert SRT to ASS", "Convert SRT subtitle files to ASS format"),
            ("Extract Audio", "Extract audio from video files"),
        ]
        
        for name, desc in tools:
            btn = ToolButton(name, desc)
            btn.clicked.connect(lambda checked, n=name: self.tool_selected.emit(n))
            layout.addWidget(btn)
            
        self.categories_layout.addWidget(category)

    def add_subtitle_tools(self):
        category = ToolCategory("🗣️ Subtitle Tools")
        layout = category.layout()
        
        tools = [
            ("Edit Subtitles", "Edit and modify subtitle files"),
            ("Merge Subtitles", "Merge multiple subtitle files"),
            ("Split Subtitles", "Split subtitle files"),
            ("Sync Subtitles", "Synchronize subtitles with video"),
        ]
        
        for name, desc in tools:
            btn = ToolButton(name, desc)
            btn.clicked.connect(lambda checked, n=name: self.tool_selected.emit(n))
            layout.addWidget(btn)
            
        self.categories_layout.addWidget(category)

    def add_conversion_tools(self):
        category = ToolCategory("🔄 Format Conversion")
        layout = category.layout()
        
        tools = [
            ("Video Format Converter", "Convert between video formats"),
            ("Audio Format Converter", "Convert between audio formats"),
            ("Subtitle Format Converter", "Convert between subtitle formats"),
        ]
        
        for name, desc in tools:
            btn = ToolButton(name, desc)
            btn.clicked.connect(lambda checked, n=name: self.tool_selected.emit(n))
            layout.addWidget(btn)
            
        self.categories_layout.addWidget(category)

    def add_additional_tools(self):
        category = ToolCategory("🛠️ Additional Tools")
        layout = category.layout()
        
        tools = [
            ("MXF to MPF Converter", "Convert MXF files to MPF format"),
            ("MPF to MXF Converter", "Convert MPF files to MXF format"),
            ("Batch Processing", "Process multiple files in batch"),
            ("Custom Templates", "Manage custom templates"),
        ]
        
        for name, desc in tools:
            btn = ToolButton(name, desc)
            btn.clicked.connect(lambda checked, n=name: self.tool_selected.emit(n))
            layout.addWidget(btn)
            
        self.categories_layout.addWidget(category)
