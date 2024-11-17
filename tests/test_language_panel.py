import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from modules.ui.language_panel import LanguagePanel
import sys

class TestLanguagePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        self.panel = LanguagePanel()
        
    def test_initial_state(self):
        """Test initial state of language panel."""
        # Check default source language
        self.assertEqual(self.panel.source_language.currentText(), "Auto")
        
        # Check target languages list is empty
        self.assertEqual(self.panel.target_languages.count(), 0)
        
    def test_add_target_language(self):
        """Test adding target language."""
        # Add language
        self.panel.add_target_language("Spanish")
        
        # Check language added
        self.assertEqual(self.panel.target_languages.count(), 1)
        self.assertEqual(self.panel.target_languages.item(0).text(), "Spanish")
        
    def test_remove_target_language(self):
        """Test removing target language."""
        # Add and remove language
        self.panel.add_target_language("French")
        self.panel.remove_target_language("French")
        
        # Check language removed
        self.assertEqual(self.panel.target_languages.count(), 0)
        
    def test_get_selected_languages(self):
        """Test getting selected languages."""
        # Add languages
        test_langs = ["Spanish", "French", "German"]
        for lang in test_langs:
            self.panel.add_target_language(lang)
            
        # Get selected languages
        selected = self.panel.get_selected_languages()
        
        # Check all languages selected
        self.assertEqual(set(selected), set(test_langs))
        
    def test_clear_languages(self):
        """Test clearing all languages."""
        # Add languages
        test_langs = ["Spanish", "French", "German"]
        for lang in test_langs:
            self.panel.add_target_language(lang)
            
        # Clear languages
        self.panel.clear_languages()
        
        # Check all cleared
        self.assertEqual(self.panel.target_languages.count(), 0)
        
    def test_language_changed_signal(self):
        """Test language changed signal."""
        # Track signal emissions
        signals_received = []
        
        def on_language_changed(lang):
            signals_received.append(lang)
            
        self.panel.language_changed.connect(on_language_changed)
        
        # Change source language
        self.panel.source_language.setCurrentText("English")
        
        # Check signal emitted
        self.assertEqual(len(signals_received), 1)
        self.assertEqual(signals_received[0], "English")
        
    def test_languages_changed_signal(self):
        """Test languages changed signal."""
        # Track signal emissions
        signals_received = []
        
        def on_languages_changed(langs):
            signals_received.append(langs)
            
        self.panel.languages_changed.connect(on_languages_changed)
        
        # Add language
        self.panel.add_target_language("Spanish")
        
        # Check signal emitted
        self.assertEqual(len(signals_received), 1)
        self.assertEqual(signals_received[0], ["Spanish"])
        
    def test_invalid_language(self):
        """Test handling invalid language."""
        # Try to add invalid language
        self.panel.add_target_language("")
        
        # Check not added
        self.assertEqual(self.panel.target_languages.count(), 0)
        
    def test_duplicate_language(self):
        """Test handling duplicate language."""
        # Add same language twice
        self.panel.add_target_language("Spanish")
        self.panel.add_target_language("Spanish")
        
        # Check added only once
        self.assertEqual(self.panel.target_languages.count(), 1)
        
if __name__ == '__main__':
    unittest.main()
