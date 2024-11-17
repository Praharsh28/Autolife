# AutoLife Media Processing Application

## Version 1.0.0 - Stable Release

A powerful media processing application with advanced subtitle generation capabilities using state-of-the-art AI models.

### Key Features
- Automatic subtitle generation using Hugging Face's Whisper Large V3 Turbo model
- Semantic text segmentation for natural subtitle breaks
- Multi-format support (WAV, MP4)
- Intuitive PyQt5-based user interface
- Robust error handling and logging
- Parallel processing support

## Continuous Integration Status
[![AutoLife Tests](https://github.com/{YOUR_USERNAME}/autolife/actions/workflows/test.yml/badge.svg)](https://github.com/{YOUR_USERNAME}/autolife/actions)
[![codecov](https://codecov.io/gh/{YOUR_USERNAME}/autolife/branch/main/graph/badge.svg)](https://codecov.io/gh/{YOUR_USERNAME}/autolife)

## Requirements
- Python 3.11 or higher
- FFmpeg installed and in system PATH
- Hugging Face API token (set in .env file)

## Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -e .
```
3. Create a `.env` file with your Hugging Face API token:
```
HUGGINGFACE_API_TOKEN=your_token_here
```

## Usage
Run the application:
```bash
python main.py
```

## Automated Testing
This project uses GitHub Actions for continuous integration and automated testing. Tests are run:
- On every push to `main` and `develop` branches
- On every pull request to these branches
- Every 6 hours automatically

### Test Reports
After each test run, you can find:
1. HTML test reports
2. Code coverage reports
3. Detailed test logs

These are available in the "Actions" tab of the GitHub repository under each workflow run.

### Local Development
To run tests locally:
```bash
pytest -v -n auto --dist=loadscope -m "not gpu"
```

## License
MIT License
