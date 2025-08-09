import cv2
import socket
import time
import pyttsx3
import config
from multiprocessing import Process

def speak_in_separate_process(text_to_speak):
    """
    This function runs in a completely separate process.
    It initializes the TTS engine, speaks the text, and then terminates.
    This prevents it from freezing the main application.
    """
    try:
        engine = pyttsx3.init()
        engine.say(text_to_speak)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        # This error will be printed in the console but won't crash the main app
        print(f"[TTS Process Error] {e}")

def setup_camera():
    """
    Initializes the camera using the index specified in the config.
    """
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"ERROR: Could not open camera at index {config.CAMERA_INDEX}.")
        print("Check if the camera is connected and not used by another application.")
        return None
    print("Camera opened successfully.")
    return cap

def get_prediction_from_server(frame):
    """
    Sends a video frame to the AI server and retrieves the classification result.
    """
    is_success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not is_success:
        print("ERROR: Could not encode frame to JPG format.")
        return None

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(config.CLIENT_SOCKET_TIMEOUT)
            s.connect((config.CLIENT_CONNECT_HOST, config.SERVER_PORT))
            s.sendall(buffer.tobytes())
            s.shutdown(socket.SHUT_WR)
            response = s.recv(1024).decode('utf-8')
            return response
    except socket.timeout:
        print(f"ERROR: Connection timed out after {config.CLIENT_SOCKET_TIMEOUT} seconds.")
        return None
    except ConnectionRefusedError:
        print("ERROR: Connection refused. Is the ai_server.py running on the VM?")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected network error occurred: {e}")
        return None

def main():
    """
    The main orchestration function for the client application.
    It captures frames, sends them for prediction, and speaks the results.
    """
    cap = setup_camera()
    if not cap:
        return

    last_spoken_text = ""
    tts_process = None  # Track the speech process
    
    print("\nStarting main loop... Press Ctrl+C in the terminal to exit.")
    print(f"Connecting to AI server at {config.CLIENT_CONNECT_HOST}:{config.SERVER_PORT}")
    
    while True:
        try:
            # Check if the previous speech process has finished
            if tts_process and not tts_process.is_alive():
                tts_process.join()  # Clean up resources
                tts_process = None

            ret, frame = cap.read()
            if not ret:
                print("ERROR: Could not read frame from camera. Retrying...")
                time.sleep(1)
                continue

            prediction = get_prediction_from_server(frame)

            # If we have a new prediction AND no speech process is currently running
            if prediction and prediction != last_spoken_text and (tts_process is None):
                print(f"Server Response: \"{prediction}\" -> Speaking.")
                last_spoken_text = prediction
                
                # Start the speech job in a separate process
                tts_process = Process(target=speak_in_separate_process, args=(prediction,))
                tts_process.start()
            elif prediction:
                # Show the prediction but don't speak if it's the same
                print(f"Server Response: \"{prediction}\" (same as before, not speaking)")
            
            time.sleep(config.CLIENT_LOOP_DELAY)

        except KeyboardInterrupt:
            print("\nShutdown signal received. Exiting...")
            if tts_process and tts_process.is_alive():
                tts_process.terminate()  # Terminate speech if exiting
                tts_process.join(timeout=1)  # Wait up to 1 second for clean exit
            break
        except Exception as e:
            print(f"FATAL: An unexpected error occurred in the main loop: {e}")
            break
            
    print("Releasing resources...")
    cap.release()

# CRITICAL: This block is required for Windows multiprocessing
if __name__ == '__main__':
    # Freeze support for Windows executable creation
    from multiprocessing import freeze_support
    freeze_support()
    main()