# Edge-AI Accessibility Assistant: Developer Guide

**Last Updated: 2025-08-08**

## 1. Project Vision & Purpose

This project is an **Edge-AI** assistant designed to help visually impaired individuals interact more independently with their physical environment. The system utilizes a standard computer's camera to perform all AI analysis locally within a virtualized ARM environment, ensuring user privacy and low-latency responses.

## 2. Core Architecture

The system consists of two primary components operating in tandem:

*   **Host (Windows + WSL2):** The primary development machine. It manages the user interface (camera, audio), project files, and launches the virtual environment.
*   **Guest (QEMU + Ubuntu Server ARM64):** An isolated, virtualized ARM64 environment that performs all intensive AI computations.

---

## 3. Environment Setup

### 3.1. One-Time WSL Configuration

**Critical Fix: Enable WSL Networking**
Apply this fix once to resolve common `pip install` freezing and connectivity issues:

1.  Create or edit the `.wslconfig` file in your Windows user profile:
    ```powershell
    # In Windows PowerShell/CMD
    echo [wsl2] > %UserProfile%\.wslconfig
    echo networkingMode=mirrored >> %UserProfile%\.wslconfig
    ```

2.  Shutdown WSL completely to apply changes:
    ```powershell
    wsl --shutdown
    ```

### 3.2. Guest VM (AI Server) Setup

The Guest VM runs the `ai_server.py`. Ensure a Python virtual environment (`ai_assistant_env`) is set up inside the VM with required packages:
*   `numpy`
*   `Pillow`
*   `tflite_runtime`

### 3.3. Host (WSL) Client Setup

The Host runs the `camera_client.py`. This setup is critical for audio output.

**1. Install System-Level Audio Dependencies**
```bash
sudo apt update && sudo apt install espeak-ng alsa-utils libasound2-plugins
```

**2. Configure WSL Audio (`.asoundrc`)**
Create the audio configuration file in the WSL home directory:
```bash
nano ~/.asoundrc
```

Paste this content:
```
pcm.!default {
    type pulse
    server /mnt/wslg/PulseServer
}

ctl.!default {
    type pulse
    server /mnt/wslg/PulseServer
}
```

**3. Create Python Virtual Environment**
```bash
# From project root directory
python3 -m venv client_env
```

**4. Install Python Dependencies**
```bash
# Activate environment
source client_env/bin/activate

# Install required packages
pip install pyttsx3 opencv-python numpy
```

---

## 4. Project Status & Next Steps

### **Current Status: Phase 2 Complete**

The system can now "see" via camera and "speak" the results using Text-to-Speech.

**Completed Features:**
*   Enhanced AI Response: Human-readable sentences with confidence thresholding.
*   Audio Output Integration: Text-to-Speech with anti-repetition logic.
*   Stable Architecture: Robust WSL-QEMU communication.

### **Next Steps: Phase 3 - Interactive Assistant**

*   **In Progress:** Voice Command Input (Wake-word detection and Speech-to-Text).
*   **To Do:** Main Application Controller (Orchestrate the listen → process → respond loop).

---

## 5. Daily Workflow & Commands

### Quick Start Checklist:
1.  Start QEMU VM
2.  Attach webcam via usbipd
3.  SSH into VM and run AI server
4.  Run camera client on host

**Terminal 1: Start Virtual Machine**
```bash
# From project root directory
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

**Windows PowerShell: Attach Webcam**
```powershell
# Run as Administrator
usbipd list                              # Find camera BUSID
usbipd bind --busid <BUSID>              # Bind device
usbipd attach --wsl --busid <BUSID>      # Attach to WSL
```

**Terminal 2: AI Server**
```bash
# Connect to VM
ssh ubuntu@localhost -p 2222

# Start AI server
source ~/projects/ai_assistant_env/bin/activate
python3 ~/projects/ai_server.py```

**Terminal 3: Camera Client**
```bash
# Activate client environment
source client_env/bin/activate

# Run camera client
python3 camera_client.py
```

---

## 6. Code Implementation

### 6.1. AI Server (`ai_server.py` on Guest VM)
```python
import socket, numpy as np, time, io
from PIL import Image
import tflite_runtime.interpreter as tflite

def load_labels(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f.readlines()]

def classify_image(interpreter, image_bytes, labels):
    # Retrieve input and output tensor details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Correctly access shape details from the first input tensor
    height = input_details['shape']
    width = input_details['shape']

    # Resize image to model input dimensions
    image = Image.open(io.BytesIO(image_bytes)).resize((width, height))
    input_data = np.expand_dims(image, axis=0)

    # Set input tensor and run inference
    interpreter.set_tensor(input_details['index'], input_data)
    
    start_time = time.time()
    interpreter.invoke()
    stop_time = time.time()

    # Get output tensor results
    output_data = interpreter.get_tensor(output_details['index'])
    results = np.squeeze(output_data)
    
    # Get top prediction index and confidence
    top_k_index = results.argsort()[-1]
    confidence = results[top_k_index] / 255.0
    confidence_threshold = 0.5

    # Generate human-readable response
    if confidence > confidence_threshold:
        object_name = labels[top_k_index]
        readable_result = f"I see a {object_name}."
    else:
        readable_result = "I'm not sure what I see."

    print(f"Prediction: {readable_result} (Confidence: {confidence:.2f})")
    return readable_result

def main():
    try:
        labels = load_labels("labels.txt")
        interpreter = tflite.Interpreter(model_path="mobilenet_v1_1.0_224_quant.tflite")
        interpreter.allocate_tensors()
        print("Model loaded. Server is listening on 0.0.0.0:12345...")
    except FileNotFoundError as e:
        print(f"Error loading model or labels: {e}")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 12345))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                # Receive image data
                image_data = b"".join(iter(lambda: conn.recv(4096), b""))
                if image_data:
                    result_text = classify_image(interpreter, image_data, labels)
                    conn.sendall(result_text.encode('utf-8'))

if __name__ == '__main__':
    main()
```

### 6.2. Camera Client (`camera_client.py` on Host WSL)
This script is responsible for capturing video, sending frames to the AI server, and speaking the results. The code is maintained in the `camera_client.py` file within the repository.

---

## 7. Troubleshooting

### Common Issues & Solutions

**`pip install` Freezes or Times Out**
- **Cause:** WSL networking configuration.
- **Solution:** Apply the `.wslconfig` fix described in Section 3.1.

**No Audio Output in WSL**
- **Symptoms:** Errors mentioning `aplay`, `ALSA`, `cannot find card '0'`, or `pulse`.
- **Solution:** Complete all steps in Section 3.3 regarding audio setup.

**Camera Not Detected**
- **Symptoms:** `Could not open camera` error.
- **Solutions:** 
  - Ensure the camera is attached via `usbipd`.
  - Try a different camera index (e.g., `CAMERA_INDEX = 1`).
  - Close other applications that may be using the camera.

**Connection Refused Errors**
- **Cause:** AI server is not running or is using a different port.
- **Solution:** Verify the AI server is running and shows "Server is listening...".