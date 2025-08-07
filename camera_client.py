import cv2
import socket
import time

def main():
    HOST = 'localhost'
    PORT = 12345

    # Select camera index 0 (the default camera).
    cap = cv2.VideoCapture(0)

    # --- HIGH-LEVEL SOLUTION ---
    # Set the camera's video format to MJPEG.
    # This is highly effective at preventing select() timeout errors on many webcams.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    # Check if the camera was successfully opened.
    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Please ensure no other application is using the camera.")
        print("Also, verify that the 'usbipd bind' and 'usbipd attach' steps were completed.")
        return

    print("Camera opened successfully. Sending frames to the server...")

    while True:
        try:
            # Read a single, instantaneous frame from the camera.
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera. Retrying...")
                time.sleep(1) # Wait a moment before trying again.
                continue

            # Encode the frame into the JPEG format to compress it for network transfer.
            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                print("Error: Could not encode frame to JPG. Skipping this frame.")
                continue
            
            # Create a new socket for each frame and connect to the server.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                    s.sendall(buffer.tobytes()) # Send the compressed image data.
                    s.shutdown(socket.SHUT_WR) # Signal the server that we are done sending.

                    # Receive the classification result from the server and print it.
                    response = s.recv(1024).decode('utf-8')
                    print(f"Result from Virtual Machine: {response}")

                except ConnectionRefusedError:
                    print("Error: Connection refused. Is the ai_server.py running on the VM?")
                    time.sleep(2) # Wait 2 seconds before retrying.
                    continue
                except BrokenPipeError:
                    print("Error: Broken pipe. Did the server disconnect? Retrying...")
                    time.sleep(2)
                    continue

            # Wait for 1 second to send about one frame per second.
            time.sleep(1)

        except KeyboardInterrupt:
            # If the user presses CTRL+C to stop the program...
            print("Program terminated by user.")
            break
        except Exception as e:
            # For any other unexpected errors...
            print(f"An unexpected error occurred: {e}")
            break
            
    # When the loop ends or an error occurs, release the camera resource.
    print("Releasing camera resource.")
    cap.release()

if __name__ == '__main__':
    main()