"""
Widget for managing file lists with multi-selection support.
"""

from PyQt5.QtWidgets import QListWidget, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt
import os
import logging

class FileListWidget(QListWidget):
    """Widget for displaying and managing file lists."""
    
    # Supported file formats
    VIDEO_FORMATS = {'.mp4', '.avi', '.mkv', '.mov', '.mxf', '.mpg', '.mpeg', '.wmv'}
    AUDIO_FORMATS = {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg'}
    SUBTITLE_FORMATS = {'.srt', '.ass', '.ssa', '.vtt'}
    
    def __init__(self):
        """Initialize the file list widget."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Enable multi-selection
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        
    def add_files(self, files):
        """
        Add files to the list.
        
        Args:
            files: List of file paths to add
        """
        try:
            added_count = 0
            for file in files:
                if os.path.exists(file):
                    # Check if file is already in list
                    items = self.findItems(file, Qt.MatchExactly)
                    if not items:
                        # Check if file extension is supported
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.VIDEO_FORMATS or ext in self.AUDIO_FORMATS or ext in self.SUBTITLE_FORMATS:
                            # Add file with just the filename for display
                            display_name = os.path.basename(file)
                            item = self.addItem(display_name)
                            # Store full path as item data
                            self.item(self.count() - 1).setData(Qt.UserRole, file)
                            added_count += 1
                            self.logger.debug(f"Added file to list: {file}")
                        else:
                            self.logger.warning(f"Unsupported file format: {file}")
                else:
                    self.logger.warning(f"File does not exist: {file}")
            
            if added_count > 0:
                self.logger.info(f"Successfully added {added_count} files")
            
        except Exception as e:
            self.logger.error(f"Failed to add files: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to add files: {str(e)}")

    def get_selected_files(self):
        """
        Get the full paths of selected files.
        
        Returns:
            list: List of selected file paths
        """
        try:
            selected_items = self.selectedItems()
            return [item.data(Qt.UserRole) for item in selected_items]
        except Exception as e:
            self.logger.error(f"Failed to get selected files: {str(e)}")
            return []

    def get_all_files(self):
        """
        Get the full paths of all files in the list.
        
        Returns:
            list: List of all file paths
        """
        try:
            return [self.item(i).data(Qt.UserRole) for i in range(self.count())]
        except Exception as e:
            self.logger.error(f"Failed to get all files: {str(e)}")
            return []

    def remove_selected(self):
        """Remove selected files from the list."""
        try:
            items = self.selectedItems()
            if not items:
                return
                
            for item in items:
                self.takeItem(self.row(item))
                self.logger.debug(f"Removed file from list: {item.text()}")
                
            self.logger.info(f"Removed {len(items)} file(s) from the list")
            
        except Exception as e:
            self.logger.error(f"Failed to remove files: {str(e)}")
            QMessageBox.critical(None, "Error", f"Failed to remove files: {str(e)}")
    
    def clear_list(self):
        """Clear all files from the list."""
        try:
            count = self.count()
            self.clear()
            self.logger.info(f"Cleared {count} file(s) from the list")
            
        except Exception as e:
            self.logger.error(f"Failed to clear list: {str(e)}")
            QMessageBox.critical(None, "Error", f"Failed to clear list: {str(e)}")
