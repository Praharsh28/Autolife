from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

class SubtitlePreview(QWidget):
    """Widget for previewing and comparing original and translated subtitles."""
    
    # Signals
    edit_requested = pyqtSignal(int, str)  # (index, text)
    subtitle_selected = pyqtSignal(int)  # index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_language = 'es'  # Default to Spanish
        self.subtitles = None
        self.current_index = -1
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for side-by-side view
        splitter = QSplitter(Qt.Horizontal)
        
        # Original subtitle panel
        original_frame = QFrame()
        original_layout = QVBoxLayout(original_frame)
        original_label = QLabel("Original Subtitles")
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        original_layout.addWidget(original_label)
        original_layout.addWidget(self.original_text)
        
        # Translated subtitle panel
        translated_frame = QFrame()
        translated_layout = QVBoxLayout(translated_frame)
        translated_label = QLabel("Translated Subtitles")
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        translated_layout.addWidget(translated_label)
        translated_layout.addWidget(self.translated_text)
        
        # Add frames to splitter
        splitter.addWidget(original_frame)
        splitter.addWidget(translated_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Selection")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        button_layout.addStretch()
        
        # Add all to main layout
        layout.addWidget(splitter)
        layout.addLayout(button_layout)
        
    def load_subtitles(self, subtitles):
        """Load subtitles into the preview."""
        if not isinstance(subtitles, dict):
            return False
            
        self.subtitles = subtitles
        self.current_index = -1
        
        try:
            # Load original subtitles
            if 'original' in subtitles and isinstance(subtitles['original'], list):
                self._display_subtitles(self.original_text, subtitles['original'])
            else:
                self.original_text.clear()
                
            # Load translated subtitles if available
            if 'translated' in subtitles and self.current_language:
                if self.current_language in subtitles['translated']:
                    self._display_subtitles(self.translated_text, subtitles['translated'][self.current_language])
                else:
                    self.translated_text.clear()
            else:
                self.translated_text.clear()
                
            return True
        except (TypeError, KeyError):
            self.clear_preview()
            return False
        
    def _display_subtitles(self, text_edit, subtitles):
        """Display subtitles in the specified text edit."""
        text_edit.clear()
        cursor = text_edit.textCursor()
        
        for i, sub in enumerate(subtitles):
            if i > 0:
                cursor.insertText('\n\n')
                
            # Format: [00:00.000] Text
            time_text = self._format_time(sub['start_time'])
            cursor.insertText(f'[{time_text}] ')
            
            # Insert subtitle text
            format = QTextCharFormat()
            format.setFontWeight(QFont.Normal)
            cursor.insertText(sub['text'], format)
            
    def _format_time(self, seconds):
        """Format time in seconds to [HH:MM:SS,mmm]."""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = seconds % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def set_current_time(self, time_seconds):
        """Set current time and highlight corresponding subtitle."""
        if not self.subtitles or 'original' not in self.subtitles:
            return
            
        # Find subtitle at current time
        for i, sub in enumerate(self.subtitles['original']):
            start = sub['start_time']
            end = start + sub.get('duration', 0)
            if start <= time_seconds <= end:
                self.select_subtitle(i)
                break

    def set_language(self, language):
        """Set the current translation language."""
        if self.current_language != language:
            self.current_language = language
            if self.subtitles:
                self.load_subtitles(self.subtitles)
                
    def clear_preview(self):
        """Clear all subtitle content."""
        self.subtitles = None
        self.current_index = -1
        self.original_text.clear()
        self.translated_text.clear()
        self.edit_btn.setEnabled(False)
        
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self.current_index >= 0 and self.subtitles and 'original' in self.subtitles:
            text = self.subtitles['original'][self.current_index]['text']
            self.edit_requested.emit(self.current_index, text)
            
    def select_subtitle(self, index):
        """Select a specific subtitle by index."""
        if self.current_index == index:
            return
            
        self.current_index = index
        self._highlight_subtitle(self.original_text, index)
        self._highlight_subtitle(self.translated_text, index)
        self.subtitle_selected.emit(index)
        self.edit_btn.setEnabled(True)

    def _highlight_subtitle(self, text_edit, index):
        """Highlight the specified subtitle in the text edit."""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # Move to the correct subtitle block
        for _ in range(index * 2):  # *2 because we have newlines between subtitles
            cursor.movePosition(QTextCursor.NextBlock)
            
        # Select the subtitle line
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        
        # Apply highlighting
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.yellow))
        cursor.mergeCharFormat(format)
        
    def apply_style(self, index, style_dict):
        """Apply style to a specific subtitle."""
        if not self.subtitles or 'original' not in self.subtitles:
            return
            
        format = QTextCharFormat()
        
        if style_dict.get('bold'):
            format.setFontWeight(QFont.Bold)
            
        if 'color' in style_dict:
            format.setForeground(QColor(style_dict['color']))
            
        # Apply to both text edits at specific index
        self._apply_format_to_subtitle(self.original_text, index, format)
        if self.current_language and self.current_language in self.subtitles.get('translated', {}):
            self._apply_format_to_subtitle(self.translated_text, index, format)

    def _apply_format_to_subtitle(self, text_edit, index, format):
        """Apply format to a specific subtitle in the text edit."""
        if not 0 <= index < len(self.subtitles['original']):
            return
            
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # Move to the correct subtitle
        for _ in range(index):
            cursor.movePosition(QTextCursor.NextBlock)
            cursor.movePosition(QTextCursor.NextBlock)
            
        # Select the subtitle text
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        cursor.mergeCharFormat(format)

    def get_current_subtitle(self):
        """Get the currently selected subtitle."""
        if self.current_index >= 0 and self.subtitles and 'original' in self.subtitles:
            return self.subtitles['original'][self.current_index]
        return None

    def request_edit(self, index, new_text):
        """Request to edit a subtitle at the specified index."""
        if not self.subtitles or 'original' not in self.subtitles:
            return False
            
        if 0 <= index < len(self.subtitles['original']):
            self.subtitles['original'][index]['text'] = new_text
            self._display_subtitles(self.original_text, self.subtitles['original'])
            self.edit_requested.emit(index, new_text)
            return True
            
        return False
