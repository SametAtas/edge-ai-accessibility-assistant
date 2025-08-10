import socket, cv2, time, json, config
from multiprocessing import Process, freeze_support
import numpy as np

# CRITICAL: This must match your model's expected input size!
# Your server shows "Expected input shape: [1 640 640 3]"
MODEL_INPUT_SIZE = (640, 640)

def speak_text(text: str):
    """Initializes TTS in a separate process to speak text non-blockingly."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        if config.OUTPUT_LANGUAGE == 'tr':
            try:
                voices = engine.getProperty('voices')
                for voice in voices:
                    if 'turkish' in voice.name.lower(): engine.setProperty('voice', voice.id); break
            except Exception: pass
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[TTS Process Error] {e}")

def get_prediction(frame: np.ndarray) -> dict | None:
    """Encodes a frame, sends it to the server, and returns the parsed JSON response."""
    # FIXED: Now using the correct model input size
    frame_resized = cv2.resize(frame, MODEL_INPUT_SIZE)
    ret, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY])
    if not ret:
        print("Error: Failed to encode frame.")
        return None

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(config.CLIENT_SOCKET_TIMEOUT)
            s.connect((config.CLIENT_CONNECT_HOST, config.SERVER_PORT))
            s.sendall(buffer.tobytes())
            s.shutdown(socket.SHUT_WR) # CRITICAL: Signals the server we are done sending.

            response_data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            if not response_data:
                print("Error: Received empty response from server.")
                return None
                
            return json.loads(response_data.decode('utf-8'))
    except socket.timeout:
        print("Error: Connection timed out.")
        return None
    except ConnectionRefusedError:
        print("Error: Connection refused. Is the server running?")
        return None
    except Exception as e:
        print(f"Network error: {e}")
        return None

def main():
    """Main client loop for real-time detection and feedback."""
    print("Starting Camera Client...")
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"FATAL: Cannot access camera at index {config.CAMERA_INDEX}.")
        return
    
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("Camera initialized. Press Ctrl+C to stop.")
    
    last_spoken_message = ""
    tts_process = None
    last_speech_time = 0
    
    try:
        while True:
            if tts_process and not tts_process.is_alive():
                tts_process.join(); tts_process = None
            
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame."); time.sleep(0.5); continue
            
            response = get_prediction(frame)
            
            if response and response.get('success'):
                message = response.get('message', '')
                object_count = response.get('object_count', 0)
                print(f"[AI]: {message}")
                
                current_time = time.time()
                time_since_last_speech = current_time - last_speech_time
                
                # IMPROVED: Should speak if message is different (regardless of object count)
                # This allows "I can't see anything" to be spoken too
                should_speak = (message != last_spoken_message and
                                time_since_last_speech > config.SPEECH_COOLDOWN and
                                tts_process is None)
                
                # Debug info to understand what's happening
                if not should_speak:
                    if message == last_spoken_message:
                        print(f">>> Skipping: Same message as before")
                    elif time_since_last_speech <= config.SPEECH_COOLDOWN:
                        print(f">>> Skipping: Cooldown active ({time_since_last_speech:.1f}s < {config.SPEECH_COOLDOWN}s)")
                    elif tts_process is not None:
                        print(f">>> Skipping: TTS already running")
                
                if should_speak:
                    print(">>> Speaking new message...")
                    last_spoken_message = message
                    last_speech_time = current_time
                    tts_process = Process(target=speak_text, args=(message,))
                    tts_process.start()
                
                # NOTE: We no longer reset last_spoken_message when object_count == 0
                # because "I can't see anything" is also a valid message to remember
            
            # This small delay prevents the CPU from running at 100% constantly.
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        if tts_process and tts_process.is_alive(): tts_process.terminate(); tts_process.join()
        cap.release()
        cv2.destroyAllWindows()
        print("Client stopped.")

if __name__ == '__main__':
    freeze_support()
    main()