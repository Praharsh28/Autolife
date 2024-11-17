"""Tests for the SubtitleEdit widget."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest

from modules.ui.subtitle_edit import SubtitleEdit, SubtitleEntry
from modules.constants import (
    MIN_DURATION, MAX_DURATION, MIN_CHARS_PER_LINE,
    MAX_CHARS_PER_LINE, MIN_WORDS_PER_LINE
)

@pytest.fixture
def subtitle_edit(qtbot):
    """Create SubtitleEdit widget instance."""
    widget = SubtitleEdit()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitForWindowShown(widget)
    yield widget
    widget.close()

@pytest.fixture
def sample_subtitles():
    """Create sample subtitle entries."""
    return [
        SubtitleEntry(start=0, duration=2, text="First subtitle"),
        SubtitleEntry(start=2, duration=3, text="Second subtitle"),
        SubtitleEntry(start=5, duration=2.5, text="Third subtitle")
    ]

class TestSubtitleEdit:
    """Test cases for SubtitleEdit widget."""

    @pytest.mark.ui
    def test_widget_initialization(self, subtitle_edit):
        """Test widget initialization."""
        assert isinstance(subtitle_edit, QWidget)
        assert subtitle_edit.isVisible()
        assert subtitle_edit.subtitle_list is not None
        assert subtitle_edit.edit_panel is not None

    @pytest.mark.ui
    def test_subtitle_loading(self, subtitle_edit, sample_subtitles):
        """Test loading subtitles into the widget."""
        subtitle_edit.load_subtitles(sample_subtitles)
        
        # Check if all subtitles are loaded
        assert subtitle_edit.subtitle_list.count() == len(sample_subtitles)
        
        # Verify first item content
        first_item = subtitle_edit.subtitle_list.item(0)
        assert "First subtitle" in first_item.text()
        assert "0:00" in first_item.text()

    @pytest.mark.ui
    def test_subtitle_selection(self, subtitle_edit, sample_subtitles, qtbot):
        """Test subtitle selection and editing."""
        subtitle_edit.load_subtitles(sample_subtitles)
        
        # Select first subtitle
        subtitle_edit.subtitle_list.setCurrentRow(0)
        qtbot.wait(100)
        
        # Verify edit panel shows correct data
        assert subtitle_edit.edit_panel.text_edit.toPlainText() == "First subtitle"
        assert subtitle_edit.edit_panel.start_time.value() == 0
        assert subtitle_edit.edit_panel.duration.value() == 2

    @pytest.mark.ui
    def test_subtitle_editing(self, subtitle_edit, sample_subtitles, qtbot):
        """Test editing subtitle properties."""
        subtitle_edit.load_subtitles(sample_subtitles)
        subtitle_edit.subtitle_list.setCurrentRow(0)
        
        # Edit text
        new_text = "Updated subtitle"
        subtitle_edit.edit_panel.text_edit.setPlainText(new_text)
        qtbot.wait(100)
        
        # Edit timing
        new_start = 1.0
        new_duration = 3.0
        subtitle_edit.edit_panel.start_time.setValue(new_start)
        subtitle_edit.edit_panel.duration.setValue(new_duration)
        
        # Verify changes
        current_subtitle = subtitle_edit.get_subtitle(0)
        assert current_subtitle.text == new_text
        assert current_subtitle.start == new_start
        assert current_subtitle.duration == new_duration

    @pytest.mark.ui
    def test_validation(self, subtitle_edit, sample_subtitles, qtbot):
        """Test subtitle validation rules."""
        subtitle_edit.load_subtitles(sample_subtitles)
        subtitle_edit.subtitle_list.setCurrentRow(0)
        
        # Test minimum duration
        subtitle_edit.edit_panel.duration.setValue(MIN_DURATION - 0.1)
        assert subtitle_edit.edit_panel.duration.value() == MIN_DURATION
        
        # Test maximum duration
        subtitle_edit.edit_panel.duration.setValue(MAX_DURATION + 0.1)
        assert subtitle_edit.edit_panel.duration.value() == MAX_DURATION
        
        # Test text length validation
        long_text = "a" * (MAX_CHARS_PER_LINE + 1)
        subtitle_edit.edit_panel.text_edit.setPlainText(long_text)
        qtbot.wait(100)
        
        # Should show warning indicator
        assert subtitle_edit.edit_panel.warning_label.isVisible()

    @pytest.mark.ui
    def test_subtitle_operations(self, subtitle_edit, sample_subtitles, qtbot):
        """Test subtitle add/remove/move operations."""
        subtitle_edit.load_subtitles(sample_subtitles)
        initial_count = subtitle_edit.subtitle_list.count()
        
        # Add new subtitle
        subtitle_edit.add_subtitle()
        assert subtitle_edit.subtitle_list.count() == initial_count + 1
        
        # Remove subtitle
        subtitle_edit.subtitle_list.setCurrentRow(0)
        subtitle_edit.remove_subtitle()
        assert subtitle_edit.subtitle_list.count() == initial_count
        
        # Move subtitle
        subtitle_edit.subtitle_list.setCurrentRow(0)
        subtitle_edit.move_subtitle_down()
        first_text = subtitle_edit.get_subtitle(1).text
        assert "First" in first_text

    @pytest.mark.ui
    def test_time_adjustment(self, subtitle_edit, sample_subtitles, qtbot):
        """Test time adjustment features."""
        subtitle_edit.load_subtitles(sample_subtitles)
        
        # Test shift time
        shift_amount = 1.0
        subtitle_edit.shift_all_subtitles(shift_amount)
        
        # Verify all subtitles shifted
        for i in range(len(sample_subtitles)):
            subtitle = subtitle_edit.get_subtitle(i)
            original = sample_subtitles[i]
            assert subtitle.start == original.start + shift_amount

    @pytest.mark.ui
    def test_keyboard_shortcuts(self, subtitle_edit, sample_subtitles, qtbot):
        """Test keyboard shortcuts."""
        subtitle_edit.load_subtitles(sample_subtitles)
        subtitle_edit.subtitle_list.setCurrentRow(0)
        
        # Test delete shortcut
        with patch.object(subtitle_edit, 'remove_subtitle') as mock_remove:
            QTest.keyClick(subtitle_edit, Qt.Key_Delete)
            assert mock_remove.called
        
        # Test navigation shortcuts
        with patch.object(subtitle_edit.subtitle_list, 'setCurrentRow') as mock_select:
            QTest.keyClick(subtitle_edit, Qt.Key_Down, Qt.ControlModifier)
            assert mock_select.called

    @pytest.mark.ui
    def test_undo_redo(self, subtitle_edit, sample_subtitles, qtbot):
        """Test undo/redo functionality."""
        subtitle_edit.load_subtitles(sample_subtitles)
        subtitle_edit.subtitle_list.setCurrentRow(0)
        
        # Make a change
        original_text = subtitle_edit.get_subtitle(0).text
        new_text = "Changed text"
        subtitle_edit.edit_panel.text_edit.setPlainText(new_text)
        qtbot.wait(100)
        
        # Undo
        subtitle_edit.undo()
        assert subtitle_edit.get_subtitle(0).text == original_text
        
        # Redo
        subtitle_edit.redo()
        assert subtitle_edit.get_subtitle(0).text == new_text

    @pytest.mark.ui
    def test_file_operations(self, subtitle_edit, sample_subtitles, qtbot):
        """Test file save/load operations."""
        subtitle_edit.load_subtitles(sample_subtitles)
        
        # Mock file dialog
        with patch('PyQt5.QtWidgets.QFileDialog') as mock_dialog:
            mock_dialog.getSaveFileName.return_value = ("/path/to/save.srt", "")
            
            # Test save
            subtitle_edit.save_subtitles()
            assert mock_dialog.getSaveFileName.called
            
            # Test load
            mock_dialog.getOpenFileName.return_value = ("/path/to/load.srt", "")
            subtitle_edit.load_from_file()
            assert mock_dialog.getOpenFileName.called

    @pytest.mark.ui
    def test_drag_drop_reorder(self, subtitle_edit, sample_subtitles, qtbot):
        """Test drag and drop reordering."""
        subtitle_edit.load_subtitles(sample_subtitles)
        
        # Simulate drag and drop
        source_index = subtitle_edit.subtitle_list.indexFromItem(
            subtitle_edit.subtitle_list.item(0))
        target_index = subtitle_edit.subtitle_list.indexFromItem(
            subtitle_edit.subtitle_list.item(1))
        
        # Create mock drag event
        event = MagicMock()
        event.source.return_value = subtitle_edit.subtitle_list
        event.pos.return_value = subtitle_edit.subtitle_list.visualRect(target_index).center()
        
        subtitle_edit.subtitle_list.dropEvent(event)
        
        # Verify order changed
        assert "Second" in subtitle_edit.get_subtitle(0).text
