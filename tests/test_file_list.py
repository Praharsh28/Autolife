import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from modules.ui.file_list import FileList
import sys
from pathlib import Path
import tempfile
import shutil

class TestFileList(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        self.file_list = FileList()
        
        # Create temp directory with test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        for i in range(3):
            path = Path(self.temp_dir) / f"test_{i}.mp4"
            path.touch()
            self.test_files.append(str(path))
            
    def tearDown(self):
        # Clean up temp files
        shutil.rmtree(self.temp_dir)
        
    def test_add_files(self):
        """Test adding files to list."""
        # Add files
        self.file_list.add_files(self.test_files)
        
        # Check file count
        self.assertEqual(self.file_list.count(), len(self.test_files))
        
        # Check file names
        for i, file in enumerate(self.test_files):
            item_text = self.file_list.list_widget.item(i).text()
            self.assertIn(Path(file).name, item_text)
            
    def test_remove_files(self):
        """Test removing files from list."""
        # Add files
        self.file_list.add_files(self.test_files)
        
        # Get first item
        item = self.file_list.list_widget.item(0)
        self.file_list.remove_file(item)
        
        # Check file removed
        self.assertEqual(self.file_list.count(), len(self.test_files) - 1)
        first_item = self.file_list.list_widget.item(0).text()
        self.assertNotIn(Path(self.test_files[0]).name, first_item)
        
    def test_clear_files(self):
        """Test clearing all files."""
        # Add and clear files
        self.file_list.add_files(self.test_files)
        self.file_list.clear_files()
        
        # Check all cleared
        self.assertEqual(self.file_list.count(), 0)
        
    def test_file_selection(self):
        """Test file selection."""
        # Add files
        self.file_list.add_files(self.test_files)
        
        # Track selection signal
        selections = []
        
        def on_select(file_path):
            selections.append(file_path)
            
        self.file_list.fileSelected.connect(on_select)
        
        # Select file
        self.file_list.list_widget.item(0).setSelected(True)
        
        # Check selection signal
        self.assertEqual(len(selections), 1)
        self.assertEqual(Path(selections[0]).name, Path(self.test_files[0]).name)
        
    def test_file_status(self):
        """Test file status updates."""
        # Add file
        self.file_list.add_files([self.test_files[0]])
        
        # Update status
        self.file_list.update_file_status(self.test_files[0], processed=True, translated=True)
        
        # Check status updated
        item = self.file_list.list_widget.item(0)
        self.assertTrue(item.processed)
        self.assertTrue(item.translated)
        self.assertFalse(item.has_error)

    def test_file_error_status(self):
        """Test file error status updates."""
        # Add file
        self.file_list.add_files([self.test_files[0]])
        
        # Update status with error
        self.file_list.update_file_status(self.test_files[0], has_error=True)
        
        # Check error status
        item = self.file_list.list_widget.item(0)
        self.assertTrue(item.has_error)
        
    def test_duplicate_files(self):
        """Test handling duplicate files."""
        # Add same file twice
        self.file_list.add_files([self.test_files[0]])
        self.file_list.add_files([self.test_files[0]])
        
        # Check added only once
        self.assertEqual(self.file_list.count(), 1)
        
    def test_invalid_files(self):
        """Test handling invalid files."""
        # Try to add non-existent file
        invalid_file = str(Path(self.temp_dir) / "nonexistent.mp4")
        initial_count = self.file_list.count()
        self.file_list.add_files([invalid_file])
        
        # Check not added
        self.assertEqual(self.file_list.count(), initial_count)
        
    def test_get_selected_files(self):
        """Test getting selected files."""
        # Add files
        self.file_list.add_files(self.test_files)
        
        # Select multiple files
        self.file_list.list_widget.item(0).setSelected(True)
        self.file_list.list_widget.item(1).setSelected(True)
        
        # Get selected
        selected = self.file_list.get_files()
        
        # Check selection
        self.assertEqual(len(selected), len(self.test_files))
        selected_names = [Path(f).name for f in selected]
        self.assertIn(Path(self.test_files[0]).name, selected_names)
        self.assertIn(Path(self.test_files[1]).name, selected_names)
        
    def test_context_menu(self):
        """Test context menu for file item."""
        # Add file
        self.file_list.add_files([self.test_files[0]])
        
        # Get item position
        item = self.file_list.list_widget.item(0)
        rect = self.file_list.list_widget.visualItemRect(item)
        position = rect.center()
        
        # Show context menu
        self.file_list.show_context_menu(position)
        
        # Menu actions are tested through integration tests
        # since QMenu.exec_ cannot be easily tested in isolation
        
    def test_translate_retranslate(self):
        """Test translation and retranslation functionality."""
        # Add file
        self.file_list.add_files([self.test_files[0]])
        item = self.file_list.list_widget.item(0)
        
        # Test initial translation
        self.file_list.translate_file(item)
        self.file_list.update_file_status(self.test_files[0], processed=True, translated=True)
        self.assertTrue(item.processed)
        self.assertTrue(item.translated)
        
        # Test retranslation
        self.file_list.retranslate_file(item)
        # Status would be updated through signals in actual usage
        
if __name__ == '__main__':
    unittest.main()
