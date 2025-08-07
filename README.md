```markdown
# Edge-AI Accessibility Assistant: Developer Guide

**Last Updated: 2025-08-07**

## 1. Project Vision & Purpose

This project is an **Edge-AI** assistant designed to help visually impaired individuals interact more independently with their physical environment. The system utilizes a standard computer's camera to perform all AI analysis locally within a virtualized ARM environment, ensuring user privacy and low-latency responses. The architecture serves as a practical implementation of edge computing, system programming, and AI model optimization.

## 2. Core Architecture

The system consists of two primary components operating in tandem:

*   **Host (Windows + WSL2):** The primary development machine. It stores the project files, launches the virtual environment, and provides the physical webcam interface.
*   **Guest (QEMU + Ubuntu Server ARM64):** An isolated, virtualized ARM64 environment. It performs all intensive AI computations, processing the video stream received from the host.

## 3. Architecture Benefits and Design Rationale

The virtualized architecture provides several key advantages:

*   **Privacy and Data Security:** All AI processing occurs locally without requiring external cloud services, ensuring sensitive visual data never leaves the user's device.
*   **Reduced Latency:** Local processing eliminates network delays associated with cloud-based AI services, providing immediate feedback to users.
*   **Offline Capability:** The system functions independently of internet connectivity, making it reliable in various environments.
*   **Resource Isolation:** The virtual machine creates a controlled environment that simulates resource-constrained edge devices, allowing for realistic testing and optimization.
*   **Scalability and Portability:** The containerized approach enables easy deployment across different hardware platforms and facilitates testing on various ARM-based systems.
*   **Development Flexibility:** Virtualization enables rapid prototyping and testing without requiring physical embedded hardware during development phases.

## 4. Daily Workflow & Essential Commands

Follow these steps for a typical development session.

### 4.1. Start the Virtual Machine (Once per session)

From your project's root directory in a **WSL terminal**, execute the following. Keep this terminal open.

```bash
qemu-system-aarch64 \
  -M virt \
  -cpu cortex-a53 \
  -m 2G \
  -smp 4 \
  -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
  -drive if=virtio,file=./qemu_files/ubuntu_vm_disk.qcow2,format=qcow2 \
  -drive if=virtio,file=./qemu_files/seed.img,format=raw \
  -device virtio-net-pci,netdev=net0 \
  -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::12345-:12345 \
  -nographic
```

### 4.2. Attach the Webcam to WSL (Once per session)

1.  Open **Windows PowerShell as Administrator**.
2.  Find your webcam's **BUSID** (e.g., `2-5`):
    ```powershell
    usbipd list
    ```
3.  Bind and attach the device to WSL:
    ```powershell
    # Use the BUSID you identified above
    usbipd bind --busid <BUSID>
    usbipd attach --wsl --busid <BUSID>
    ```

### 4.3. Connect to the Virtual Machine via SSH

Open a **new WSL terminal** and connect to the running guest VM.

```bash
ssh ubuntu@localhost -p 2222
```
*(Password is the one set in your `user-data.yaml` file.)*

### 4.4. Run the AI Server

Inside the **SSH-connected terminal**, navigate to the projects directory, activate the environment, and start the AI server.

```bash
cd ~/projects
source ai_assistant_env/bin/activate
python3 ai_server.py
```
*(The server will print `Server is listening...` and wait for connections.)*

### 4.5. Run the Camera Client

Open a **third WSL terminal** on your host machine, navigate to the project's root directory, and start the camera client.

```bash
# Make sure you are in the project's root directory
python3 camera_client.py
```
*(You should now see classification results printed in this terminal.)*

### 4.6. Safely Shutdown the VM

When finished, run this command **inside the SSH-connected terminal**:

```bash
sudo shutdown now
```

## 5. Code & Environment

### 5.1. AI Server (`ai_server.py` on Guest)

This file must be created inside the Guest VM (e.g., using `nano ~/projects/ai_server.py`). It contains the logic for receiving images and performing AI classification.

```python
import socket
import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite
import time
import io

def load_labels(filename):
    """Loads labels from a text file."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f.readlines()]

def classify_image(interpreter, image_bytes, labels):
    """Classifies the incoming image data and returns the result as text."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    height = input_details['shape']
    width = input_details['shape']

    image = Image.open(io.BytesIO(image_bytes)).resize((width, height))
    input_data = np.expand_dims(image, axis=0)

    interpreter.set_tensor(input_details['index'], input_data)
    
    start_time = time.time()
    interpreter.invoke()
    stop_time = time.time()

    output_data = interpreter.get_tensor(output_details['index'])
    results = np.squeeze(output_data)
    
    top_k = results.argsort()[-1:][::-1]
    
    top_label_index = top_k
    top_label = f'{labels[top_label_index]}: {results[top_label_index] / 255.0:.2f}'
    
    print(f"Prediction: {top_label} ({stop_time - start_time:.3f}s)")
    return top_label

def main():
    print("Loading AI Model and labels...")
    labels = load_labels("labels.txt")
    interpreter = tflite.Interpreter(model_path="mobilenet_v1_1.0_224_quant.tflite")
    interpreter.allocate_tensors()
    print("Model loaded successfully.")

    HOST = '0.0.0.0'
    PORT = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection received from: {addr}")
                
                image_data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    image_data += chunk
                
                if image_data:
                    result_text = classify_image(interpreter, image_data, labels)
                    conn.sendall(result_text.encode('utf-8'))

if __name__ == '__main__':
    main()
```

### 5.2. Camera Client (`camera_client.py` on Host)

This file is located in the project's root directory. It is responsible for capturing video from the webcam, setting the stable MJPEG format, and sending frames to the AI server.

```python
import cv2
import socket
import time

def main():
    HOST = 'localhost'
    PORT = 12345
    cap = cv2.VideoCapture(0)
    
    # Set MJPEG format to prevent camera timeout errors
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    if not cap.isOpened():
        print("Error: Could not open camera. Check if it is used by another application.")
        return

    print("Camera opened successfully. Sending frames to the server...")

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera. Retrying...")
                time.sleep(1)
                continue

            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                print("Error: Could not encode frame to JPG. Skipping.")
                continue
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                    s.sendall(buffer.tobytes())
                    response = s.recv(1024).decode('utf-8')
                    print(f"Result from Virtual Machine: {response}")

                except ConnectionRefusedError:
                    print("Error: Connection refused. Is the ai_server.py running on the VM?")
                    time.sleep(2)
                except Exception as e:
                    print(f"Socket Error: {e}")
                    time.sleep(2)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
            
    print("Releasing camera resource.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
```

## 6. Troubleshooting & Critical Fixes

### 6.1. Critical Fix: `usbipd` Connection Fails or Freezes

*   **Symptoms:** The `usbipd attach` command fails with a `firewall` or `tcp connect` error, or it freezes without any output.
*   **Permanent Solution:** Change WSL's networking mode to be more compatible. This is a one-time setup.
    1.  Create a `.wslconfig` file in your Windows user profile folder (`%UserProfile%`). From **CMD** or **PowerShell**:
        ```cmd
        echo [wsl2] > %UserProfile%\.wslconfig
        echo networkingMode=mirrored >> %UserProfile%\.wslconfig
        ```
    2.  Shutdown WSL completely to apply the change. In **PowerShell** or **CMD**:
        ```powershell
        wsl --shutdown
        ```
    3.  The next time WSL starts, it will use the new networking mode, resolving the issue.

### 6.2. Critical Fix: OpenCV `select() timeout` Error

*   **Symptom:** The client prints "Error: Could not read frame from camera."
*   **Primary Solution:** The line `cap.set(cv2.CAP_PROP_FOURCC, ...)` in the `camera_client.py` file is designed to prevent this.
*   **Secondary Causes:**
    *   **Camera in Use:** Ensure no other application (Zoom, Teams, etc.) is using the camera. A system reboot is the most reliable way to ensure this.
    *   **Incorrect Index:** Try changing `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` if you have multiple cameras.
```