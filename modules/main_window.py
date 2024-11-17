"""
Main application window implementation.
"""

import os
import sys
import traceback
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget,
    QFileDialog, QLabel, QMessageBox, QHBoxLayout, QProgressBar,
    QInputDialog, QSpinBox, QCheckBox, QGroupBox, QStyle, QApplication
)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets

from .file_list_widget import FileListWidget
from .workers.subtitle_worker import SubtitleWorker
from .workers.srt_to_ass_worker import SrtToAssWorker
from .utilities import setup_logger
from .constants import WINDOW_TITLE, WINDOW_GEOMETRY, DARK_THEME, TEST_FILES_DIR

class MainWindow(QMainWindow):
    """
    Main application window with media processing functionality.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        try:
            # Setup logger first
            self.logger = setup_logger('MainWindow')
            self.logger.info("Initializing MainWindow")
            
            # Initialize instance variables
            self.init_instance_variables()
            
            # Setup window properties
            self.setWindowTitle(WINDOW_TITLE)
            self.setGeometry(*WINDOW_GEOMETRY)
            
            # Initialize UI
            self.initUI()
            
            # Apply theme and connect signals
            self.apply_dark_theme()
            self.setup_connections()
            
            # Load test files if they exist
            self.load_test_files()
            
            self.logger.info("MainWindow initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize MainWindow: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            QMessageBox.critical(None, "Initialization Error", error_msg)
            raise

    def init_instance_variables(self):
        """Initialize instance variables."""
        try:
            self.button_convert_audio = QPushButton("Generate Subtitles")
            self.button_srt_to_ass = QPushButton("Convert SRT to ASS")
            self.button_mxf_to_mp4 = QPushButton("Convert MXF to MP4")
            self.button_overlay_subtitles = QPushButton("Overlay Subtitles")
            self.button_mp4_to_mxf = QPushButton("Convert MP4 to MXF")
            self.progress_bar = QProgressBar()
            self.status_display = QTextEdit()
            self.batch_size_spinner = QSpinBox()
            self.delete_original_checkbox = QCheckBox("Delete original files after conversion")
            self.file_progress = {}
            self.file_list = FileListWidget()
        except Exception as e:
            raise Exception(f"Failed to initialize instance variables: {str(e)}")

    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        try:
            app = QApplication.instance()
            if app is None:
                raise Exception("QApplication instance not found")
            
            app.setStyle("Fusion")
            
            # Create and configure palette
            palette = QPalette()
            
            # Set colors for various UI elements
            palette.setColor(QPalette.Window, QColor(DARK_THEME['background']))
            palette.setColor(QPalette.WindowText, QColor(DARK_THEME['text']))
            palette.setColor(QPalette.Base, QColor(DARK_THEME['list_background']))
            palette.setColor(QPalette.AlternateBase, QColor(DARK_THEME['list_alternate']))
            palette.setColor(QPalette.ToolTipBase, QColor(DARK_THEME['background']))
            palette.setColor(QPalette.ToolTipText, QColor(DARK_THEME['text']))
            palette.setColor(QPalette.Text, QColor(DARK_THEME['text']))
            palette.setColor(QPalette.Button, QColor(DARK_THEME['button']))
            palette.setColor(QPalette.ButtonText, QColor(DARK_THEME['button_text']))
            palette.setColor(QPalette.BrightText, QColor(DARK_THEME['error']))
            palette.setColor(QPalette.Link, QColor(DARK_THEME['highlight']))
            palette.setColor(QPalette.Highlight, QColor(DARK_THEME['highlight']))
            palette.setColor(QPalette.HighlightedText, QColor(DARK_THEME['highlight_text']))
            
            app.setPalette(palette)
            
            # Style specific widgets
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {DARK_THEME['background']};
                }}
                QPushButton {{
                    background-color: {DARK_THEME['button']};
                    color: {DARK_THEME['button_text']};
                    border: 1px solid {DARK_THEME['border']};
                    padding: 5px;
                    border-radius: 3px;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {DARK_THEME['button_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {DARK_THEME['highlight']};
                }}
                QProgressBar {{
                    border: 1px solid {DARK_THEME['border']};
                    border-radius: 3px;
                    text-align: center;
                    color: {DARK_THEME['highlight_text']};
                }}
                QProgressBar::chunk {{
                    background-color: {DARK_THEME['progress_bar']};
                }}
                QGroupBox {{
                    background-color: {DARK_THEME['group_box']};
                    border: 1px solid {DARK_THEME['border']};
                    border-radius: 3px;
                    margin-top: 0.5em;
                    padding-top: 0.5em;
                    color: {DARK_THEME['group_box_title']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }}
                QTextEdit {{
                    background-color: {DARK_THEME['status_background']};
                    color: {DARK_THEME['status_text']};
                    border: 1px solid {DARK_THEME['border']};
                    border-radius: 3px;
                }}
                QSpinBox {{
                    background-color: {DARK_THEME['list_background']};
                    color: {DARK_THEME['text']};
                    border: 1px solid {DARK_THEME['border']};
                    border-radius: 3px;
                    padding: 2px;
                }}
                QCheckBox {{
                    color: {DARK_THEME['text']};
                }}
                QCheckBox::indicator {{
                    width: 13px;
                    height: 13px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 1px solid {DARK_THEME['border']};
                    background-color: {DARK_THEME['button']};
                }}
                QCheckBox::indicator:checked {{
                    border: 1px solid {DARK_THEME['highlight']};
                    background-color: {DARK_THEME['highlight']};
                }}
                QLabel {{
                    color: {DARK_THEME['text']};
                }}
            """)
            
        except Exception as e:
            raise Exception(f"Failed to apply dark theme: {str(e)}")

    def setup_connections(self):
        """Setup signal connections for buttons and workers."""
        try:
            # Connect buttons to their respective functions
            self.button_convert_audio.clicked.connect(self.generate_subtitles)
            self.button_srt_to_ass.clicked.connect(self.convert_srt_to_ass)
            self.button_mxf_to_mp4.clicked.connect(self.convert_mxf_to_mp4)
            self.button_mp4_to_mxf.clicked.connect(self.convert_mp4_to_mxf)
            self.button_overlay_subtitles.clicked.connect(self.overlay_subtitles)
            
            self.logger.info("Button connections setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup connections: {str(e)}", exc_info=True)
            raise

    def initUI(self):
        """Initialize the user interface."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create file management section
        file_management = QGroupBox("File Management")
        file_layout = QVBoxLayout()
        
        # Add file list
        file_layout.addWidget(self.file_list)
        
        # Add file management buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Files")
        remove_button = QPushButton("Remove Selected")
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        file_layout.addLayout(button_layout)
        
        file_management.setLayout(file_layout)
        layout.addWidget(file_management)

        # Create processing options section
        processing = QGroupBox("Processing Options")
        processing_layout = QVBoxLayout()
        
        # Add batch size control
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size_spinner.setRange(1, 10)
        self.batch_size_spinner.setValue(3)
        batch_layout.addWidget(self.batch_size_spinner)
        processing_layout.addLayout(batch_layout)
        
        # Add processing buttons
        processing_layout.addWidget(self.button_convert_audio)
        processing_layout.addWidget(self.button_srt_to_ass)
        processing_layout.addWidget(self.button_mxf_to_mp4)
        processing_layout.addWidget(self.button_overlay_subtitles)
        processing_layout.addWidget(self.button_mp4_to_mxf)
        
        # Add delete original checkbox
        processing_layout.addWidget(self.delete_original_checkbox)
        
        processing.setLayout(processing_layout)
        layout.addWidget(processing)

        # Add progress section
        progress = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_display)
        progress.setLayout(progress_layout)
        layout.addWidget(progress)

        # Connect signals
        add_button.clicked.connect(self.add_files)
        remove_button.clicked.connect(self.remove_selected_files)

        # Configure status display
        self.status_display.setReadOnly(True)
        self.status_display.setFont(QFont("Consolas", 10))

    def generate_subtitles(self):
        """Generate subtitles for selected files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to process.")
                return

            self.logger.info(f"Starting subtitle generation for {len(files)} files")
            self.status_display.append(f"Starting subtitle generation for {len(files)} files...")
            
            # Create and setup worker
            self.subtitle_worker = SubtitleWorker(
                files, 
                self.batch_size_spinner.value()
            )
            
            # Connect worker signals
            self.subtitle_worker.signals.progress.connect(self.update_progress)
            self.subtitle_worker.signals.file_completed.connect(self.update_file_progress)
            self.subtitle_worker.signals.error.connect(self.handle_error)
            self.subtitle_worker.signals.log.connect(self.log_message)
            self.subtitle_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.subtitle_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start subtitle generation: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def convert_srt_to_ass(self):
        """Start SRT to ASS conversion process."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to process.")
                return

            # Get ASS template file
            template_file, _ = QFileDialog.getOpenFileName(
                self, "Select ASS Template", "", "ASS Files (*.ass)"
            )
            if not template_file:
                return

            # Read available styles and let user choose
            styles = self.read_ass_styles(template_file)
            if not styles:
                QMessageBox.warning(self, "No Styles", "No styles found in template file.")
                return

            style_name = self.get_style_choice(styles)
            if not style_name:
                return

            self.logger.info(f"Starting SRT to ASS conversion for {len(files)} files")
            self.status_display.append(f"Starting SRT to ASS conversion for {len(files)} files...")
            
            # Create and setup worker
            self.srt_to_ass_worker = SrtToAssWorker(
                files, 
                template_file, 
                style_name
            )
            
            # Connect worker signals
            self.srt_to_ass_worker.signals.progress.connect(self.update_progress)
            self.srt_to_ass_worker.signals.file_completed.connect(self.update_file_progress)
            self.srt_to_ass_worker.signals.error.connect(self.handle_error)
            self.srt_to_ass_worker.signals.log.connect(self.log_message)
            self.srt_to_ass_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.srt_to_ass_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start SRT to ASS conversion: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def convert_mxf_to_mp4(self):
        """Convert MXF files to MP4 format."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to process.")
                return

            self.logger.info(f"Starting MXF to MP4 conversion for {len(files)} files")
            self.status_display.append(f"Starting MXF to MP4 conversion for {len(files)} files...")
            
            # Create and setup worker
            self.mxf_to_mp4_worker = SubtitleWorker(
                files, 
                self.batch_size_spinner.value()
            )
            
            # Connect worker signals
            self.mxf_to_mp4_worker.signals.progress.connect(self.update_progress)
            self.mxf_to_mp4_worker.signals.file_completed.connect(self.update_file_progress)
            self.mxf_to_mp4_worker.signals.error.connect(self.handle_error)
            self.mxf_to_mp4_worker.signals.log.connect(self.log_message)
            self.mxf_to_mp4_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.mxf_to_mp4_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start MXF to MP4 conversion: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def convert_mp4_to_mxf(self):
        """Convert MP4 files to MXF format."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to process.")
                return

            self.logger.info(f"Starting MP4 to MXF conversion for {len(files)} files")
            self.status_display.append(f"Starting MP4 to MXF conversion for {len(files)} files...")
            
            # Create and setup worker
            self.mp4_to_mxf_worker = SubtitleWorker(
                files, 
                self.batch_size_spinner.value()
            )
            
            # Connect worker signals
            self.mp4_to_mxf_worker.signals.progress.connect(self.update_progress)
            self.mp4_to_mxf_worker.signals.file_completed.connect(self.update_file_progress)
            self.mp4_to_mxf_worker.signals.error.connect(self.handle_error)
            self.mp4_to_mxf_worker.signals.log.connect(self.log_message)
            self.mp4_to_mxf_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.mp4_to_mxf_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start MP4 to MXF conversion: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def overlay_subtitles(self):
        """Overlay subtitles on video files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to process.")
                return

            self.logger.info(f"Starting subtitle overlay for {len(files)} files")
            self.status_display.append(f"Starting subtitle overlay for {len(files)} files...")
            
            # Create and setup worker
            self.overlay_worker = SubtitleWorker(
                files, 
                self.batch_size_spinner.value()
            )
            
            # Connect worker signals
            self.overlay_worker.signals.progress.connect(self.update_progress)
            self.overlay_worker.signals.file_completed.connect(self.update_file_progress)
            self.overlay_worker.signals.error.connect(self.handle_error)
            self.overlay_worker.signals.log.connect(self.log_message)
            self.overlay_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.overlay_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start subtitle overlay: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def handle_error(self, error_message):
        """Handle errors during processing."""
        try:
            # Format error message for display
            formatted_error = f"Error: {error_message}"
            if isinstance(error_message, dict):
                if 'error' in error_message:
                    formatted_error = f"Error: {error_message['error']}"
                if 'file' in error_message:
                    formatted_error = f"Error processing {error_message['file']}: {error_message['error']}"
            
            # Log error with full context
            self.logger.error(formatted_error, exc_info=True)
            
            # Show error dialog
            QMessageBox.critical(self, "Processing Error", formatted_error)
            
            # Update status display
            self.status_display.append(formatted_error)
            
            # Re-enable buttons
            self.set_buttons_enabled(True)
            
            # Reset progress
            self.progress_bar.setValue(0)
            
        except Exception as e:
            self.logger.error(f"Error in error handler: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Critical Error", 
                               f"Error handling failed: {str(e)}")

    def process_completed(self):
        """Handle completion of processing."""
        try:
            self.logger.info("Processing completed successfully")
            
            # Update UI
            self.status_display.append("Processing completed successfully")
            self.progress_bar.setValue(100)
            
            # Re-enable buttons
            self.set_buttons_enabled(True)
            
            # Reset progress tracking
            self.file_progress.clear()
            
            # Handle file cleanup if requested
            if self.delete_original_checkbox.isChecked():
                self.delete_original_files()
                
        except Exception as e:
            self.logger.error(f"Error in completion handler: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def update_progress(self, value):
        """Update the progress bar."""
        try:
            # Ensure value is within valid range
            value = max(0, min(100, value))
            
            # Update progress bar
            self.progress_bar.setValue(int(value))
            
            # Update status for significant progress points
            if value in [25, 50, 75, 100]:
                self.status_display.append(f"Progress: {value}%")
                
        except Exception as e:
            self.logger.error(f"Error updating progress: {str(e)}", exc_info=True)

    def update_file_progress(self, filename, progress):
        """Update progress for a specific file."""
        try:
            # Update progress for specific file
            self.file_progress[filename] = max(0, min(100, progress))
            
            # Calculate and update total progress
            if self.file_progress:
                total_progress = sum(self.file_progress.values()) / len(self.file_progress)
                self.progress_bar.setValue(int(total_progress))
                
                # Log progress for debugging
                self.logger.debug(f"File progress - {filename}: {progress}%, Total: {total_progress}%")
            
        except Exception as e:
            self.logger.error(f"Error updating file progress: {str(e)}", exc_info=True)

    def add_files(self):
        """Open file dialog to add files."""
        try:
            # Default to test_files directory if it exists
            default_dir = TEST_FILES_DIR if os.path.exists(TEST_FILES_DIR) else os.path.expanduser("~")

            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Add Files",
                default_dir,
                "All Supported Files (*.mp4 *.mxf *.srt *.ass);;Video Files (*.mp4 *.mxf);;Subtitle Files (*.srt *.ass);;All Files (*.*)"
            )
            for file in files:
                self.file_list.addItem(file)

        except Exception as e:
            error_msg = f"Error opening files: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def remove_selected_files(self):
        """Remove selected files from the list."""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def log_message(self, message):
        """Add a message to the status display."""
        self.status_display.append(message)
        self.logger.info(message)

    def set_buttons_enabled(self, enabled):
        """Enable or disable buttons."""
        self.button_convert_audio.setEnabled(enabled)
        self.button_srt_to_ass.setEnabled(enabled)
        self.button_mxf_to_mp4.setEnabled(enabled)
        self.button_mp4_to_mxf.setEnabled(enabled)
        self.button_overlay_subtitles.setEnabled(enabled)

    def get_style_choice(self, styles):
        """Prompt the user to select a style."""
        style_name, ok = QInputDialog.getItem(
            self, "Select Style", "Choose a style:", styles, 0, False
        )
        return style_name if ok else None

    def read_ass_styles(self, ass_template_path):
        """Read styles from ASS template file."""
        try:
            with open(ass_template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            styles = []
            in_styles_section = False
            
            for line in content.split('\n'):
                if '[V4+ Styles]' in line:
                    in_styles_section = True
                    continue
                elif in_styles_section and line.startswith('['):
                    break
                elif in_styles_section and line.startswith('Style:'):
                    style_name = line.split(',')[0].replace('Style:', '').strip()
                    styles.append(style_name)
            
            return styles
            
        except Exception as e:
            self.logger.error(f"Error reading ASS template: {str(e)}")
            return []

    def delete_original_files(self):
        """Delete original files after successful conversion."""
        files = self.file_list.get_selected_files()
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    self.log_message(f"Deleted original file: {file}")
            except Exception as e:
                self.logger.error(f"Error deleting {file}: {str(e)}")
                continue

    def load_test_files(self):
        """Load files from test directory if they exist."""
        try:
            if os.path.exists(TEST_FILES_DIR):
                test_files = []
                for file in os.listdir(TEST_FILES_DIR):
                    file_path = os.path.join(TEST_FILES_DIR, file)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.file_list.VIDEO_FORMATS or ext in self.file_list.AUDIO_FORMATS:
                            test_files.append(file_path)
                
                if test_files:
                    self.file_list.add_files(test_files)
                    self.log_message(f"Loaded {len(test_files)} test file(s)")
                    self.logger.info(f"Loaded {len(test_files)} test files from {TEST_FILES_DIR}")
        except Exception as e:
            self.logger.error(f"Error loading test files: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
