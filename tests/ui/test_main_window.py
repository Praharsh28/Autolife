"""Tests for the MainWindow class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

from modules.ui.main_window import MainWindow
from modules.workers.subtitle_worker import SubtitleWorker
from modules.workers.srt_to_ass_worker import SrtToAssWorker

@pytest.fixture
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def main_window(app, qtbot):
    """Create MainWindow instance."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitForWindowShown(window)
    yield window
    window.close()

@pytest.fixture
def mock_file_dialog():
    """Mock QFileDialog."""
    with patch('PyQt5.QtWidgets.QFileDialog') as mock:
        dialog = Mock()
        mock.return_value = dialog
        yield dialog

class TestMainWindow:
    """Test cases for MainWindow class."""

    @pytest.mark.ui
    def test_window_initialization(self, main_window):
        """Test window initialization."""
        assert isinstance(main_window, QMainWindow)
        assert main_window.windowTitle() == "AutoLife Media Processing"
        assert main_window.isVisible()

    @pytest.mark.ui
    def test_menu_actions(self, main_window, qtbot):
        """Test menu actions."""
        # File menu
        file_menu = main_window.menuBar().actions()[0].menu()
        assert file_menu is not None
        
        # Find and test actions
        actions = {action.text(): action for action in file_menu.actions()}
        assert "Open" in actions
        assert "Exit" in actions

    @pytest.mark.ui
    def test_file_selection(self, main_window, mock_file_dialog, qtbot):
        """Test file selection dialog."""
        # Mock file dialog response
        test_files = ["/path/to/test1.mp4", "/path/to/test2.mp4"]
        mock_file_dialog.getOpenFileNames.return_value = (test_files, "")
        
        # Trigger file selection
        main_window._open_files()
        
        # Verify dialog was shown with correct filters
        mock_file_dialog.getOpenFileNames.assert_called_once()
        assert "Media Files" in mock_file_dialog.getOpenFileNames.call_args[0][3]

    @pytest.mark.ui
    def test_file_list_widget(self, main_window, qtbot):
        """Test file list widget functionality."""
        # Add test files
        test_files = [Path("test1.mp4"), Path("test2.mp4")]
        main_window.file_list.add_files([str(f) for f in test_files])
        
        # Check files were added
        assert main_window.file_list.count() == 2
        
        # Test item selection
        main_window.file_list.setCurrentRow(0)
        assert main_window.file_list.currentItem() is not None

    @pytest.mark.ui
    def test_worker_integration(self, main_window, qtbot):
        """Test worker thread integration."""
        # Mock file selection
        test_files = [Path("test1.mp4"), Path("test2.mp4")]
        main_window.file_list.add_files([str(f) for f in test_files])
        
        # Start processing
        with patch.object(SubtitleWorker, '__init__', return_value=None):
            with patch.object(SubtitleWorker, 'start'):
                main_window._start_processing()
                assert main_window._worker is not None

    @pytest.mark.ui
    def test_progress_updates(self, main_window, qtbot):
        """Test progress bar updates."""
        # Setup progress tracking
        progress_values = []
        main_window.progress_bar.valueChanged.connect(
            lambda v: progress_values.append(v))
        
        # Simulate progress updates
        main_window._update_progress(50)
        assert progress_values[-1] == 50
        
        main_window._update_progress(100)
        assert progress_values[-1] == 100

    @pytest.mark.ui
    def test_error_handling(self, main_window, qtbot):
        """Test error dialog display."""
        # Mock error dialog
        with patch('PyQt5.QtWidgets.QMessageBox') as mock_dialog:
            # Trigger error
            main_window._show_error("Test error")
            
            # Verify error dialog
            mock_dialog.critical.assert_called_once()
            assert "Test error" in mock_dialog.critical.call_args[0]

    @pytest.mark.ui
    def test_settings_dialog(self, main_window, qtbot):
        """Test settings dialog."""
        # Mock settings dialog
        with patch('modules.ui.settings_dialog.SettingsDialog') as mock_dialog:
            dialog_instance = Mock()
            mock_dialog.return_value = dialog_instance
            
            # Open settings
            main_window._open_settings()
            
            # Verify dialog shown
            assert dialog_instance.exec_.called

    @pytest.mark.ui
    def test_drag_and_drop(self, main_window, qtbot):
        """Test drag and drop functionality."""
        # Create mock drop event
        event = MagicMock()
        event.mimeData().hasUrls.return_value = True
        event.mimeData().urls.return_value = [
            MagicMock(toLocalFile=lambda: "/path/to/test.mp4")
        ]
        
        # Simulate drop
        main_window.dragEnterEvent(event)
        assert event.accept.called
        
        main_window.dropEvent(event)
        assert main_window.file_list.count() > 0

    @pytest.mark.ui
    def test_keyboard_shortcuts(self, main_window, qtbot):
        """Test keyboard shortcuts."""
        # Test open files shortcut (Ctrl+O)
        with patch.object(main_window, '_open_files') as mock_open:
            QTest.keyClick(main_window, Qt.Key_O, Qt.ControlModifier)
            assert mock_open.called
        
        # Test start processing shortcut (Ctrl+R)
        with patch.object(main_window, '_start_processing') as mock_start:
            QTest.keyClick(main_window, Qt.Key_R, Qt.ControlModifier)
            assert mock_start.called

    @pytest.mark.ui
    def test_window_state_persistence(self, main_window, qtbot):
        """Test window state saving/restoration."""
        # Change window state
        new_size = (800, 600)
        main_window.resize(*new_size)
        
        # Mock settings
        with patch('PyQt5.QtCore.QSettings') as mock_settings:
            settings = Mock()
            mock_settings.return_value = settings
            
            # Close window (triggers save)
            main_window.close()
            
            # Verify state saved
            assert settings.setValue.called
