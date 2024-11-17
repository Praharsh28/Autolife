import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from modules.ui.subtitle_preview import SubtitlePreview
import sys

class TestSubtitlePreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        self.preview = SubtitlePreview()
        
        # Sample subtitle data
        self.sample_subs = {
            'original': [
                {'start_time': 0.0, 'duration': 2.0, 'text': 'Hello'},
                {'start_time': 2.5, 'duration': 1.5, 'text': 'World'}
            ],
            'translated': {
                'es': [
                    {'start_time': 0.0, 'duration': 2.0, 'text': 'Hola'},
                    {'start_time': 2.5, 'duration': 1.5, 'text': 'Mundo'}
                ]
            }
        }
        
    def test_initial_state(self):
        """Test initial state of preview."""
        # Check empty state
        self.assertEqual(self.preview.original_text.toPlainText(), "")
        self.assertEqual(self.preview.translated_text.toPlainText(), "")
        
    def test_load_subtitles(self):
        """Test loading subtitles."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Check original text loaded
        original_text = self.preview.original_text.toPlainText()
        self.assertIn("Hello", original_text)
        self.assertIn("World", original_text)
        
        # Check translated text loaded
        translated_text = self.preview.translated_text.toPlainText()
        self.assertIn("Hola", translated_text)
        self.assertIn("Mundo", translated_text)
        
    def test_clear_preview(self):
        """Test clearing preview."""
        # Load and clear
        self.preview.load_subtitles(self.sample_subs)
        self.preview.clear_preview()
        
        # Check cleared
        self.assertEqual(self.preview.original_text.toPlainText(), "")
        self.assertEqual(self.preview.translated_text.toPlainText(), "")
        
    def test_edit_subtitle(self):
        """Test subtitle editing."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Track edit signal
        edits_received = []
        
        def on_edit(index, text):
            edits_received.append((index, text))
            
        self.preview.edit_requested.connect(on_edit)
        
        # Simulate edit
        self.preview.request_edit(0, "New Text")
        
        # Check edit signal
        self.assertEqual(len(edits_received), 1)
        self.assertEqual(edits_received[0], (0, "New Text"))
        
    def test_time_navigation(self):
        """Test time-based navigation."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Set current time
        self.preview.set_current_time(2.5)
        
        # Check correct subtitle highlighted
        current = self.preview.get_current_subtitle()
        self.assertEqual(current['text'], "World")
        
    def test_language_switch(self):
        """Test switching translation language."""
        # Add another language
        subs_multi = self.sample_subs.copy()
        subs_multi['translated']['fr'] = [
            {'start_time': 0.0, 'duration': 2.0, 'text': 'Bonjour'},
            {'start_time': 2.5, 'duration': 1.5, 'text': 'Monde'}
        ]
        
        self.preview.load_subtitles(subs_multi)
        
        # Switch language
        self.preview.set_language('fr')
        
        # Check French text shown
        translated_text = self.preview.translated_text.toPlainText()
        self.assertIn("Bonjour", translated_text)
        self.assertIn("Monde", translated_text)
        
    def test_invalid_subtitles(self):
        """Test handling invalid subtitle data."""
        # Test with empty data
        self.preview.load_subtitles({})
        self.assertEqual(self.preview.original_text.toPlainText(), "")
        
        # Test with invalid structure
        invalid_subs = {'original': 'not a list'}
        self.preview.load_subtitles(invalid_subs)
        self.assertEqual(self.preview.original_text.toPlainText(), "")
        
    def test_time_formatting(self):
        """Test subtitle time formatting."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Get formatted text
        text = self.preview.original_text.toPlainText()
        
        # Check time format (00:00:00,000)
        self.assertRegex(text, r'\d{2}:\d{2}:\d{2},\d{3}')
        
    def test_subtitle_selection(self):
        """Test subtitle selection."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Track selection signal
        selections = []
        
        def on_select(index):
            selections.append(index)
            
        self.preview.subtitle_selected.connect(on_select)
        
        # Select subtitle
        self.preview.select_subtitle(1)
        
        # Check selection signal
        self.assertEqual(len(selections), 1)
        self.assertEqual(selections[0], 1)
        
    def test_style_application(self):
        """Test subtitle style application."""
        self.preview.load_subtitles(self.sample_subs)
        
        # Apply style
        style = {'bold': True, 'color': '#FF0000'}
        self.preview.apply_style(0, style)
        
        # Check style applied (implementation dependent)
        # This is a placeholder for actual style checking
        pass
        
if __name__ == '__main__':
    unittest.main()
