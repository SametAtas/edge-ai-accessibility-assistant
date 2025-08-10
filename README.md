# Edge-AI Accessibility Assistant: Developer Guide

**Last Updated: 2025-08-10**

## 1. Project Vision & Purpose

This project is an **Edge-AI** assistant designed to help visually impaired individuals interact more independently with their physical environment. The system utilizes a standard computer's camera to perform all AI analysis locally within a virtualized ARM environment, ensuring user privacy and low-latency responses.

## 2. Core Architecture

The system consists of two primary components operating in a decoupled architecture for maximum stability:

- **Host (Windows):** The primary user-facing environment. It runs the `camera_client.py` script, managing the physical camera, user-facing logic, and Text-to-Speech output.
- **Guest (QEMU + Ubuntu Server on WSL2):** An isolated, virtualized ARM64 environment. It runs `ai_server.py`, performing all intensive AI computations without direct access to host hardware, ensuring stability and portability.

---

## 3. Environment Setup

### 3.1. One-Time WSL Configuration (For QEMU Networking)

This fix is recommended for ensuring stable network communication between the host and the QEMU VM. Apply this once:

1.  Create or edit the `.wslconfig` file in your Windows user profile (`%UserProfile%`):

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

1.  **Navigate to your project folder inside WSL.**
2.  **Create Python Virtual Environment (inside VM via SSH):**
    ```shell
    python3 -m venv ai_assistant_env
    source ai_assistant_env/bin/activate
    ```
3.  **Install Dependencies:**
    ```shell
    pip install -r requirements-vm.txt
    ```
    *Note: `requirements-vm.txt` should contain `tflite-runtime`, `numpy`, and `Pillow`.*

### 3.3. Host (Windows) Client Setup

1.  **Install Python on Windows** from the Microsoft Store or `python.org` (ensure "Add Python to PATH" is checked).
2.  **Create Python Virtual Environment (in project root):**
    ```powershell
    # In a Windows PowerShell terminal, from the project's root directory
    python -m venv win_env
    .\win_env\Scripts\Activate.ps1
    ```
3.  **Install Dependencies:**
    ```powershell
    pip install -r requirements-windows.txt
    ```
    *Note: `requirements-windows.txt` should contain `opencv-python` and `pyttsx3`.*

---

## 4. Daily Workflow & Commands

### **Terminal 1 (WSL): Start AI Server**

1.  **Launch the QEMU Virtual Machine:**
    ```shell
    # This command launches the VM. Keep this terminal open.
    # Ensure file paths to disk and BIOS are correct.
    qemu-system-aarch64 \
      -M virt \
      -cpu cortex-a53 \
      -m 2G \
      -smp 4 \
      -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
      -drive if=virtio,file=./qemu_files/ubuntu_vm_disk.qcow2 \
      -device virtio-net-pci,netdev=net0 \
      -netdev user,id=net0,hostfwd=tcp::12345-:12345 \
      -nographic
    ```
2.  **Connect to VM and Start Server:** Open a **second WSL terminal** and run:
    ```shell
    # Connect to the running VM via SSH
    ssh ubuntu@localhost -p 2222

    # Once inside, navigate to your project, activate the environment,
    # and start the AI server.
    cd path/to/your/project
    source ai_assistant_env/bin/activate
    python3 ai_server.py
    ```

### **Terminal 2 (Windows PowerShell): Start Camera Client**

1.  Open a **Windows PowerShell** terminal in your project's root directory.
2.  **Activate the Windows Virtual Environment:**
    ```powershell
    .\win_env\Scripts\Activate.ps1
    ```
3.  **Run the Camera Client:**
    ```powershell
    python camera_client.py
    ```