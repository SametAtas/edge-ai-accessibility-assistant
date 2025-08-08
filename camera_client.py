import cv2
import socket
import time
import numpy as np
import pyttsx3

HOST = 'localhost'
PORT = 12345
CAMERA_INDEX = 0

def main():
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 160)
    except Exception as e:
        print(f"ERROR: Could not initialize TTS engine: {e}")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    print("Camera opened successfully. Sending frames...")
    print("(Press Ctrl+C to quit)")

    # --- NEW: Variable to remember the last spoken text ---
    last_spoken_text = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            time.sleep(1)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error: Could not encode frame.")
            continue

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((HOST, PORT))
                s.sendall(buffer.tobytes())
                s.shutdown(socket.SHUT_WR)

                response = s.recv(1024).decode('utf-8')

                if response:
                    print(f"AI Says: {response}")

                    # --- NEW LOGIC: Only speak if the message is new ---
                    if response != last_spoken_text:
                        tts_engine.say(response)
                        tts_engine.runAndWait()
                        last_spoken_text = response # Remember what was just said
                    # --- END NEW LOGIC ---

        except Exception as e:
            # This will catch connection errors and others
            print(f"An error occurred: {e}")
            time.sleep(2)

if __name__ == '__main__':
    main()