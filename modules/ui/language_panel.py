from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QProgressBar, QPushButton, QFrame, QListWidget,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from ..constants import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from ..language_utils import TranslationManager

class LanguagePanel(QWidget):
    """Panel for language selection and translation progress."""
    
    language_changed = pyqtSignal(str)  # Emitted when source/target language changes
    languages_changed = pyqtSignal(list)  # Emitted when language list changes
    translationRequested = pyqtSignal(str, str)  # source_lang, target_lang
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translation_manager = TranslationManager()
        self._suppress_selection_signal = False
        self.setup_ui()
        
        # Connect signals
        self.source_language.currentTextChanged.connect(self._on_language_changed)
        self.target_languages.itemSelectionChanged.connect(self._on_target_selection_changed)
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Language selection section
        lang_frame = QFrame()
        lang_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        lang_layout = QVBoxLayout(lang_frame)
        
        # Source language
        source_layout = QHBoxLayout()
        source_label = QLabel("Source Language:")
        self.source_language = QComboBox()
        self.source_language.addItem("Auto")  # Default source language
        for lang in sorted(SUPPORTED_LANGUAGES):
            self.source_language.addItem(lang)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_language)
        
        # Target language
        target_layout = QVBoxLayout()
        target_label = QLabel("Target Languages:")
        self.target_languages = QListWidget()
        self.target_languages.setSelectionMode(QAbstractItemView.MultiSelection)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_languages)
        
        # Add language selections to frame
        lang_layout.addLayout(source_layout)
        lang_layout.addLayout(target_layout)
        
        # Translation progress section
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        # Translate button
        self.translate_btn = QPushButton("Translate")
        self.translate_btn.clicked.connect(self.request_translation)
        self.translate_btn.setEnabled(False)  # Initially disabled until languages are selected
        
        # Add all widgets to main layout
        layout.addWidget(lang_frame)
        layout.addWidget(progress_frame)
        layout.addWidget(self.translate_btn)
        layout.addStretch()
                
    def add_target_language(self, language: str) -> bool:
        """Add a target language to the list if it's valid and not already present."""
        if not language or language not in SUPPORTED_LANGUAGES:
            return False
            
        # Check if language already exists
        items = self.target_languages.findItems(language, Qt.MatchExactly)
        if items:
            return False
                
        # Add and select the item
        self._suppress_selection_signal = True
        item = self.target_languages.addItem(language)
        last_row = self.target_languages.count() - 1
        last_item = self.target_languages.item(last_row)
        last_item.setSelected(True)
        self._suppress_selection_signal = False
        
        self.languages_changed.emit(self.get_selected_languages())
        return True
    
    def remove_target_language(self, language: str) -> bool:
        """Remove a target language from the list."""
        items = self.target_languages.findItems(language, Qt.MatchExactly)
        if items:
            self._suppress_selection_signal = True
            for item in items:
                self.target_languages.takeItem(self.target_languages.row(item))
            self._suppress_selection_signal = False
            self.languages_changed.emit(self.get_selected_languages())
            return True
        return False
    
    def get_selected_languages(self) -> list:
        """Get list of all target languages."""
        return [item.text() for item in self.target_languages.selectedItems()]
    
    def clear_languages(self):
        """Clear all languages from the target list."""
        self._suppress_selection_signal = True
        self.target_languages.clear()
        self._suppress_selection_signal = False
        self.languages_changed.emit([])
    
    def _on_language_changed(self, text: str):
        """Handle source language selection changes."""
        if text:
            self.language_changed.emit(text)
            self._update_translate_button()
    
    def _on_target_selection_changed(self):
        """Handle target language selection changes."""
        if not self._suppress_selection_signal:
            self._update_translate_button()
            self.languages_changed.emit(self.get_selected_languages())
    
    def _update_translate_button(self):
        """Update translate button enabled state based on selections."""
        source = self.source_language.currentText()
        targets = self.get_selected_languages()
        self.translate_btn.setEnabled(bool(source and targets))
    
    def request_translation(self):
        """Emit signal to request translation."""
        source = self.source_language.currentText()
        targets = self.get_selected_languages()
        if source and targets:
            for target in targets:
                self.translationRequested.emit(source, target)
            
    def update_progress(self, progress: int, status: str = ""):
        """Update translation progress."""
        self.progress_bar.setValue(progress)
        if status:
            self.status_label.setText(status)
            
    def reset_progress(self):
        """Reset progress bar and status."""
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        
    def enable_translation(self, enable: bool):
        """Enable or disable translation controls."""
        self.source_language.setEnabled(enable)
        self.target_languages.setEnabled(enable)
        self.translate_btn.setEnabled(enable and bool(self.get_selected_languages()))
