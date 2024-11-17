from PyQt5.QtWidgets import (QListWidget, QSpinBox, QLabel, QFileDialog,
                             QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
                             QGroupBox, QComboBox, QProgressBar, QCheckBox)
from PyQt5.QtCore import Qt
from .base_dialog import BaseDialog

class BatchProcessingDialog(BaseDialog):
    """Dialog for batch processing multiple files."""
    
    description = """Process multiple files in batch with customizable settings
                    and processing options."""
    
    def __init__(self, parent=None):
        super().__init__("Batch Processing", parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Input files list
        files_group = QGroupBox("Input Files")
        files_layout = QVBoxLayout()
        
        # File list
        self.file_list = QListWidget()
        files_layout.addWidget(self.file_list)
        
        # File buttons
        button_layout = QHBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.file_list.clear)
        
        button_layout.addWidget(add_files_btn)
        button_layout.addWidget(add_folder_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(clear_btn)
        files_layout.addLayout(button_layout)
        
        files_group.setLayout(files_layout)
        self.content_layout.addWidget(files_group)
        
        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        
        # Operation type
        operation_layout = QHBoxLayout()
        self.operation = QComboBox()
        self.operation.addItems([
            "Generate Subtitles",
            "Convert Format",
            "Extract Audio",
            "Edit Subtitles",
            "Merge Subtitles"
        ])
        
        operation_layout.addWidget(QLabel("Operation:"))
        operation_layout.addWidget(self.operation)
        operation_layout.addStretch()
        options_layout.addLayout(operation_layout)
        
        # Output settings
        output_layout = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select output directory...")
        self.output_dir.setReadOnly(True)
        
        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self._browse_output)
        
        output_layout.addWidget(QLabel("Output Directory:"))
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(browse_output_btn)
        options_layout.addLayout(output_layout)
        
        # Processing settings
        settings_layout = QHBoxLayout()
        
        self.parallel_processing = QCheckBox("Enable parallel processing")
        self.parallel_processing.setChecked(True)
        
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 16)
        self.max_threads.setValue(4)
        
        settings_layout.addWidget(self.parallel_processing)
        settings_layout.addWidget(QLabel("Max threads:"))
        settings_layout.addWidget(self.max_threads)
        settings_layout.addStretch()
        options_layout.addLayout(settings_layout)
        
        # Error handling
        error_layout = QHBoxLayout()
        self.on_error = QComboBox()
        self.on_error.addItems([
            "Stop processing",
            "Skip and continue",
            "Retry once",
            "Retry three times"
        ])
        
        error_layout.addWidget(QLabel("On Error:"))
        error_layout.addWidget(self.on_error)
        error_layout.addStretch()
        options_layout.addLayout(error_layout)
        
        options_group.setLayout(options_layout)
        self.content_layout.addWidget(options_group)
        
        # Progress tracking
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        # Overall progress
        self.overall_progress = QProgressBar()
        progress_layout.addWidget(QLabel("Overall Progress:"))
        progress_layout.addWidget(self.overall_progress)
        
        # Current file progress
        self.file_progress = QProgressBar()
        progress_layout.addWidget(QLabel("Current File:"))
        progress_layout.addWidget(self.file_progress)
        
        progress_group.setLayout(progress_layout)
        self.content_layout.addWidget(progress_group)
        
    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.srt *.ass);;All Files (*.*)"
        )
        for file in files:
            self.file_list.addItem(file)
            
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            # TODO: Add all media files from the folder
            pass
            
    def _remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
            
    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            self.output_dir.setText(folder)
            
    def get_values(self):
        """Get the dialog values as a dictionary."""
        return {
            'files': [
                self.file_list.item(i).text()
                for i in range(self.file_list.count())
            ],
            'operation': self.operation.currentText(),
            'output_directory': self.output_dir.text(),
            'parallel_processing': {
                'enabled': self.parallel_processing.isChecked(),
                'max_threads': self.max_threads.value()
            },
            'error_handling': self.on_error.currentText()
        }
