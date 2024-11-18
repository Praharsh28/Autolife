from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import logging

class MenuCategory(QFrame):
    """A category in the sidebar menu."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 8)
        
        # Category title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #666;")
        
        self.layout.addWidget(title_label)

class MenuButton(QPushButton):
    """A button in the sidebar menu."""
    def __init__(self, text, description="", parent=None):
        super().__init__(text, parent)
        self.setToolTip(description)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background: transparent;
                color: #333;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background: rgba(0, 0, 0, 0.1);
            }
        """)

class SidebarMenu(QWidget):
    """A modern sidebar menu widget."""
    tool_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        # Set fixed width for sidebar
        self.setFixedWidth(250)
        self.setStyleSheet("""
            SidebarMenu {
                background: white;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 16, 12, 16)
        
        # Scroll area for categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        
        # Container for categories
        container = QWidget()
        self.categories_layout = QVBoxLayout(container)
        self.categories_layout.setSpacing(16)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(container)
        
        # Add categories
        self.add_frequently_used()
        self.add_subtitle_tools()
        self.add_conversion_tools()
        self.add_additional_tools()
        
        # Add scroll area to main layout
        layout.addWidget(scroll)
        
    def add_category(self, title):
        """Add a new category to the sidebar."""
        category = MenuCategory(title)
        self.categories_layout.addWidget(category)
        return category
        
    def add_tool_button(self, category, text, description=""):
        """Add a tool button to a category."""
        button = MenuButton(text, description)
        button.clicked.connect(lambda: self.tool_selected.emit(text))
        category.layout.addWidget(button)
        return button
        
    def add_frequently_used(self):
        """Add frequently used tools category."""
        category = self.add_category("📌 Frequently Used")
        self.add_tool_button(category, "Generate Subtitles", 
                           "Generate subtitles from video/audio files")
        self.add_tool_button(category, "Convert SRT to ASS", 
                           "Convert SRT subtitle files to ASS format")
        self.add_tool_button(category, "Extract Audio", 
                           "Extract audio from video files")
        
    def add_subtitle_tools(self):
        """Add subtitle tools category."""
        category = self.add_category("🗣️ Subtitle Tools")
        self.add_tool_button(category, "Edit Subtitles", 
                           "Edit and modify subtitle files")
        self.add_tool_button(category, "Merge Subtitles", 
                           "Merge multiple subtitle files")
        self.add_tool_button(category, "Split Subtitles", 
                           "Split subtitle files")
        self.add_tool_button(category, "Sync Subtitles", 
                           "Synchronize subtitles with video")
        
    def add_conversion_tools(self):
        """Add format conversion tools category."""
        category = self.add_category("🔄 Format Conversion")
        self.add_tool_button(category, "Video Converter", 
                           "Convert between video formats")
        self.add_tool_button(category, "Audio Converter", 
                           "Convert between audio formats")
        self.add_tool_button(category, "Subtitle Converter", 
                           "Convert between subtitle formats")
        
    def add_additional_tools(self):
        """Add additional tools category."""
        category = self.add_category("🛠️ Additional Tools")
        self.add_tool_button(category, "MXF ↔ MPF", 
                           "Convert between MXF and MPF formats")
        self.add_tool_button(category, "Batch Processing", 
                           "Process multiple files in batch")
        self.add_tool_button(category, "Custom Templates", 
                           "Manage custom templates")
