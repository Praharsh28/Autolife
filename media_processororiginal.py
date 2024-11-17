import sys
import os
import subprocess
import warnings
import gc
import re
import torch
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import requests
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit,
    QVBoxLayout, QWidget, QFileDialog, QLabel, QListWidget,
    QMessageBox, QHBoxLayout, QAbstractItemView, QProgressBar,
    QInputDialog, QStyleFactory, QSpinBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QCursor
from PyQt5.QtCore import QSize
import time

# Suppress FP16 warning for Whisper
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super(FileListWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.addItem(file_path)
        else:
            event.ignore()


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    file_completed = pyqtSignal(str, int)  # Modified to include progress value


class SubtitleWorker(QThread):
    def __init__(self, files, batch_size=3):
        super().__init__()
        self.files = files
        self.batch_size = batch_size
        self.signals = WorkerSignals()
        self.API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
        self.API_TOKEN = "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"
        
        # Constants for subtitle formatting
        self.MAX_CHARS_PER_LINE = 37  # Netflix standard
        self.MIN_DURATION = 1.0       # Minimum duration in seconds
        self.MAX_DURATION = 7.0       # Maximum duration in seconds
        self.CHARS_PER_SECOND = 20    # Reading speed (characters per second)
        
        # Setup logging
        self.logger = logging.getLogger('SubtitleWorker')
        self.logger.setLevel(logging.DEBUG)
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        log_file = os.path.join('logs', f'subtitle_worker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def segment_line(self, text):
        """
        Segment a line of text according to professional subtitle standards.
        Based on Netflix and BBC subtitle guidelines.
        """
        words = text.split()
        if not words:
            return []

        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            space_length = 1 if current_line else 0
            
            # Check if adding this word exceeds line length
            if current_length + word_length + space_length > self.MAX_CHARS_PER_LINE:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is longer than max length, need to hyphenate
                    if word_length > self.MAX_CHARS_PER_LINE:
                        split_point = self.MAX_CHARS_PER_LINE - 1
                        lines.append(word[:split_point] + '-')
                        current_line = [word[split_point:]]
                        current_length = len(current_line[0])
                    else:
                        current_line = [word]
                        current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length + space_length

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def process_segments(self, segments):
        """
        Process segments according to professional subtitle standards.
        Following Netflix, BBC, and EBU subtitle timing guidelines.
        """
        processed_segments = []
        
        for segment in segments:
            if isinstance(segment, dict):
                text = segment.get('text', '').strip()
                start_time = segment.get('start', 0)
                end_time = segment.get('end', start_time + 5)
                
                if not text:
                    continue

                # Split text into sentences
                sentences = re.split(r'([.!?]+)', text)
                sentences = [s.strip() for s in sentences if s.strip()]

                current_time = start_time
                for i in range(0, len(sentences), 2):
                    sentence = sentences[i]
                    punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                    full_sentence = sentence + punctuation

                    # Split long sentences into lines
                    lines = self.segment_line(full_sentence)
                    
                    if not lines:
                        continue

                    # Calculate optimal duration based on content length
                    total_chars = sum(len(line) for line in lines)
                    optimal_duration = total_chars / self.CHARS_PER_SECOND

                    # Apply duration constraints
                    duration = min(max(optimal_duration, self.MIN_DURATION), self.MAX_DURATION)
                    
                    # Add extra time for line breaks and punctuation
                    if len(lines) > 1:
                        duration *= 1.1  # 10% extra for multiple lines
                    if any(p in punctuation for p in '!?'):
                        duration *= 1.2  # 20% extra for strong punctuation

                    # Ensure we don't exceed total segment duration
                    if current_time + duration > end_time:
                        duration = end_time - current_time

                    processed_segments.append({
                        'text': '\n'.join(lines),
                        'start': current_time,
                        'end': current_time + duration
                    })
                    
                    current_time += duration

            elif isinstance(segment, str):
                lines = self.segment_line(segment)
                if not lines:
                    continue

                total_chars = sum(len(line) for line in lines)
                duration = min(max(total_chars / self.CHARS_PER_SECOND, self.MIN_DURATION), self.MAX_DURATION)

                processed_segments.append({
                    'text': '\n'.join(lines),
                    'start': 0,
                    'end': duration
                })

        return processed_segments

    def process_generate_subtitles(self, file_name):
        temp_file = None
        try:
            # Set up detailed logging for this file
            self.logger.info("="*50)
            self.logger.info(f"Starting new transcription job for: {file_name}")
            self.logger.info(f"Input file details:")
            self.logger.info(f"- Path: {os.path.abspath(file_name)}")
            self.logger.info(f"- Size: {os.path.getsize(file_name)/1024/1024:.2f} MB")
            self.logger.info(f"- Exists: {os.path.exists(file_name)}")
            self.signals.log.emit(f"Processing {file_name}")

            # Generate a unique temp file name
            temp_file = f"temp_converted_{os.path.basename(file_name)}_{datetime.now().strftime('%H%M%S')}.wav"
            self.logger.info(f"Temporary file will be: {temp_file}")
            
            # First, check input file
            if not os.path.exists(file_name):
                raise Exception(f"Input file does not exist: {file_name}")
            
            # Get input file format info
            probe_command = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'stream=codec_name,codec_type,sample_rate,channels',
                '-of', 'json',
                file_name
            ]
            
            self.logger.info("Probing input file format...")
            probe_result = subprocess.run(probe_command, capture_output=True, text=True)
            if probe_result.returncode == 0:
                self.logger.info(f"Input file format: {probe_result.stdout}")
            else:
                self.logger.warning(f"Failed to probe input file: {probe_result.stderr}")
            
            # Convert to WAV with very strict settings
            ffmpeg_command = [
                'ffmpeg',
                '-v', 'warning',  # Set verbosity level
                '-i', file_name,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sampling rate (required by Whisper)
                '-ac', '1',  # Mono audio (required by Whisper)
                '-f', 'wav',  # Force WAV format
                '-bitexact',  # Ensure exact format
                '-y',  # Overwrite output
                temp_file
            ]
            
            self.logger.info("Converting audio file...")
            self.logger.info(f"FFmpeg command: {' '.join(ffmpeg_command)}")
            
            conversion_result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
            
            if conversion_result.returncode != 0:
                error_msg = (
                    f"FFmpeg conversion failed with return code {conversion_result.returncode}\n"
                    f"Error output: {conversion_result.stderr}\n"
                    f"Standard output: {conversion_result.stdout}"
                )
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            self.logger.info("Audio conversion completed")

            # Verify the converted file
            if not os.path.exists(temp_file):
                raise Exception(f"Conversion failed: Output file not created: {temp_file}")

            # Verify converted file format
            verify_command = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,channels,sample_rate,bits_per_sample',
                '-of', 'json',
                temp_file
            ]
            
            self.logger.info("Verifying converted audio format...")
            verify_result = subprocess.run(verify_command, capture_output=True, text=True)
            if verify_result.returncode == 0:
                self.logger.info(f"Converted file format: {verify_result.stdout}")
            else:
                self.logger.error(f"Failed to verify converted file: {verify_result.stderr}")

            # Check file size
            file_size = os.path.getsize(temp_file)
            self.logger.info(f"Converted file size: {file_size/1024/1024:.2f} MB")
            max_size = 25 * 1024 * 1024
            
            if file_size > max_size:
                raise Exception(f"File size ({file_size/1024/1024:.2f} MB) exceeds 25MB limit")

            # Read file content for debugging
            with open(temp_file, 'rb') as f:
                header = f.read(44)  # Read WAV header
                self.logger.debug(f"WAV header (hex): {header.hex()}")

            # API call with detailed logging
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Attempt {attempt + 1}/{max_retries} to call Whisper API")
                    
                    headers = {
                        "Authorization": f"Bearer {self.API_TOKEN}",
                        "Content-Type": "audio/wav"
                    }
                    
                    self.logger.debug(f"Request headers: {headers}")
                    
                    with open(temp_file, "rb") as audio_file:
                        audio_data = audio_file.read()
                        self.logger.info(f"Sending {len(audio_data)} bytes to API")
                        
                        response = requests.post(
                            self.API_URL,
                            headers=headers,
                            data=audio_data,
                            timeout=300
                        )
                        
                        self.logger.info(f"API Response Status: {response.status_code}")
                        self.logger.debug(f"API Response Headers: {dict(response.headers)}")
                        
                        if response.status_code == 503:
                            self.logger.warning("Model is loading...")
                            if attempt < max_retries - 1:
                                self.logger.info(f"Waiting {retry_delay} seconds before retry")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                        
                        try:
                            self.logger.debug(f"Raw API Response: {response.text[:1000]}...")
                            result = response.json()
                            
                            if isinstance(result, dict) and "error" in result:
                                error_msg = f"API Error Response: {result}"
                                self.logger.error(error_msg)
                                if "Malformed soundfile" in str(result):
                                    self.logger.error("Audio format error detected - checking file details:")
                                    # Additional file format checks
                                    with open(temp_file, 'rb') as f:
                                        wav_header = f.read(44)
                                        self.logger.error(f"WAV Header: {wav_header.hex()}")
                                raise Exception(f"API Error: {result['error']}")
                            
                            self.logger.info("Successfully received valid API response")
                            self.logger.debug(f"API Response Content: {result}")
                            break
                            
                        except ValueError as e:
                            error_msg = (
                                f"Failed to parse API response as JSON\n"
                                f"Error: {str(e)}\n"
                                f"Response Text: {response.text[:1000]}..."
                            )
                            self.logger.error(error_msg)
                            raise Exception(error_msg)
                            
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Request failed: {str(e)}")
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    raise Exception(f"API request failed after {max_retries} attempts: {str(e)}")

            # Write SRT file
            srt_file_path = os.path.splitext(file_name)[0] + ".srt"
            self.logger.info(f"Writing SRT file: {srt_file_path}")
            
            with open(srt_file_path, "w", encoding="utf-8") as srt_file:
                # Handle the new Whisper-large-v3-turbo response format
                if isinstance(result, dict):
                    if "text" in result:
                        # Single text response - create one segment
                        duration = self.get_audio_duration(temp_file)
                        segments = [{"start": 0, "end": duration, "text": result["text"]}]
                    elif "chunks" in result:
                        segments = result["chunks"]
                    elif "segments" in result:
                        segments = result["segments"]
                    else:
                        error_msg = f"Unexpected response format. Response: {result}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                elif isinstance(result, list):
                    segments = result
                else:
                    error_msg = f"Unknown response type: {type(result)}. Response: {result}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

                if not segments:
                    error_msg = "No segments found in the API response"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

                self.logger.debug(f"Processing {len(segments)} segments")
                processed_segments = self.process_segments(segments)
                
                for i, segment in enumerate(processed_segments, start=1):
                    start_time = self.format_timestamp(segment['start'])
                    end_time = self.format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    if not text:  # Skip empty segments
                        continue
                        
                    srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

            self.logger.info(f"Successfully created SRT file: {srt_file_path}")
            self.signals.log.emit(f"Subtitles saved to {srt_file_path}")
            self.signals.file_completed.emit(file_name, 100)

        except Exception as e:
            error_msg = f"Failed to process {file_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
        finally:
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temporary file {temp_file}: {str(e)}")

    def get_audio_duration(self, file_path):
        """Get the duration of an audio file using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0
        except Exception as e:
            self.logger.warning(f"Failed to get audio duration: {str(e)}")
            return 0

    def run(self):
        try:
            self.logger.info("Starting batch processing of files")
            # Process files in batches
            with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                futures = []
                for file_path in self.files:
                    self.logger.debug(f"Submitting file for processing: {file_path}")
                    future = executor.submit(
                        self.process_generate_subtitles,
                        file_path
                    )
                    futures.append((file_path, future))
                
                completed = 0
                total_files = len(self.files)
                
                for file_path, future in futures:
                    try:
                        future.result()
                        completed += 1
                        progress = (completed / total_files) * 100
                        self.signals.progress.emit(int(progress))
                        self.signals.file_completed.emit(file_path, 100)  # Add progress value
                        self.logger.info(f"Successfully processed file: {file_path}")
                        
                    except Exception as e:
                        error_msg = f"Error processing {file_path}: {str(e)}"
                        self.logger.error(error_msg)
                        self.signals.error.emit(error_msg)
            
            self.logger.info("Processing completed")
            self.signals.log.emit("Processing completed.")
            self.signals.finished.emit()
            
        except Exception as e:
            error_msg = f"Critical error in processing: {str(e)}"
            self.logger.critical(error_msg)
            self.signals.error.emit(error_msg)

    @staticmethod
    def format_timestamp(seconds):
        """Format timestamp for SRT file"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


class SrtToAssWorker(QThread):
    def __init__(self, files, ass_template_path, style_name):
        super().__init__()
        self.files = files
        self.ass_template_path = ass_template_path
        self.style_name = style_name
        self.signals = WorkerSignals()

        # Setup logging
        self.logger = logging.getLogger('SrtToAssWorker')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create file handler
        log_file = os.path.join('logs', f'srt_to_ass_worker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(fh)

    def run(self):
        try:
            self.logger.info("Starting batch processing of files")
            total_files = len(self.files)
            for index, srt_path in enumerate(self.files):
                if srt_path.lower().endswith('.srt'):
                    ass_path = os.path.splitext(srt_path)[0] + ".ass"
                    self.process_srt_to_ass(srt_path, ass_path)
                    progress = int((index + 1) / total_files * 100)
                    self.signals.progress.emit(progress)
                else:
                    self.signals.log.emit(f"Skipping {srt_path}: Not an SRT file.")
            self.signals.finished.emit()
        except Exception as e:
            error_msg = f"Critical error in processing: {str(e)}"
            self.logger.critical(error_msg)
            self.signals.error.emit(error_msg)

    def process_srt_to_ass(self, srt_path, ass_path):
        self.logger.info(f"Converting {srt_path} to ASS using style '{self.style_name}'...")
        header = []
        events = []
        with open(self.ass_template_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Build the header, including styles
        in_events = False
        for line in lines:
            if line.strip() == "[Events]":
                in_events = True
                header.append(line)
                header.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                break
            else:
                header.append(line)

        # Read the SRT file
        with open(srt_path, 'r', encoding='utf-8') as srt_file:
            srt_content = srt_file.read()

        pattern = re.compile(
            r'(\d+)\s+(\d{2}:\d{2}:\d{2}[,\.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,\.]\d{3})\s+(.*?)\s*(?=\d+\s+\d{2}|\Z)',
            re.DOTALL)
        matches = pattern.findall(srt_content)

        for match in matches:
            index, start_time, end_time, text = match
            start_time = start_time.replace(',', '.')
            end_time = end_time.replace(',', '.')
            text = text.replace('\n', '\\N')
            dialogue_line = f"Dialogue: 0,{start_time},{end_time},{self.style_name},,0,0,0,,{text}"
            events.append(dialogue_line)

        with open(ass_path, 'w', encoding='utf-8') as ass_file:
            ass_file.writelines(header)
            ass_file.write('\n'.join(events))

        self.logger.info(f"Converted {srt_path} to {ass_path}")
        self.signals.log.emit(f"Converted {srt_path} to {ass_path}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize instance variables
        self.button_convert_audio = QPushButton("Generate Subtitles")
        self.button_srt_to_ass = QPushButton("Convert SRT to ASS")
        self.button_mxf_to_mp4 = QPushButton("Convert MXF to MP4")
        self.button_overlay_subtitles = QPushButton("Overlay Subtitles")
        self.button_mp4_to_mxf = QPushButton("Convert MP4 to MXF")
        self.progress_bar = QProgressBar()
        self.status_display = QTextEdit()
        self.batch_size_spinner = QSpinBox()
        self.delete_original_checkbox = QCheckBox("Delete original files after conversion")
        self.file_progress = {}

        self.setWindowTitle("Media Processing Application")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        # Apply modern style
        self.setStyle(QStyleFactory.create('Fusion'))
        self.apply_dark_theme()
        
        # Enhanced UI Layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add title and description
        title = QLabel("Media Processing Suite")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        description = QLabel("Process your media files with automatic subtitles and conversions")
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)

        # File handling section
        file_section = QGroupBox("File Management")
        file_layout = QVBoxLayout()

        # Enhanced file list
        self.file_list = FileListWidget()
        self.file_list.setMinimumHeight(200)
        self.file_list.setStyleSheet("""\
            QListWidget {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #2980b9;
                color: white;
            }
        """)
        file_layout.addWidget(self.file_list)

        # Enhanced buttons
        button_style = """\
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                background-color: #2980b9;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """

        buttons_layout = QHBoxLayout()
        self.button_add_files = QPushButton("Add Files")
        self.button_add_files.setStyleSheet(button_style)
        self.button_add_files.setToolTip("Click to add media files for processing")
        
        self.button_remove_selected = QPushButton("Remove Selected")
        self.button_remove_selected.setStyleSheet(button_style)
        buttons_layout.addWidget(self.button_add_files)
        buttons_layout.addWidget(self.button_remove_selected)
        file_layout.addLayout(buttons_layout)
        file_section.setLayout(file_layout)
        main_layout.addWidget(file_section)

        # Processing section
        process_section = QGroupBox("Processing Steps")
        process_layout = QVBoxLayout()

        # Enhanced processing buttons with progress indicators
        for btn in [self.button_convert_audio, self.button_srt_to_ass, 
                   self.button_mxf_to_mp4, self.button_overlay_subtitles, 
                   self.button_mp4_to_mxf]:
            btn.setStyleSheet(button_style)
            btn.setMinimumHeight(40)
            process_layout.addWidget(btn)

        process_section.setLayout(process_layout)
        main_layout.addWidget(process_section)

        # Connect button signals
        self.button_add_files.clicked.connect(self.add_files)
        self.button_remove_selected.clicked.connect(self.remove_selected_files)
        self.button_convert_audio.clicked.connect(self.generate_subtitles)
        self.button_srt_to_ass.clicked.connect(self.convert_srt_to_ass)
        self.button_mxf_to_mp4.clicked.connect(self.convert_mxf_to_mp4)
        self.button_overlay_subtitles.clicked.connect(self.overlay_subtitles)
        self.button_mp4_to_mxf.clicked.connect(self.convert_mp4_to_mxf)

        # Enhanced progress bar
        self.progress_bar.setStyleSheet("""\
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Enhanced status display
        self.status_display.setStyleSheet("""\
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.status_display.setMaximumHeight(150)
        main_layout.addWidget(self.status_display)

        # Settings section
        settings_section = QGroupBox("Processing Settings")
        settings_layout = QHBoxLayout()
        
        self.batch_size_spinner.setStyleSheet("""\
            QSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        """)
        self.batch_size_spinner.setToolTip("Number of files to process simultaneously")
        
        self.delete_original_checkbox.setStyleSheet("""\
            QCheckBox {
                spacing: 5px;
            }
        """)
        settings_layout.addWidget(self.batch_size_spinner)
        settings_layout.addWidget(self.delete_original_checkbox)
        
        settings_section.setLayout(settings_layout)
        main_layout.addWidget(settings_section)

        # Set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

    def update_file_progress(self, filename, progress):
        self.file_progress[filename] = progress
        total_progress = sum(self.file_progress.values()) / len(self.file_progress)
        self.progress_bar.setValue(int(total_progress))
        self.log(f"Progress for {filename}: {progress}%")

    def add_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*)", options=options)
        if files:
            for file_path in files:
                self.file_list.addItem(file_path)

    def remove_selected_files(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.log("No files selected to remove.")
            return
        for item in selected_items:
            self.file_list.takeItem(self.file_list.row(item))
        self.log("Selected files removed from the list.")

    def log(self, message):
        self.status_display.append(message)
        # Auto-scroll to the bottom
        self.status_display.verticalScrollBar().setValue(self.status_display.verticalScrollBar().maximum())

    # Function to generate subtitles using Whisper in a separate thread
    def generate_subtitles(self):
        if self.file_list.count() == 0:
            self.log("No files to process.")
            return

        # Disable the button to prevent multiple clicks
        self.button_convert_audio.setEnabled(False)

        # Collect file paths
        files = [self.file_list.item(index).text() for index in range(self.file_list.count())]

        # Create and start the worker thread
        self.worker = SubtitleWorker(files)
        self.worker.signals.log.connect(self.log)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.error.connect(self.handle_error_generate_subtitles)
        self.worker.signals.finished.connect(self.processing_finished_generate_subtitles)
        self.worker.signals.file_completed.connect(self.update_file_progress)
        self.worker.start()

    def handle_error_generate_subtitles(self, error_message):
        self.log(f"An error occurred during subtitle generation: {error_message}")
        self.button_convert_audio.setEnabled(True)

    def processing_finished_generate_subtitles(self):
        self.log("Subtitle generation completed.")
        self.progress_bar.setValue(100)
        self.button_convert_audio.setEnabled(True)

    def convert_srt_to_ass(self):
        if self.file_list.count() == 0:
            self.log("No files to process.")
            return

        # Prompt for the ASS template file
        ass_template_path, _ = QFileDialog.getOpenFileName(self, "Select ASS Template File", "", "ASS Files (*.ass)")
        if not ass_template_path:
            self.log("No ASS template file selected.")
            return

        # Read the styles from the template
        styles = self.read_ass_styles(ass_template_path)
        if not styles:
            self.log("No styles found in the ASS template file.")
            return

        # Prompt user to select a style
        style_name, ok = self.get_style_choice(styles)
        if not ok or not style_name:
            self.log("No style selected.")
            return

        # Collect file paths
        files = [self.file_list.item(index).text() for index in range(self.file_list.count())]

        # Disable the button to prevent multiple clicks
        self.button_srt_to_ass.setEnabled(False)

        # Create and start the worker thread
        self.worker = SrtToAssWorker(files, ass_template_path, style_name)
        self.worker.signals.log.connect(self.log)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.error.connect(self.handle_error_srt_to_ass)
        self.worker.signals.finished.connect(self.processing_finished_srt_to_ass)
        self.worker.start()

    def handle_error_srt_to_ass(self, error_message):
        self.log(f"An error occurred during SRT to ASS conversion: {error_message}")
        self.button_srt_to_ass.setEnabled(True)

    def processing_finished_srt_to_ass(self):
        self.log("SRT to ASS conversion completed.")
        self.progress_bar.setValue(100)
        self.button_srt_to_ass.setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def get_style_choice(self, styles):
        """Prompt the user to select a style from the styles dictionary."""
        items = list(styles.keys())
        style_choice, ok = QInputDialog.getItem(self, "Select Style", "Choose a style for the subtitles:", items, 0, False)
        return style_choice, ok

    def read_ass_styles(self, ass_template_path):
        """Read the styles from the ASS template file."""
        styles = {}
        with open(ass_template_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        styles_section = False
        for line in lines:
            if line.strip() == "[V4+ Styles]":
                styles_section = True
                continue
            if styles_section:
                if line.strip() == "":
                    continue
                if line.startswith("Format:"):
                    continue
                elif line.startswith("Style:"):
                    style_line = line.strip()
                    style_name = style_line.split(",")[0].split(":")[1].strip()
                    styles[style_name] = style_line
                elif line.startswith("[Events]"):
                    break
        return styles

    # Function to convert MXF to MP4
    def convert_mxf_to_mp4(self):
        if self.file_list.count() == 0:
            self.log("No files to process.")
            return

        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            if file_path.lower().endswith('.mxf'):
                self.process_convert_mxf_to_mp4(file_path)
            else:
                self.log(f"Skipping {file_path}: Not an MXF file.")

    def process_convert_mxf_to_mp4(self, input_path):
        output_path = os.path.splitext(input_path)[0] + ".mp4"

        command = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            output_path, "-y"
        ]

        self.log(f"Converting {input_path} to MP4...")
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Conversion complete: {output_path}")

        # Delete the original .mxf file after conversion
        if os.path.exists(output_path):
            os.remove(input_path)
            self.log(f"Deleted original file: {input_path}")

    # Function to overlay subtitles onto video
    def overlay_subtitles(self):
        if self.file_list.count() == 0:
            self.log("No files to process.")
            return

        for index in range(self.file_list.count()):
            video_path = self.file_list.item(index).text()
            if video_path.lower().endswith('.mp4'):
                subtitle_path = os.path.splitext(video_path)[0] + ".ass"
                if os.path.isfile(subtitle_path):
                    self.process_overlay_subtitles(video_path, subtitle_path)
                else:
                    self.log(f"No subtitle file found for {video_path}. Skipping.")
            else:
                self.log(f"Skipping {video_path}: Not an MP4 file.")

    def process_overlay_subtitles(self, video_path, subtitle_path):
        # Prepare the subtitle path for FFmpeg
        subtitle_path_ffmpeg = subtitle_path.replace('\\', '/').replace(':', '\\:')

        subtitle_filter = f"subtitles='{subtitle_path_ffmpeg}'"

        temp_output_path = video_path + "_temp.mp4"

        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'copy',
            temp_output_path, '-y'
        ]

        try:
            self.log(f'Overlaying subtitles onto {video_path}...')
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.replace(temp_output_path, video_path)
            self.log(f"Successfully overlaid subtitles on {video_path}.")
        except subprocess.CalledProcessError as e:
            self.log(f"Error overlaying subtitles on {video_path}: {e}")
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")

    # Function to convert MP4 to MXF
    def convert_mp4_to_mxf(self):
        if self.file_list.count() == 0:
            self.log("No files to process.")
            return

        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            if file_path.lower().endswith('.mp4'):
                self.process_convert_mp4_to_mxf(file_path)
            else:
                self.log(f"Skipping {file_path}: Not an MP4 file.")

    def process_convert_mp4_to_mxf(self, input_path):
        output_path = os.path.splitext(input_path)[0] + ".mxf"

        command = [
            "ffmpeg", "-i", input_path,
            "-c:v", "mpeg2video", "-qscale:v", "2", "-c:a", "pcm_s16le",
            output_path, "-y"
        ]

        self.log(f"Converting {input_path} to MXF...")
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Conversion complete: {output_path}")

        # Delete the original .mp4 file after conversion
        if os.path.exists(output_path):
            os.remove(input_path)
            self.log(f"Deleted original file: {input_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
