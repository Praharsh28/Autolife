"""
Main application window implementation.
"""

import os
import sys
import traceback
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QTextEdit,
    QCheckBox, QSpinBox, QGroupBox, QStyle, QApplication
)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize
from .file_list_widget import FileListWidget
from .workers.subtitle_worker import SubtitleWorker
from .workers.srt_to_ass_worker import SrtToAssWorker
from .utilities import setup_logger
from .constants import *
from .sidebar_menu import SidebarMenu
from .dialogs.subtitle_dialog import SubtitleGenerationDialog

import logging

class MainWindow(QMainWindow):
    """
    Main application window with media processing functionality.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainWindow")
        
        try:
            # Initialize instance variables
            self.init_instance_variables()
            
            # Setup window properties
            self.setWindowTitle("AutoLife Media Tools")
            self.setMinimumSize(1000, 600)
            
            # Initialize UI
            self.init_ui()
            
            self.logger.info("MainWindow initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize MainWindow: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            QMessageBox.critical(None, "Initialization Error", error_msg)
            raise

    def init_instance_variables(self):
        """Initialize instance variables."""
        try:
            # Create file list widget
            self.file_list = FileListWidget()
            
            # Create progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setAlignment(Qt.AlignCenter)
            
            # Create status display
            self.status_display = QTextEdit()
            self.status_display.setReadOnly(True)
            self.status_display.setMaximumHeight(150)
            self.status_display.setFont(QFont("Consolas", 10))
            
            # Create processing options
            self.delete_original_checkbox = QCheckBox("Delete Original Files")
            self.batch_size_spinbox = QSpinBox()
            self.batch_size_spinbox.setRange(1, 10)
            self.batch_size_spinbox.setValue(3)
            
            # Create sidebar menu
            self.sidebar = SidebarMenu()
            
            # Initialize file progress tracking
            self.file_progress = {}
            
        except Exception as e:
            self.logger.error(f"Failed to initialize instance variables: {str(e)}")
            raise

    def init_ui(self):
        """Initialize the user interface."""
        try:
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create main layout
            main_layout = QHBoxLayout()
            central_widget.setLayout(main_layout)
            
            # Add sidebar menu
            main_layout.addWidget(self.sidebar)
            
            # Create right panel
            right_panel = QWidget()
            right_layout = QVBoxLayout()
            right_panel.setLayout(right_layout)
            
            # Add file list
            file_list_group = QGroupBox("Files")
            file_list_layout = QVBoxLayout()
            file_list_layout.addWidget(self.file_list)
            file_list_group.setLayout(file_list_layout)
            right_layout.addWidget(file_list_group)
            
            # Create button layout
            button_layout = QHBoxLayout()
            
            # Create and add buttons
            add_button = QPushButton("Add Files")
            add_button.clicked.connect(self.add_files)
            button_layout.addWidget(add_button)
            
            remove_button = QPushButton("Remove Selected")
            remove_button.clicked.connect(self.remove_selected_files)
            button_layout.addWidget(remove_button)
            
            # Add button layout to right panel
            right_layout.addLayout(button_layout)
            
            # Add processing options
            options_group = QGroupBox("Processing Options")
            options_layout = QHBoxLayout()
            options_layout.addWidget(self.delete_original_checkbox)
            options_layout.addWidget(QLabel("Batch Size:"))
            options_layout.addWidget(self.batch_size_spinbox)
            options_group.setLayout(options_layout)
            right_layout.addWidget(options_group)
            
            # Add progress bar
            progress_group = QGroupBox("Progress")
            progress_layout = QVBoxLayout()
            progress_layout.addWidget(self.progress_bar)
            progress_group.setLayout(progress_layout)
            right_layout.addWidget(progress_group)
            
            # Add status display
            status_group = QGroupBox("Status")
            status_layout = QVBoxLayout()
            status_layout.addWidget(self.status_display)
            status_group.setLayout(status_layout)
            right_layout.addWidget(status_group)
            
            # Add right panel to main layout
            main_layout.addWidget(right_panel)
            
            # Connect signals
            self.sidebar.tool_selected.connect(self.handle_tool_selection)
            
            # Load test files
            self.load_test_files()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {str(e)}")
            raise

    def load_test_files(self):
        """Load test files into the file list."""
        try:
            test_files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files')
            if os.path.exists(test_files_dir):
                test_files = [os.path.join(test_files_dir, f) for f in os.listdir(test_files_dir)]
                self.file_list.add_files(test_files)
                self.log_message(f"Loaded {len(test_files)} test files")
            else:
                self.logger.warning(f"Test files directory not found: {test_files_dir}")
                
        except Exception as e:
            self.logger.error(f"Failed to load test files: {str(e)}")
            self.handle_error(str(e))

    def handle_tool_selection(self, tool_name):
        """Handle tool selection from the sidebar menu."""
        try:
            self.logger.info(f"Tool selected: {tool_name}")
            
            # Map tool names to functions
            tool_map = {
                "Generate Subtitles": self.generate_subtitles,
                "Convert SRT to ASS": self.convert_srt_to_ass,
                "Overlay Subtitles": self.overlay_subtitles
            }
            
            # Execute the selected tool
            if tool_name in tool_map:
                tool_map[tool_name]()
            else:
                self.logger.warning(f"Unknown tool selected: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle tool selection: {str(e)}")

    def generate_subtitles(self):
        """Generate subtitles for selected files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select video files to generate subtitles.")
                return
            
            dialog = SubtitleGenerationDialog(self)
            if dialog.exec_():
                self.set_buttons_enabled(False)
                self.progress_bar.setValue(0)
                
                worker = SubtitleWorker(files, dialog.get_settings())
                worker.progress.connect(self.update_progress)
                worker.file_progress.connect(self.update_file_progress)
                worker.error.connect(self.handle_error)
                worker.finished.connect(self.process_completed)
                worker.start()
                
        except Exception as e:
            self.logger.error(f"Failed to generate subtitles: {str(e)}")
            self.handle_error(str(e))

    def convert_srt_to_ass(self):
        """Convert SRT files to ASS format."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select SRT files to convert.")
                return
            
            worker = SrtToAssWorker(files)
            worker.progress.connect(self.update_progress)
            worker.error.connect(self.handle_error)
            worker.finished.connect(self.process_completed)
            worker.start()
            
        except Exception as e:
            self.logger.error(f"Failed to convert SRT to ASS: {str(e)}")
            self.handle_error(str(e))

    def overlay_subtitles(self):
        """Overlay subtitles on video files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select video files.")
                return
            
            # Implementation for overlaying subtitles
            self.log_message("Overlaying subtitles...")
            
        except Exception as e:
            self.logger.error(f"Failed to overlay subtitles: {str(e)}")
            self.handle_error(str(e))

    def handle_error(self, error_message):
        """Handle errors during processing."""
        self.log_message(f"Error: {error_message}")
        self.set_buttons_enabled(True)
        QMessageBox.critical(self, "Error", str(error_message))

    def process_completed(self):
        """Handle completion of processing."""
        self.log_message("Processing completed successfully!")
        self.set_buttons_enabled(True)
        if self.delete_original_checkbox.isChecked():
            self.delete_original_files()

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def update_file_progress(self, filename, progress):
        """Update progress for a specific file."""
        self.file_progress[filename] = progress
        total_progress = sum(self.file_progress.values()) / len(self.file_progress)
        self.update_progress(int(total_progress))

    def add_files(self):
        """Open file dialog to add files."""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files",
                "",
                "All Files (*.*)"
            )
            if files:
                self.file_list.add_files(files)
                
        except Exception as e:
            self.logger.error(f"Failed to add files: {str(e)}")
            self.handle_error(str(e))

    def remove_selected_files(self):
        """Remove selected files from the list."""
        try:
            self.file_list.remove_selected_files()
            
        except Exception as e:
            self.logger.error(f"Failed to remove files: {str(e)}")
            self.handle_error(str(e))

    def log_message(self, message):
        """Add a message to the status display."""
        self.status_display.append(message)

    def set_buttons_enabled(self, enabled):
        """Enable or disable buttons."""
        for button in self.findChildren(QPushButton):
            button.setEnabled(enabled)

    def delete_original_files(self):
        """Delete original files after successful conversion."""
        try:
            files = self.file_list.get_all_files()
            for file in files:
                if os.path.exists(file):
                    os.remove(file)
            self.file_list.clear()
            self.log_message("Original files deleted.")
            
        except Exception as e:
            self.logger.error(f"Failed to delete original files: {str(e)}")
            self.handle_error(str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
