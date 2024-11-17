"""
Constants used throughout the media processing application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
TEMPLATES_DIR = os.path.join(RESOURCES_DIR, 'templates')
DEFAULT_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, 'default_template.ass')

# Application directories
APP_DIR = os.path.dirname(os.path.dirname(__file__))
RESOURCES_DIR = os.path.join(APP_DIR, 'resources')
TEMPLATES_DIR = os.path.join(RESOURCES_DIR, 'templates')
LOGS_DIR = os.path.join(RESOURCES_DIR, 'logs')
TEST_FILES_DIR = os.path.join(APP_DIR, 'test_files')

# API Configuration
API_BASE_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
if not API_TOKEN:
    raise ValueError("HUGGINGFACE_API_TOKEN not found. Please set it in your .env file")

# Network Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Initial retry delay in seconds
MAX_RETRY_DELAY = 32.0  # Maximum retry delay in seconds
JITTER_RANGE = 0.1  # ±10% jitter
REQUEST_TIMEOUT = 30  # Request timeout in seconds
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}  # HTTP status codes that trigger retry

# File Size Limits
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB maximum file size

# Subtitle Formatting
MAX_LINE_LENGTH = 42  # Maximum characters per line
MIN_LINE_LENGTH = 20  # Minimum characters per line
MAX_SUBTITLE_DURATION = 7.0  # Maximum duration for a subtitle in seconds
MIN_SUBTITLE_DURATION = 1.0  # Minimum duration for a subtitle in seconds
CHARS_PER_SECOND = 20  # Average reading speed (characters per second)

# UI Theme
DARK_THEME = {
    # Base Colors
    'background': '#1E1E1E',           # Dark gray background
    'text': '#E8E8E8',                 # Light gray text
    
    # Button Colors
    'button': '#2D2D2D',               # Slightly lighter gray for buttons
    'button_text': '#FFFFFF',          # White text for buttons
    'button_hover': '#3D3D3D',         # Even lighter gray for button hover
    'button_pressed': '#4D4D4D',       # Lightest gray for button press
    
    # List Colors
    'list_background': '#252526',      # Dark gray for list backgrounds
    'list_alternate': '#2D2D2D',       # Slightly lighter for alternating items
    
    # Progress Colors
    'progress': '#007ACC',             # Blue for progress bars
    'progress_bar': '#007ACC',         # Blue for progress bar
    'progress_background': '#252526',  # Dark background for progress bar
    
    # Group Box Colors
    'group_box': '#252526',           # Background for group boxes
    'group_box_border': '#3D3D3D',    # Border for group boxes
    'group_box_title': '#E8E8E8',     # Title text for group boxes
    
    # Status Colors
    'status_background': '#252526',    # Background for status text
    'status_text': '#E8E8E8',         # Color for status text
    
    # Highlight Colors
    'highlight': '#007ACC',            # Blue for highlighted/selected items
    'highlight_text': '#FFFFFF',       # White text for highlighted items
    
    # Border Colors
    'border': '#3D3D3D',              # Border color for UI elements
    
    # State Colors
    'error': '#FF6B6B',               # Red for errors
    'success': '#4CAF50',             # Green for success
    'warning': '#FFA726',             # Orange for warnings
    'info': '#29B6F6',                # Light blue for info
}

# UI Styles
BUTTON_STYLE = """
    QPushButton {
        background-color: %(button)s;
        color: %(button_text)s;
        border: 2px solid %(border)s;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: %(button_hover)s;
    }
    QPushButton:pressed {
        background-color: %(button_pressed)s;
    }
    QPushButton:disabled {
        background-color: #1A1A1A;
        color: #666666;
    }
""" % DARK_THEME

PROGRESS_BAR_STYLE = """
    QProgressBar {
        border: 2px solid %(button)s;
        border-radius: 5px;
        text-align: center;
        color: %(text)s;
        background-color: %(progress_background)s;
    }
    QProgressBar::chunk {
        background-color: %(progress_bar)s;
        width: 10px;
        margin: 0.5px;
    }
""" % DARK_THEME

LIST_WIDGET_STYLE = """
    QListWidget {
        background-color: %(list_background)s;
        color: %(text)s;
        border: 2px solid %(border)s;
        border-radius: 5px;
        padding: 5px;
    }
    QListWidget::item {
        padding: 5px;
        border-radius: 3px;
    }
    QListWidget::item:selected {
        background-color: %(highlight)s;
        color: %(highlight_text)s;
    }
    QListWidget::item:hover {
        background-color: %(button)s;
    }
    QListWidget::item:alternate {
        background-color: %(list_alternate)s;
    }
""" % DARK_THEME

LABEL_STYLE = """
    QLabel {
        color: %(text)s;
        font-size: 14px;
    }
""" % DARK_THEME

ERROR_LABEL_STYLE = """
    QLabel {
        color: %(error)s;
        font-size: 14px;
        font-weight: bold;
    }
""" % DARK_THEME

SUCCESS_LABEL_STYLE = """
    QLabel {
        color: %(success)s;
        font-size: 14px;
        font-weight: bold;
    }
""" % DARK_THEME

GROUP_BOX_STYLE = """
    QGroupBox {
        background-color: %(group_box)s;
        border: 2px solid %(group_box_border)s;
        border-radius: 5px;
        padding: 5px;
    }
    QGroupBox::title {
        color: %(text)s;
        font-size: 14px;
    }
""" % DARK_THEME

# Window Configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Autolife Subtitle Generator"
WINDOW_GEOMETRY = (100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)  # (x, y, width, height)

# Thread pool settings
MIN_WORKERS = 2
MAX_WORKERS = 8
WORKER_TIMEOUT = 300  # 5 minutes worker timeout

# Resource Management
MAX_MEMORY_PERCENT = 80.0  # Maximum memory usage as percentage of system memory
MAX_CONCURRENT_TASKS = 3   # Maximum number of concurrent processing tasks
MEMORY_CHECK_INTERVAL = 1.0  # Seconds between memory checks
CLEANUP_DELAY = 5.0  # Seconds to wait before cleaning up temporary files

# Disk Management
MIN_FREE_SPACE_BYTES = 1024 * 1024 * 1024  # 1GB minimum free space
TEMP_DIR_CLEANUP_THRESHOLD = 85.0  # Clean temp files when disk usage exceeds 85%
TEMP_FILE_MAX_AGE = 3600 * 24  # 24 hours maximum temp file age
DISK_CHECK_INTERVAL = 300  # Check disk space every 5 minutes

# Cache Configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
CACHE_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB maximum cache size
CACHE_MAX_AGE = 7 * 24 * 3600  # 7 days maximum cache age
CACHE_CLEANUP_INTERVAL = 3600  # Cleanup every hour
CACHE_MIN_FREE_SPACE = 1024 * 1024 * 1024  # 1GB minimum free space

# FFmpeg Configuration
FFMPEG_TIMEOUT = 3600  # 1 hour maximum process time
FFMPEG_FORMATS = {
    'wav': 'Waveform Audio',
    'mp3': 'MP3 Audio',
    'aac': 'AAC Audio',
    'flac': 'FLAC Audio',
    'ogg': 'OGG Vorbis'
}
FFMPEG_COMMAND_TEMPLATES = {
    'wav': '-acodec pcm_s16le -ar 16000 -ac 1',  # 16-bit PCM, 16kHz, mono
    'mp3': '-codec:a libmp3lame -qscale:a 2',    # High quality MP3
    'aac': '-codec:a aac -b:a 192k',             # High quality AAC
    'flac': '-codec:a flac',                      # Lossless FLAC
    'ogg': '-codec:a libvorbis -qscale:a 6'      # High quality Vorbis
}

# Language Configuration
SUPPORTED_LANGUAGES = {
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi"
}
DEFAULT_LANGUAGE = "English"

# Language Codes
LANGUAGE_CODES = {
    'eng': 'en', 'spa': 'es', 'fra': 'fr', 'deu': 'de',
    'ita': 'it', 'por': 'pt', 'nld': 'nl', 'pol': 'pl',
    'rus': 'ru', 'ukr': 'uk', 'ara': 'ar', 'hin': 'hi',
    'ben': 'bn', 'zho': 'zh', 'jpn': 'ja', 'kor': 'ko'
}

LANGUAGE_DIRECTIONS = {
    'ar': 'rtl',  # Arabic
    'he': 'rtl',  # Hebrew
    'fa': 'rtl',  # Persian
    'ur': 'rtl'   # Urdu
}

LANGUAGE_MODELS = {
    ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
    ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
    ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
    ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
    ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
    ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
    ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
    ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
    'default': 'facebook/m2m100_418M'  # Fallback for unsupported pairs
}

PUNCTUATION_RULES = {
    'en': {
        'patterns': {
            r'\s+': ' ',  # Normalize whitespace
            r'\.{3,}': '...',  # Normalize ellipsis
            r'["\']([^"\']*)["\']': r'"\1"',  # Normalize quotes
            r'\s*([.,!?;:])\s*': r'\1 ',  # Fix punctuation spacing
        }
    },
    'zh': {
        'patterns': {
            r'\s+': '',  # Remove spaces between Chinese characters
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'「\1」',  # Chinese quotes
            r'([。，！？；：])': r'\1',  # No space after Chinese punctuation
        }
    },
    'ja': {
        'patterns': {
            r'\s+': '',
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'「\1」',
            r'([。、！？；：])': r'\1',
        }
    },
    'ar': {
        'patterns': {
            r'\s+': ' ',
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'"\1"',
            r'\s*([.،!؟;:])\s*': r'\1 ',
        }
    }
}

SUBTITLE_RULES = {
    'en': {
        'max_chars_per_line': 42,
        'min_chars_per_line': 20,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 20
    },
    'zh': {
        'max_chars_per_line': 30,  # Chinese characters need more space
        'min_chars_per_line': 15,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 15
    },
    'ja': {
        'max_chars_per_line': 30,
        'min_chars_per_line': 15,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 15
    },
    'ar': {
        'max_chars_per_line': 50,  # Arabic script is more compact
        'min_chars_per_line': 25,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 25
    }
}

# Media formats
SUPPORTED_VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'wmv']
SUPPORTED_AUDIO_FORMATS = ['mp3', 'wav', 'aac', 'm4a', 'flac']

# File Extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
SUBTITLE_EXTENSIONS = {'.srt', '.vtt', '.sub', '.ass'}

# Progress Updates
PROGRESS_UPDATE_INTERVAL = 100  # Milliseconds between progress updates
