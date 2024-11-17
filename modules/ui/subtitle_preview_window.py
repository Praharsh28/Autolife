from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont

import cv2
import numpy as np

class VideoFrame(QLabel):
    """Custom widget for displaying video frame with subtitle overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        
        # Subtitle properties
        self.subtitle_text = ""
        self.subtitle_style = "Normal"
        self.subtitle_color = "White"
        self.subtitle_position = "Bottom"
        
    def set_frame(self, frame):
        """Set video frame from numpy array."""
        if frame is None:
            return
            
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QPixmap from numpy array
        pixmap = QPixmap.fromImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )
        
        # Scale pixmap to fit label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        
    def set_subtitle(self, text: str, style: str = None,
                    color: str = None, position: str = None):
        """Set subtitle text and properties."""
        self.subtitle_text = text
        if style:
            self.subtitle_style = style
        if color:
            self.subtitle_color = color
        if position:
            self.subtitle_position = position
        self.update()
        
    def paintEvent(self, event):
        """Override paint event to draw subtitle overlay."""
        super().paintEvent(event)
        if not self.subtitle_text:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Set font
        font = QFont()
        font.setPointSize(12)
        if self.subtitle_style == "Bold":
            font.setBold(True)
        elif self.subtitle_style == "Italic":
            font.setItalic(True)
        painter.setFont(font)
        
        # Set color
        color = QColor(self.subtitle_color)
        painter.setPen(color)
        
        # Calculate text position
        text_rect = painter.boundingRect(
            self.rect(),
            Qt.AlignHCenter,
            self.subtitle_text
        )
        
        if self.subtitle_position == "Bottom":
            y = self.height() - text_rect.height() - 20
        elif self.subtitle_position == "Top":
            y = 20
        else:  # Middle
            y = (self.height() - text_rect.height()) // 2
            
        text_rect.moveTop(y)
        text_rect.moveLeft((self.width() - text_rect.width()) // 2)
        
        # Draw text shadow for better visibility
        shadow_color = QColor(0, 0, 0, 160)
        painter.setPen(shadow_color)
        painter.drawText(text_rect.adjusted(1, 1, 1, 1), Qt.AlignCenter, self.subtitle_text)
        
        # Draw main text
        painter.setPen(color)
        painter.drawText(text_rect, Qt.AlignCenter, self.subtitle_text)

class SubtitlePreviewWindow(QDialog):
    """Window for previewing subtitle changes with video frame."""
    
    def __init__(self, video_path: str, frame_time: float,
                 subtitle: dict, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.frame_time = frame_time
        self.subtitle = subtitle
        self.setup_ui()
        self.load_frame()
        
    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Subtitle Preview")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Video frame with subtitle overlay
        self.frame_view = VideoFrame()
        layout.addWidget(self.frame_view)
        
        # Time slider
        slider_layout = QHBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(-2000, 2000)  # ±2 seconds
        self.time_slider.setValue(0)
        self.time_slider.valueChanged.connect(self.on_time_changed)
        
        slider_layout.addWidget(QLabel("-2s"))
        slider_layout.addWidget(self.time_slider)
        slider_layout.addWidget(QLabel("+2s"))
        
        layout.addLayout(slider_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.toggled.connect(self.toggle_playback)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.play_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Setup playback timer
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.next_frame)
        
    def load_frame(self):
        """Load video frame at current time."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return
            
        # Seek to frame
        target_time = self.frame_time + (self.time_slider.value() / 1000.0)
        cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
        
        # Read frame
        ret, frame = cap.read()
        if ret:
            self.frame_view.set_frame(frame)
            
        cap.release()
        
        # Update subtitle
        self.frame_view.set_subtitle(
            self.subtitle['text'],
            self.subtitle.get('style'),
            self.subtitle.get('color'),
            self.subtitle.get('position')
        )
        
    def on_time_changed(self):
        """Handle time slider change."""
        self.load_frame()
        
    def toggle_playback(self, playing: bool):
        """Toggle preview playback."""
        if playing:
            self.play_timer.start(33)  # ~30 fps
            self.play_btn.setText("Pause")
        else:
            self.play_timer.stop()
            self.play_btn.setText("Play")
        
    def next_frame(self):
        """Load next frame during playback."""
        current_value = self.time_slider.value()
        if current_value >= 2000:
            self.play_btn.setChecked(False)
            return
            
        self.time_slider.setValue(current_value + 33)  # Move ~1 frame forward
        
    def closeEvent(self, event):
        """Handle window close."""
        self.play_timer.stop()
        super().closeEvent(event)
