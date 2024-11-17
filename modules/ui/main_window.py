from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSplitter, QFileDialog, QMessageBox, QDockWidget,
    QToolBar, QStatusBar, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon

from .language_panel import LanguagePanel
from .subtitle_preview import SubtitlePreview
from .file_list import FileList
from ..processing.batch_manager import BatchManager, ProcessingStatus
from ..utils.sync_utils import SubtitleSynchronizer
from ..workers.subtitle_worker import SubtitleWorker
from ..constants import APP_NAME, APP_VERSION

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.settings = QSettings(APP_NAME, APP_VERSION)
        self.subtitle_worker = SubtitleWorker()
        self.batch_manager = BatchManager(max_concurrent=2)
        self.subtitle_sync = SubtitleSynchronizer()
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Connect batch manager signals
        self.batch_manager.on_task_complete = self.on_task_complete
        self.batch_manager.on_task_error = self.on_task_error
        self.batch_manager.on_progress_update = self.on_progress_update
        
        # Start batch processing
        self.batch_manager.start_processing()
        
    def setup_ui(self):
        """Initialize the UI components."""
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel (file list and controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # File list
        self.file_list = FileList()
        left_layout.addWidget(self.file_list)
        
        # Batch controls
        batch_controls = QHBoxLayout()
        self.start_batch_btn = QPushButton("Start Batch")
        self.cancel_batch_btn = QPushButton("Cancel Batch")
        batch_controls.addWidget(self.start_batch_btn)
        batch_controls.addWidget(self.cancel_batch_btn)
        left_layout.addLayout(batch_controls)
        
        main_layout.addWidget(left_panel)
        
        # Right panel (language selection and preview)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Language panel
        self.language_panel = LanguagePanel()
        right_layout.addWidget(self.language_panel)
        
        # Subtitle preview
        self.subtitle_preview = SubtitlePreview()
        right_layout.addWidget(self.subtitle_preview)
        
        main_layout.addWidget(right_panel)
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connect signals
        self.start_batch_btn.clicked.connect(self.start_batch)
        self.cancel_batch_btn.clicked.connect(self.cancel_batch)
        self.file_list.fileSelected.connect(self.on_file_selected)
        self.language_panel.languageChanged.connect(self.on_language_changed)
        self.language_panel.languages_changed.connect(self.on_languages_changed)
        
    def setup_toolbar(self):
        """Setup the main toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add media files action
        add_action = QAction("Add Files", self)
        add_action.setStatusTip("Add media files for subtitle generation")
        add_action.triggered.connect(self.add_files)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Start processing action
        process_action = QAction("Process All", self)
        process_action.setStatusTip("Process all files in the list")
        process_action.triggered.connect(self.process_files)
        toolbar.addAction(process_action)
        
        # Cancel processing action
        cancel_action = QAction("Cancel", self)
        cancel_action.setStatusTip("Cancel current processing")
        cancel_action.triggered.connect(self.cancel_processing)
        cancel_action.setEnabled(False)
        toolbar.addAction(cancel_action)
        
    def setup_connections(self):
        """Setup signal/slot connections."""
        # File list signals
        self.file_list.filesAdded.connect(self.update_status)
        
        # Subtitle preview signals
        self.subtitle_preview.editRequested.connect(self.edit_subtitle)
        
        # Worker signals
        self.subtitle_worker.signals.progress.connect(self.update_progress)
        self.subtitle_worker.signals.finished.connect(self.on_processing_finished)
        self.subtitle_worker.signals.error.connect(self.show_error)
        
    def load_settings(self):
        """Load application settings."""
        # Window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Window state
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
    def save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
    def add_files(self):
        """Open file dialog to add media files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Media Files",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        if files:
            self.file_list.add_files(files)
            
    def process_files(self):
        """Start processing all files in the list."""
        if not self.file_list.has_files():
            QMessageBox.warning(self, "No Files", "Please add files to process.")
            return
            
        self.language_panel.enable_translation(False)
        self.subtitle_worker.process_files(
            self.file_list.get_files(),
            self.language_panel.target_combo.currentData()
        )
        
    def cancel_processing(self):
        """Cancel current processing."""
        self.subtitle_worker.stop()
        self.language_panel.enable_translation(True)
        
    def on_file_selected(self, file_path: str):
        """Handle file selection in the file list."""
        subtitles = self.subtitle_worker.get_subtitles(file_path)
        if subtitles:
            self.subtitle_preview.set_original_subtitles(subtitles)
            
    def on_language_changed(self, language_pair: str):
        """Handle language selection change."""
        self.status_bar.showMessage(f"Selected language pair: {language_pair}")
        
    def translate_subtitles(self, source_lang: str, target_lang: str):
        """Handle translation request."""
        current_file = self.file_list.get_selected_file()
        if not current_file:
            QMessageBox.warning(self, "No File", "Please select a file to translate.")
            return
            
        self.language_panel.enable_translation(False)
        self.subtitle_worker.translate_file(current_file, source_lang, target_lang)
        
    def edit_subtitle(self, index: int):
        """Handle subtitle edit request."""
        # This would open a subtitle edit dialog
        pass
        
    def update_progress(self, progress: int, status: str):
        """Update progress in UI."""
        self.language_panel.update_progress(progress, status)
        self.status_bar.showMessage(status)
        
    def on_processing_finished(self):
        """Handle processing completion."""
        self.language_panel.enable_translation(True)
        self.language_panel.reset_progress()
        self.status_bar.showMessage("Processing completed")
        
    def show_error(self, error: str):
        """Show error message."""
        QMessageBox.critical(self, "Error", error)
        
    def update_status(self):
        """Update status bar with file count."""
        count = self.file_list.count()
        self.status_bar.showMessage(f"Files in queue: {count}")
        
    def on_task_complete(self, task_id: str, task):
        """Handle completed batch processing task."""
        self.file_list.update_file_status(task_id, "Completed")
        self.subtitle_preview.load_subtitles(task.result)
        
    def on_task_error(self, task_id: str, error: str):
        """Handle batch processing error."""
        self.file_list.update_file_status(task_id, f"Error: {error}")
        
    def on_progress_update(self, task_id: str, progress: float):
        """Update progress for a batch task."""
        self.file_list.update_file_progress(task_id, progress)
        
    def start_batch(self):
        """Start batch processing for selected files."""
        selected_files = self.file_list.get_selected_files()
        target_languages = self.language_panel.get_selected_languages()
        
        for file_path in selected_files:
            task_id = self.batch_manager.add_task(file_path, target_languages)
            self.file_list.update_file_status(task_id, "Pending")
            
    def cancel_batch(self):
        """Cancel current batch processing."""
        selected_files = self.file_list.get_selected_files()
        for file_path in selected_files:
            self.batch_manager.cancel_task(str(file_path))
            
    def on_file_selected(self, file_path: str):
        """Handle file selection."""
        task = self.batch_manager.get_task_status(file_path)
        if task and task.status == ProcessingStatus.COMPLETED:
            self.subtitle_preview.load_subtitles(task.result)
            
    def on_languages_changed(self, languages: list):
        """Handle language selection changes."""
        # Update batch tasks if needed
        selected_files = self.file_list.get_selected_files()
        for file_path in selected_files:
            self.batch_manager.add_task(file_path, languages)
            
    def closeEvent(self, event):
        """Clean up before closing."""
        self.batch_manager.stop_processing()
        self.save_settings()
        self.subtitle_worker.stop()
        super().closeEvent(event)
