# config.py
#
# Central configuration file for the Edge-AI Accessibility Assistant.
# All operational parameters are managed from here for easy tuning.

# --- SERVER & NETWORK SETTINGS ---
SERVER_BIND_HOST: str = '0.0.0.0'
CLIENT_CONNECT_HOST: str = 'localhost'
SERVER_PORT: int = 12345

# --- AI MODEL SETTINGS ---
# NOTE: '1.tflite' provides the best balance of speed
# and accuracy for the emulated ARM environment.
AI_MODEL_FILE: str = '1.tflite'
AI_LABELS_FILE: str = 'coco_labels.txt'

# Minimum confidence score (0.0 to 1.0) for a detection to be considered valid.
AI_CONFIDENCE_THRESHOLD: float = 0.45

# --- SPATIAL POSITIONING SETTINGS ---
# X-axis thresholds (0.0=left, 1.0=right) for location descriptions.
LEFT_THRESHOLD: float = 0.35
RIGHT_THRESHOLD: float = 0.65

# --- CLIENT-SIDE SETTINGS ---
CAMERA_INDEX: int = 0
CLIENT_SOCKET_TIMEOUT: float = 15.0  # Seconds to wait for a network response.

# --- PERFORMANCE & UX (User Experience) SETTINGS ---
# JPEG quality for network transfer (1-100).
JPEG_QUALITY: int = 85

# 'tr' for Turkish, 'en' for English.
OUTPUT_LANGUAGE: str = 'en'

# Max number of objects to describe in one sentence to avoid long responses.
MAX_OBJECTS_TO_DESCRIBE: int = 3

# IMPROVED: Shorter cooldown for better responsiveness
# Minimum seconds between speech announcements to prevent chatty behavior.
SPEECH_COOLDOWN: float = 1.5  # Reduced from 2.0 to 1.5 seconds