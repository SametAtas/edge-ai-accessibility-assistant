# --- SERVER SETTINGS (VM Side) ---
# The host address the AI server will bind to inside the VM.
# '0.0.0.0' makes it listen on all available network interfaces within the VM.
SERVER_BIND_HOST = '0.0.0.0'

# --- CLIENT SETTINGS (Host Side) ---
# The address the client will connect to. Since we're using QEMU port forwarding,
# the client connects to localhost, and QEMU forwards the connection to the VM.
CLIENT_CONNECT_HOST = 'localhost'

# The port number used by both server and client.
# Must match the port in QEMU's hostfwd configuration.
SERVER_PORT = 12345

# --- AI MODEL SETTINGS ---
# Path to the TensorFlow Lite model file inside the Guest VM.
AI_MODEL_FILE = 'mobilenet_v1_1.0_224_quant.tflite'

# Path to the labels file corresponding to the model, inside the Guest VM.
AI_LABELS_FILE = 'labels.txt'

# The minimum confidence score (from 0.0 to 1.0) required to consider a
# prediction valid. Prevents the assistant from announcing low-certainty guesses.
AI_CONFIDENCE_THRESHOLD = 0.5

# --- CAMERA SETTINGS ---
# The index of the camera to be used by OpenCV.
# 0 is usually the default built-in webcam. If you have multiple cameras,
# you might need to change this to 1, 2, etc.
CAMERA_INDEX = 0

# The delay in seconds between capturing frames in the main client loop.
# Prevents overwhelming the server and reduces CPU usage.
CLIENT_LOOP_DELAY = 1.0

# Maximum time in seconds the client will wait for a server response
# before giving up. Prevents the client from freezing indefinitely.
CLIENT_SOCKET_TIMEOUT = 5.0