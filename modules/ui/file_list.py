from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QHBoxLayout, QMenu
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

import os

class FileListItem(QListWidgetItem):
    """Custom list widget item for media files."""
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.setText(self.file_name)
        self.setToolTip(file_path)
        
        # Status flags
        self.processed = False
        self.has_error = False
        self.translated = False
        
    def set_processed(self, processed: bool = True):
        """Mark file as processed."""
        self.processed = processed
        self.update_display()
        
    def set_error(self, has_error: bool = True):
        """Mark file as having an error."""
        self.has_error = has_error
        self.update_display()
        
    def set_translated(self, translated: bool = True):
        """Mark file as translated."""
        self.translated = translated
        self.update_display()
        
    def update_display(self):
        """Update item display based on status."""
        if self.has_error:
            self.setForeground(QColor("#FF0000"))
        elif self.processed:
            if self.translated:
                self.setForeground(QColor("#008000"))
            else:
                self.setForeground(QColor("#0000FF"))
        else:
            self.setForeground(QColor("#000000"))

class FileList(QWidget):
    """Widget for displaying and managing media files."""
    
    fileSelected = pyqtSignal(str)  # Emitted when a file is selected
    filesAdded = pyqtSignal()  # Emitted when files are added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Media Files")
        header_layout.addWidget(header_label)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_files)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # File list
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)
        
    def add_files(self, files: list):
        """Add files to the list."""
        for file_path in files:
            if os.path.isfile(file_path) and not self.file_exists(file_path):
                item = FileListItem(file_path)
                self.list_widget.addItem(item)
        self.filesAdded.emit()
        
    def file_exists(self, file_path: str) -> bool:
        """Check if file already exists in list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.file_path == file_path:
                return True
        return False
        
    def get_files(self) -> list:
        """Get list of all file paths."""
        return [self.list_widget.item(i).file_path 
                for i in range(self.list_widget.count())]
        
    def get_selected_file(self) -> str:
        """Get currently selected file path."""
        items = self.list_widget.selectedItems()
        return items[0].file_path if items else None
        
    def has_files(self) -> bool:
        """Check if list has any files."""
        return self.list_widget.count() > 0
        
    def count(self) -> int:
        """Get number of files in list."""
        return self.list_widget.count()
        
    def clear_files(self):
        """Clear all files from list."""
        self.list_widget.clear()
        self.filesAdded.emit()
        
    def on_selection_changed(self):
        """Handle file selection change."""
        selected = self.get_selected_file()
        if selected:
            self.fileSelected.emit(selected)
            
    def show_context_menu(self, position):
        """Show context menu for file item."""
        item = self.list_widget.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # Add menu actions
        remove_action = menu.addAction("Remove")
        remove_action.triggered.connect(lambda: self.remove_file(item))
        
        if item.processed:
            if item.translated:
                retranslate_action = menu.addAction("Retranslate")
                retranslate_action.triggered.connect(lambda: self.retranslate_file(item))
            else:
                translate_action = menu.addAction("Translate")
                translate_action.triggered.connect(lambda: self.translate_file(item))
                
        menu.exec_(self.list_widget.mapToGlobal(position))
        
    def remove_file(self, item: FileListItem):
        """Remove file from list."""
        self.list_widget.takeItem(self.list_widget.row(item))
        self.filesAdded.emit()
        
    def translate_file(self, item: FileListItem):
        """Request translation for file."""
        # This would be handled by connecting to appropriate signals
        pass
        
    def retranslate_file(self, item: FileListItem):
        """Request retranslation for file."""
        # This would be handled by connecting to appropriate signals
        pass
        
    def update_file_status(self, file_path: str, processed: bool = False,
                          has_error: bool = False, translated: bool = False):
        """Update status of a file in the list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.file_path == file_path:
                item.set_processed(processed)
                item.set_error(has_error)
                item.set_translated(translated)
                break
