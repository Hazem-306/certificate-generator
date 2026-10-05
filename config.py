"""
Application configuration and constants.
"""
from pathlib import Path
import sys

APP_NAME = "Certificates Generator"
APP_VERSION = "1.1"

def get_base_dir():
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
IMAGES_DIR = BASE_DIR / "images"

PRIMARY_RED = "#E50000"
DEFAULT_FONT = "Helvetica"
DEFAULT_FONT_SIZE = 20

# UI Configuration
SIDEBAR_RATIO = 15
MAIN_WINDOW_RATIO = 85
FONT_SCALE_MULTIPLIER = 1.5
