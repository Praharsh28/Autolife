"""
Custom QListWidget for handling file lists with drag and drop support.
"""

from PyQt5.QtWidgets import QListWidget, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
import os

class FileListWidget(QListWidget):
    """
    Custom QListWidget that supports drag and drop file operations.
    """
    files_dropped = pyqtSignal(list)  # Signal emitted when files are dropped

    # Supported video formats
    VIDEO_FORMATS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mxf'}
    
    # Supported audio formats
    AUDIO_FORMATS = {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg', '.wma', '.aiff'}
    
    def __init__(self, parent=None):
        """Initialize the FileListWidget."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #4b6eaf;
            }
            QListWidget::item:hover {
                background-color: #363636;
            }
        """)

    def dragEnterEvent(self, event):
        """Handle drag enter events for files."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move events for files."""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Handle drop events for files.
        Validates file types and adds them to the list.
        """
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            dropped_files = []
            invalid_files = []
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._is_valid_media_file(file_path):
                    dropped_files.append(file_path)
                    if not self._is_duplicate(file_path):
                        self.addItem(file_path)
                else:
                    invalid_files.append(file_path)
            
            if invalid_files:
                QMessageBox.warning(
                    self,
                    "Invalid Files",
                    f"The following files are not supported:\n\n"
                    f"{chr(10).join(os.path.basename(f) for f in invalid_files)}\n\n"
                    f"Supported formats:\n"
                    f"Video: {', '.join(self.VIDEO_FORMATS)}\n"
                    f"Audio: {', '.join(self.AUDIO_FORMATS)}"
                )
            
            if dropped_files:
                self.files_dropped.emit(dropped_files)
        else:
            event.ignore()

    def _is_valid_media_file(self, file_path):
        """
        Check if the file is a supported media file.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if file is supported, False otherwise
        """
        ext = os.path.splitext(file_path.lower())[1]
        return ext in self.VIDEO_FORMATS or ext in self.AUDIO_FORMATS

    def _is_duplicate(self, file_path):
        """
        Check if the file is already in the list.
        
        Args:
            file_path (str): Path to check for duplicates
            
        Returns:
            bool: True if file is already in list, False otherwise
        """
        for i in range(self.count()):
            if self.item(i).text() == file_path:
                return True
        return False

    def get_selected_files(self):
        """
        Get list of selected file paths.
        
        Returns:
            list: List of selected file paths
        """
        return [item.text() for item in self.selectedItems()]

    def get_all_files(self):
        """
        Get list of all file paths in the widget.
        
        Returns:
            list: List of all file paths
        """
        return [self.item(i).text() for i in range(self.count())]

    def remove_selected_files(self):
        """Remove selected files from the list."""
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def add_file(self, filepath):
        """
        Add a file to the list.
        
        Args:
            filepath (str): Path to file to add
        """
        if not self._is_duplicate(filepath):
            self.addItem(filepath)
            
    def add_files(self, files):
        """
        Add multiple files to the list.
        
        Args:
            files: List of file paths to add
        """
        for file in files:
            if os.path.isfile(file):
                ext = os.path.splitext(file)[1].lower()
                if ext in self.VIDEO_FORMATS or ext in self.AUDIO_FORMATS:
                    self.addItem(file)
                    
    def remove_file(self, filepath):
        """
        Remove a specific file from the list.
        
        Args:
            filepath (str): Path to file to remove
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                self.takeItem(i)
                break
    
    def clear(self):
        """Clear all files from the list."""
        super().clear()
    
    def select_file(self, filepath):
        """
        Select a specific file in the list.
        
        Args:
            filepath (str): Path to file to select
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                self.item(i).setSelected(True)
                break
    
    def is_selected(self, filepath):
        """
        Check if a specific file is selected.
        
        Args:
            filepath (str): Path to file to check
            
        Returns:
            bool: True if file is selected, False otherwise
        """
        for item in self.selectedItems():
            if item.text() == filepath:
                return True
        return False
    
    def filter_by_extension(self, extension):
        """
        Get list of files with specific extension.
        
        Args:
            extension (str): File extension to filter by
            
        Returns:
            list: List of file paths with given extension
        """
        return [self.item(i).text() for i in range(self.count())
                if self.item(i).text().endswith(extension)]
    
    def update_file_status(self, filepath, status):
        """
        Update the status of a file.
        
        Args:
            filepath (str): Path to file to update
            status (str): New status
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                self.item(i).setData(Qt.UserRole, status)
                break
    
    def get_file_status(self, filepath):
        """
        Get the status of a file.
        
        Args:
            filepath (str): Path to file to check
            
        Returns:
            str: File status or None if not set
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                return self.item(i).data(Qt.UserRole)
        return None
    
    def clear_file_status(self, filepath):
        """
        Clear the status of a file.
        
        Args:
            filepath (str): Path to file to clear status for
        """
        self.update_file_status(filepath, None)
    
    def update_file_progress(self, filepath, progress):
        """
        Update the progress of a file.
        
        Args:
            filepath (str): Path to file to update
            progress (int): Progress value (0-100)
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                self.item(i).setData(Qt.UserRole + 1, progress)
                break
    
    def get_file_progress(self, filepath):
        """
        Get the progress of a file.
        
        Args:
            filepath (str): Path to file to check
            
        Returns:
            int: Progress value (0-100) or 0 if not set
        """
        for i in range(self.count()):
            if self.item(i).text() == filepath:
                progress = self.item(i).data(Qt.UserRole + 1)
                return progress if progress is not None else 0
        return 0
    
    def clear_file_progress(self, filepath):
        """
        Clear the progress of a file.
        
        Args:
            filepath (str): Path to file to clear progress for
        """
        self.update_file_progress(filepath, 0)
