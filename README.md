# Edge-AI Accessibility Assistant - Developer Guide and Codebase

**Last Updated:** 2025-08-06

## 1. Project Vision and Purpose

This project is an **Edge-AI** assistant designed to help visually impaired individuals interact more independently with their physical environment. The system utilizes a standard computer's camera and microphone to perform all AI analysis locally within a virtual ARM environment, ensuring privacy and security while maintaining low-latency response times. The architecture demonstrates practical implementation of edge computing principles and AI model optimization in resource-constrained environments.

## 2. Core Architecture

The project consists of two main interacting components:

* **Host (Main Machine - Windows with WSL Ubuntu):** This is your primary computer where project files are stored. It is responsible for launching the virtual machine and interfacing with physical hardware like the webcam.
* **Guest (Virtual Machine - QEMU with Ubuntu Server ARM64):** This is an isolated virtual computer running Ubuntu Server on an ARM64 architecture. It performs all AI computations, processing data received from the Host machine.

## 3. Architecture Benefits and Design Rationale

The virtualized architecture provides several key advantages:

* **Privacy and Data Security:** All AI processing occurs locally without requiring external cloud services, ensuring sensitive visual data never leaves the user's device.
* **Reduced Latency:** Local processing eliminates network delays associated with cloud-based AI services, providing immediate feedback to users.
* **Offline Capability:** The system functions independently of internet connectivity, making it reliable in various environments.
* **Resource Isolation:** The virtual machine creates a controlled environment that simulates resource-constrained edge devices, allowing for realistic testing and optimization.
* **Scalability and Portability:** The containerized approach enables easy deployment across different hardware platforms and facilitates testing on various ARM-based systems.
* **Development Flexibility:** Virtualization enables rapid prototyping and testing without requiring physical embedded hardware during development phases.

## 4. Crucial Commands and Daily Workflow

This section outlines the essential commands for your daily project routine.

### 4.1. Starting the Virtual Machine (Powering On - Once Per Session)

This command must be run in your **Host machine's WSL (Ubuntu) terminal**, from the project's root directory. This terminal window **must remain open** as long as you are working on the project.

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

### 4.2. Attaching the Webcam to WSL (Once Per Session)

This step makes your physical webcam connected to Windows available to your WSL Ubuntu environment.

1. **Open Windows PowerShell as an Administrator.**
2. List your USB devices and identify the **BUSID** of your webcam (e.g., `2-5`):
   ```powershell
   usbipd list
   ```
3. **Bind** the webcam to make it sharable:
   ```powershell
   # Replace <BUSID> with your webcam's BUSID (e.g., 2-5)
   .\usbipd bind --busid <BUSID>
   ```
4. **Attach** the webcam to your WSL instance:
   ```powershell
   .\usbipd attach --wsl --busid <BUSID>
   ```

### 4.3. Connecting to the Virtual Machine (SSH)

After the VM is running and the webcam is attached, open a **NEW WSL (Ubuntu) terminal** and connect to the VM:

```bash
ssh ubuntu@localhost -p 2222
```

* **Password:** Use the secure password you set in the `user-data.yaml` file.
* **First-time Connection Error (`REMOTE HOST IDENTIFICATION HAS CHANGED!`)**: If you encounter this, it's normal. Run the command suggested in the error message (e.g., `ssh-keygen -f '/home/username/.ssh/known_hosts' -R '[localhost]:2222'`) to clear the old host key, then try connecting again.

### 4.4. Safely Shutting Down the Virtual Machine (Ending Your Session)

When you are done working, run this command inside the **SSH-connected terminal (`ubuntu@ubuntu:~$`)**:

```bash
sudo shutdown now
```

## 5. System Setup (Host & Guest - One-Time Installation Steps)

These steps were completed during the initial project setup and generally do not need to be repeated. They are included here for reference in case a complete re-setup is needed.

### 5.1. Host Machine (WSL) Initial Setup

```bash
# In your Ubuntu (WSL) terminal
sudo apt update
sudo apt install qemu-system-arm qemu-efi-aarch64 cloud-image-utils -y
sudo apt install linux-tools-virtual hwdata -y # usbipd client tools for WSL
# Note: usbipd-win itself is installed in Windows PowerShell:
# winget install --interactive --exact dorssel.usbipd-win
```

### 5.2. Preparing Project Files on the Host Machine

```bash
# Navigate to your project's root directory (e.g., ~/edge-ai-accessibility-assistant)
mkdir qemu_files

# Download the Ubuntu Cloud Image
wget -P ./qemu_files/ https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img

# Create the user-data.yaml file (CONTAINS PASSWORD - DO NOT COMMIT TO GIT!)
touch ./qemu_files/user-data.yaml
nano ./qemu_files/user-data.yaml
# Paste the following content, replacing 'YourSecurePassword' with your actual secure password:
#cloud-config
#user: ubuntu
#password: 'YourSecurePassword'
#chpasswd: { expire: False }
#ssh_pwauth: True

# Create the virtual CD-ROM image for user data
cloud-localds -v ./qemu_files/seed.img ./qemu_files/user-data.yaml

# Copy the Ubuntu image to create the virtual disk
cp ./qemu_files/jammy-server-cloudimg-arm64.img ./qemu_files/ubuntu_vm_disk.qcow2

# Resize the virtual disk to 20GB (can be increased to 30G/40G if more space is needed)
qemu-img resize ./qemu_files/ubuntu_vm_disk.qcow2 20G
```

### 5.3. Virtual Machine Initial Setup (Guest - Inside SSH)

```bash
# After connecting via SSH
# Verify disk size (should automatically be 20G): df -h

# Update the system
sudo apt update
sudo apt upgrade -y

# Install necessary development tools
sudo apt install python3-pip python3-venv build-essential unzip wget -y

# Install SSH server (already part of the setup, can be re-run for confirmation)
sudo apt install openssh-server -y
```

## 6. AI Development Environment and Code

### 6.1. Python Environment and Libraries

```bash
# Inside the SSH-connected terminal on the VM...
# Create and navigate to the projects folder
mkdir -p ~/projects
cd ~/projects

# Create and activate the Python virtual environment
python3 -m venv ai_assistant_env
source ai_assistant_env/bin/activate

# Install required libraries
pip install numpy Pillow tflite-runtime 
```

### 6.2. AI Model and Test Files

```bash
# (While the virtual environment is active)
# Download the test model, labels, and an example image
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v1_1.0_224_quant_and_labels.zip
unzip mobilenet_v1_1.0_224_quant_and_labels.zip
# Rename the labels file for easier access
mv labels_mobilenet_quant_v1_224.txt labels.txt
wget https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/lite/examples/python/testdata/grace_hopper.bmp
```

### 6.3. AI Server Code (`ai_server.py`)

Create this file in the VM (`nano ~/projects/ai_server.py`) and paste the following code:

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
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    # Convert incoming bytes to PIL Image and resize for the model
    image = Image.open(io.BytesIO(image_bytes)).resize((width, height))
    input_data = np.expand_dims(image, axis=0)

    # Set the tensor and invoke the interpreter for prediction
    interpreter.set_tensor(input_details[0]['index'], input_data)
    
    start_time = time.time()
    interpreter.invoke()
    stop_time = time.time()

    # Get prediction results
    output_data = interpreter.get_tensor(output_details[0]['index'])
    results = np.squeeze(output_data)
    
    # Get the top predicted label
    top_k = results.argsort()[-1:][::-1]
    top_label = f'{labels[top_k[0]]}: {results[top_k[0]] / 255.0:.2f}'
    
    print(f"Prediction: {top_label} ({stop_time - start_time:.3f}s)")
    return top_label

def main():
    print("Loading AI Model and labels...")
    labels = load_labels("labels.txt")
    interpreter = tflite.Interpreter(model_path="mobilenet_v1_1.0_224_quant.tflite")
    interpreter.allocate_tensors()
    print("Model loaded successfully.")

    HOST = '0.0.0.0'  # Listen on all network interfaces
    PORT = 12345      # Port forwarded from Host machine

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection received from: {addr}")
                
                # Receive image data in chunks
                image_data = b""
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    image_data += data
                
                # Classify and send result back
                if image_data:
                    result_text = classify_image(interpreter, image_data, labels)
                    conn.sendall(result_text.encode('utf-8'))

if __name__ == '__main__':
    main()
```

### 6.4. Camera Client Code (`camera_client.py`)

Create this file on the **Host machine** (in your main project folder) using `nano camera_client.py` and paste the following code:

```python
import cv2
import socket
import time

def main():
    HOST = 'localhost'
    PORT = 12345

    # Camera index (0 is usually default. Try 1, 2, or -1 if 0 doesn't work.)
    # Note: On some systems, 0 + cv2.CAP_V4L2 might be needed (e.g., cap = cv2.VideoCapture(0 + cv2.CAP_V4L2))
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Please ensure no other application is using the camera.")
        print("Verify 'usbipd bind' and 'usbipd attach' steps are done.")
        return

    print("Camera opened successfully. Sending frames...")

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera. Retrying...")
                # If cannot read frame, release camera and try re-opening
                cap.release()
                cap = cv2.VideoCapture(0) # Try opening again
                if not cap.isOpened():
                    print("Error: Could not re-open camera. Exiting.")
                    break
                time.sleep(1) # Give time for camera to re-initialize
                continue

            # Encode the frame into JPEG format for network transfer
            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                print("Error: Could not encode frame to JPG. Skipping frame.")
                continue
            
            # Create a network socket and connect to the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                    s.sendall(buffer)
                    s.shutdown(socket.SHUT_WR) # Signal that we are done sending

                    # Receive the classification result from the server
                    response = s.recv(1024).decode('utf-8')
                    print(f"Result from Virtual Machine: {response}")

                except ConnectionRefusedError:
                    print("Error: Connection refused. Is the ai_server.py running on the VM?")
                    time.sleep(2) # Wait before retrying connection
                    continue
                except BrokenPipeError:
                    print("Error: Broken pipe - Server disconnected. Retrying connection...")
                    time.sleep(2)
                    continue

            time.sleep(1) # Send one frame per second

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
            
    # Release the camera resource when the loop ends or on error
    cap.release()

if __name__ == '__main__':
    main()
```

### 6.5. Running the Code

1. **On the Virtual Machine (SSH-connected terminal):** Start `ai_server.py`.
   ```bash
   cd ~/projects
   source ai_assistant_env/bin/activate
   python3 ai_server.py
   ```

2. **On the Host Machine (WSL Ubuntu terminal, in your main project folder):** Start `camera_client.py`.
   ```bash
   source venv/bin/activate
   pip install opencv-python-headless  # Ensure it's installed
   python3 camera_client.py
   ```

## 7. Current Challenge: Camera `select() timeout` Error

**Error Message:** `[ WARN:0@X.XXX] global cap_v4l.cpp:1049 tryIoctl VIDEOIO(V4L2:/dev/video0): select() timeout. Error: Could not read frame.`

This indicates that the camera driver interface is experiencing timeout issues when attempting to read frame data. The fact that `fswebcam` works confirms camera accessibility through WSL, indicating the issue is specific to OpenCV's V4L2 interaction.

### **Potential Solutions (Try Systematically!)**

1. **Ensure No Other Application is Using the Camera (CRITICAL!)**: This is the most common cause. Close all applications on Windows that might use the camera (Discord, Zoom, Teams, Skype, Windows Camera App, browser tabs). A full computer reboot before starting the project is the safest approach.

2. **Refresh USBIPD Connection (Hard Reset)**:
   * In **Administrator PowerShell:**
     ```powershell
     .\usbipd detach --busid <BUSID> # If attached, detach it
     .\usbipd bind --busid <BUSID>   # Bind it again
     .\usbipd attach --wsl --busid <BUSID> # Attach it again
     ```
   * Then, try running the client in WSL again.

3. **Force Camera Index and Backend**: Modify the `cap = cv2.VideoCapture(0)` line in `camera_client.py` and try different indices or backends.
   * `cap = cv2.VideoCapture(1)`
   * `cap = cv2.VideoCapture(2)` (if you have multiple USB cameras)
   * `cap = cv2.VideoCapture(-1)` (try Windows default index)
   * `cap = cv2.VideoCapture(0 + cv2.CAP_V4L2)` (force V4L2 backend)
   * **After each change, save the file and re-run the client.**

4. **Restart WSL Services**:
   * Close all WSL Ubuntu terminal windows.
   * In Windows CMD/PowerShell: `wsl --shutdown`
   * Then, restart WSL (by simply opening a new Ubuntu terminal).
   * Repeat the `usbipd` steps (bind and attach).
   * Run the client again.

5. **Reinstall `opencv-python-headless` (as a last resort)**: Sometimes, a corrupted installation can cause this.
   * `pip uninstall opencv-python-headless -y`
   * `pip install opencv-python-headless`
   * Then re-run the client.