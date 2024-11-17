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
    QCheckBox, QSpinBox, QGroupBox, QStyle, QApplication, QInputDialog, QDialog
)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets
from modules.tools_window import ToolsWindow
from .file_list_widget import FileListWidget
from .workers.subtitle_worker import SubtitleWorker
from .workers.srt_to_ass_worker import SrtToAssWorker
from .utilities import setup_logger
from .constants import *
from .sidebar_menu import SidebarMenu
from .dialogs import (
    SubtitleGenerationDialog,
    FormatConversionDialog,
    SubtitleEditDialog,
    BatchProcessingDialog,
    TemplateManagementDialog
)

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
            right_layout.addWidget(self.file_list)
            
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
            
            # Create processing options group
            options_group = QGroupBox("Processing Options")
            options_layout = QHBoxLayout()
            options_group.setLayout(options_layout)
            
            # Add processing options
            options_layout.addWidget(QLabel("Batch Size:"))
            options_layout.addWidget(self.batch_size_spinbox)
            options_layout.addWidget(self.delete_original_checkbox)
            options_layout.addStretch()
            
            # Add options group to right panel
            right_layout.addWidget(options_group)
            
            # Add progress bar and status display
            right_layout.addWidget(self.progress_bar)
            right_layout.addWidget(self.status_display)
            
            # Add right panel to main layout
            main_layout.addWidget(right_panel)
            
            # Connect sidebar signals
            self.sidebar.tool_selected.connect(self.handle_tool_selection)
            
            self.logger.info("UI initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {str(e)}")
            raise

    def handle_tool_selection(self, tool_name):
        """Handle tool selection from the sidebar menu."""
        try:
            self.logger.info(f"Tool selected: {tool_name}")
            
            # Get selected files
            files = self.file_list.get_selected_files()
            
            # Map tool names to functions
            tool_map = {
                "Generate Subtitles": self.generate_subtitles,
                "Edit Subtitles": self.edit_subtitles,
                "Convert Video": self.convert_video,
                "Convert Audio": self.convert_audio,
                "Convert Subtitles": self.convert_subtitle,
                "Batch Process": self.batch_process,
                "Manage Templates": self.manage_templates,
                "Extract Audio": self.extract_audio,
                "Merge Subtitles": self.merge_subtitles,
                "Split Subtitles": self.split_subtitles,
                "Sync Subtitles": self.sync_subtitles,
                "Convert SRT to ASS": self.convert_srt_to_ass,
                "Convert MXF to MP4": self.convert_mxf_to_mp4,
                "Convert MP4 to MXF": self.convert_mp4_to_mxf,
                "Overlay Subtitles": self.overlay_subtitles
            }
            
            # Execute the selected tool
            if tool_name in tool_map:
                tool_map[tool_name]()
            else:
                self.logger.warning(f"Unknown tool selected: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle tool selection: {str(e)}")
            self.handle_error(str(e))

    def extract_audio(self):
        """Extract audio from video files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select video files to extract audio from.")
                return

            self.logger.info(f"Starting audio extraction for {len(files)} files")
            self.status_display.append(f"Starting audio extraction...")
            
            # Create worker for audio extraction (to be implemented)
            self.extract_audio_worker = AudioExtractionWorker(
                files,
                self.batch_size_spinbox.value(),
                delete_original=self.delete_original_checkbox.isChecked()
            )
            
            # Connect signals
            self.extract_audio_worker.signals.progress.connect(self.update_progress)
            self.extract_audio_worker.signals.file_completed.connect(self.update_file_progress)
            self.extract_audio_worker.signals.error.connect(self.handle_error)
            self.extract_audio_worker.signals.finished.connect(self.process_completed)
            
            # Start worker
            self.extract_audio_worker.start()
            
            # Disable buttons while processing
            self.set_buttons_enabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to start audio extraction: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def edit_subtitles(self):
        """Open subtitle editor."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select subtitle files to edit.")
                return

            dialog = SubtitleEditDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                self.logger.info(f"Saving subtitle edits with settings: {values}")
                
                # Create worker for subtitle editing
                self.subtitle_edit_worker = SubtitleEditWorker(
                    files[0],
                    values['timing'],
                    values['style'],
                    delete_original=self.delete_original_checkbox.isChecked()
                )
                
                # Connect signals
                self.subtitle_edit_worker.signals.progress.connect(self.update_progress)
                self.subtitle_edit_worker.signals.error.connect(self.handle_error)
                self.subtitle_edit_worker.signals.finished.connect(self.process_completed)
                
                # Start worker
                self.subtitle_edit_worker.start()
                
                # Disable buttons while processing
                self.set_buttons_enabled(False)
                
        except Exception as e:
            self.logger.error(f"Failed to edit subtitles: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def merge_subtitles(self):
        """Merge multiple subtitle files."""
        try:
            files = self.file_list.get_selected_files()
            if len(files) < 2:
                QMessageBox.warning(self, "Not Enough Files", 
                                  "Please select at least two subtitle files to merge.")
                return

            # Show merge options dialog (to be implemented)
            self.merge_dialog = SubtitleMergeDialog(files, self)
            if self.merge_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting subtitle merge...")
                # Implement merge logic
                
        except Exception as e:
            self.logger.error(f"Failed to merge subtitles: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to merge subtitles: {str(e)}")

    def split_subtitles(self):
        """Split subtitle file into multiple parts."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select a subtitle file to split.")
                return

            # Show split options dialog (to be implemented)
            self.split_dialog = SubtitleSplitDialog(files[0], self)
            if self.split_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting subtitle split...")
                # Implement split logic
                
        except Exception as e:
            self.logger.error(f"Failed to split subtitles: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to split subtitles: {str(e)}")

    def sync_subtitles(self):
        """Synchronize subtitles with video."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to sync.")
                return

            # Show sync options dialog (to be implemented)
            self.sync_dialog = SubtitleSyncDialog(files, self)
            if self.sync_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting subtitle sync...")
                # Implement sync logic
                
        except Exception as e:
            self.logger.error(f"Failed to sync subtitles: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to sync subtitles: {str(e)}")

    def convert_video(self):
        """Convert video files to different formats."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select video files to convert.")
                return

            dialog = FormatConversionDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                self.logger.info(f"Starting video conversion with settings: {values}")
                
                # Create worker for video conversion
                self.video_worker = VideoConversionWorker(
                    files,
                    values['output_format'],
                    video_settings=values['video'],
                    audio_settings=values['audio'],
                    preserve_metadata=values['preserve_metadata'],
                    hardware_acceleration=values['hardware_acceleration'],
                    batch_size=self.batch_size_spinbox.value(),
                    delete_original=self.delete_original_checkbox.isChecked()
                )
                
                # Connect signals
                self.video_worker.signals.progress.connect(self.update_progress)
                self.video_worker.signals.file_completed.connect(self.update_file_progress)
                self.video_worker.signals.error.connect(self.handle_error)
                self.video_worker.signals.finished.connect(self.process_completed)
                
                # Start worker
                self.video_worker.start()
                
                # Disable buttons while processing
                self.set_buttons_enabled(False)
                
        except Exception as e:
            self.logger.error(f"Failed to start video conversion: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def convert_audio(self):
        """Convert audio files to different formats."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select audio files to convert.")
                return

            # Show format selection dialog (to be implemented)
            self.audio_convert_dialog = AudioConvertDialog(files, self)
            if self.audio_convert_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting audio conversion...")
                # Implement conversion logic
                
        except Exception as e:
            self.logger.error(f"Failed to convert audio: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to convert audio: {str(e)}")

    def convert_subtitle(self):
        """Convert subtitle files to different formats."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select subtitle files to convert.")
                return

            # Show format selection dialog (to be implemented)
            self.subtitle_convert_dialog = SubtitleConvertDialog(files, self)
            if self.subtitle_convert_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting subtitle conversion...")
                # Implement conversion logic
                
        except Exception as e:
            self.logger.error(f"Failed to convert subtitles: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to convert subtitles: {str(e)}")

    def show_mxf_mpf_dialog(self):
        """Show MXF MPF conversion dialog."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select files to convert.")
                return

            # Show conversion dialog (to be implemented)
            self.mxf_mpf_dialog = MXFMPFDialog(files, self)
            if self.mxf_mpf_dialog.exec_() == QDialog.Accepted:
                self.status_display.append("Starting MXF/MPF conversion...")
                # Implement conversion logic
                
        except Exception as e:
            self.logger.error(f"Failed to show MXF/MPF dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show MXF/MPF dialog: {str(e)}")

    def batch_process(self):
        """Show batch processing dialog."""
        try:
            dialog = BatchProcessingDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                self.logger.info(f"Starting batch processing with settings: {values}")
                
                # Create worker for batch processing
                self.batch_worker = BatchProcessingWorker(
                    values['files'],
                    values['operation'],
                    values['output_directory'],
                    parallel_processing=values['parallel_processing'],
                    error_handling=values['error_handling'],
                    delete_original=self.delete_original_checkbox.isChecked()
                )
                
                # Connect signals
                self.batch_worker.signals.progress.connect(self.update_progress)
                self.batch_worker.signals.file_completed.connect(self.update_file_progress)
                self.batch_worker.signals.error.connect(self.handle_error)
                self.batch_worker.signals.finished.connect(self.process_completed)
                
                # Start worker
                self.batch_worker.start()
                
                # Disable buttons while processing
                self.set_buttons_enabled(False)
                
        except Exception as e:
            self.logger.error(f"Failed to start batch processing: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def manage_templates(self):
        """Show template management dialog."""
        try:
            dialog = TemplateManagementDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                self.logger.info(f"Template saved: {values['name']}")
                
        except Exception as e:
            self.logger.error(f"Failed to manage templates: {str(e)}", exc_info=True)
            self.handle_error(str(e))

    def generate_subtitles(self):
        """Generate subtitles for selected files."""
        try:
            files = self.file_list.get_selected_files()
            if not files:
                QMessageBox.warning(self, "No Files Selected", 
                                  "Please select video or audio files to generate subtitles for.")
                return

            dialog = SubtitleGenerationDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                self.logger.info(f"Starting subtitle generation with settings: {values}")
                
                # Create worker for subtitle generation
                self.subtitle_worker = SubtitleWorker(
                    files,
                    values['language'],
                    values['output_format'],
                    word_timing=values['word_timing'],
                    speaker_diarization=values['speaker_diarization'],
                    max_speakers=values['max_speakers'],
                    batch_size=self.batch_size_spinbox.value(),
                    delete_original=self.delete_original_checkbox.isChecked()
                )
                
                # Connect signals
                self.subtitle_worker.signals.progress.connect(self.update_progress)
                self.subtitle_worker.signals.file_completed.connect(self.update_file_progress)
                self.subtitle_worker.signals.error.connect(self.handle_error)
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

            # Use default template
            template_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'templates',
                'default.ass'
            )
            
            if not os.path.exists(template_file):
                QMessageBox.critical(self, "Template Missing", 
                                  f"Default template not found: {template_file}")
                return

            # Read available styles
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
                self.batch_size_spinbox.value()
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
                self.batch_size_spinbox.value()
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
                self.batch_size_spinbox.value()
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
            default_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files') if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files')) else os.path.expanduser("~")

            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Add Files",
                default_dir,
                "All Supported Files (*.mp4 *.mxf *.srt *.ass);;Video Files (*.mp4 *.mxf);;Subtitle Files (*.srt *.ass);;All Files (*.*)"
            )
            
            # Use the file_list's add_files method
            if files:
                self.file_list.add_files(files)
                self.logger.info(f"Added {len(files)} files to list")

        except Exception as e:
            error_msg = f"Error opening files: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def remove_selected_files(self):
        """Remove selected files from the list."""
        try:
            self.file_list.remove_selected()
        except Exception as e:
            error_msg = f"Error removing files: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def log_message(self, message):
        """Add a message to the status display."""
        self.status_display.append(message)
        self.logger.info(message)

    def set_buttons_enabled(self, enabled):
        """Enable or disable buttons."""
        self.sidebar.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

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
            test_files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files')
            if os.path.exists(test_files_dir):
                test_files = []
                for file in os.listdir(test_files_dir):
                    file_path = os.path.join(test_files_dir, file)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.file_list.VIDEO_FORMATS or ext in self.file_list.AUDIO_FORMATS or ext in self.file_list.SUBTITLE_FORMATS:
                            test_files.append(file_path)
                
                if test_files:
                    self.file_list.add_files(test_files)
                    self.logger.info(f"Loaded {len(test_files)} test files from {test_files_dir}")
                else:
                    self.logger.info(f"No compatible test files found in {test_files_dir}")
                
        except Exception as e:
            self.logger.error(f"Error loading test files: {str(e)}", exc_info=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
