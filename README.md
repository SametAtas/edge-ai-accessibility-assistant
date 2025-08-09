# Edge-AI Accessibility Assistant: Developer Guide

**Last Updated: 2025-08-09**

## 1. Project Vision & Purpose

This project is an **Edge-AI** assistant designed to help visually impaired individuals interact more independently with their physical environment. The system utilizes a standard computer's camera to perform all AI analysis locally within a virtualized ARM environment, ensuring user privacy and low-latency responses.

## 2. Core Architecture

The system consists of two primary components operating in tandem, leveraging a decoupled architecture for maximum stability:

*   **Host (Windows):** The primary user-facing environment. It runs the `camera_client.py` script, managing the physical camera, audio output (Text-to-Speech), and the user interface.
*   **Guest (QEMU + Ubuntu Server ARM64 on WSL2):** An isolated, virtualized ARM64 environment launched via WSL2. It runs the `ai_server.py`, performing all intensive AI computations without direct access to host hardware, ensuring stability and portability.

---

## 3. Environment Setup

### 3.1. One-Time WSL Configuration (For QEMU)

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

The Guest VM runs the `ai_server.py`. A Python virtual environment (`ai_assistant_env`) is required inside the VM.

1.  **Create Virtual Environment (inside VM via SSH):**
    ```bash
    python3 -m venv ai_assistant_env
    ```
2.  **Install Dependencies:** Ensure a `requirements-vm.txt` file exists inside the VM's project directory with necessary content (e.g., `numpy`, `Pillow`, `tflite-runtime`). Then, install the dependencies:
    ```bash
    source ai_assistant_env/bin/activate
    pip install -r requirements-vm.txt
    ```

### 3.3. Host (Windows) Client Setup

The Host runs `camera_client.py` natively on Windows to avoid all WSL hardware compatibility issues.

1.  **Install Python on Windows:**
    *   **Recommended:** Install "Python 3.11" (or newer) from the Microsoft Store.
    *   **Alternative:** Download from `python.org`, ensuring you check **"Add Python to PATH"** during installation.

2.  **Create Python Virtual Environment (in project root):**
    ```powershell
    # In a Windows PowerShell terminal, from the project's root directory
    python -m venv win_env
    ```

3.  **Activate Environment and Install Dependencies:**
    ```powershell
    # Activate the new environment
    .\win_env\Scripts\Activate.ps1
    
    # Install required packages from the provided requirements-windows.txt file
    pip install -r requirements-windows.txt
    ```

---

## 4. Daily Workflow & Commands

The new workflow is simpler and more reliable, with no `usbipd` required.

### **Terminal 1 (WSL): Start AI Server**

1.  **Start the QEMU Virtual Machine:**
    ```bash
    # This command launches the VM. Keep this terminal open.
    # Ensure file paths to disk and BIOS are correct for your setup.
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

2.  **Connect to VM and Start Server:** Open a **second WSL terminal** and run:
    ```bash
    # Connect to the running VM via SSH
    ssh ubuntu@localhost -p 2222

    # Once inside, activate the environment and start the AI server
    source ~/projects/ai_assistant_env/bin/activate
    python3 ~/projects/ai_server.py
    ```
    Leave this terminal open. You should see the "Server is listening..." message.

### **Terminal 2 (Windows PowerShell): Start Camera Client**

1.  Open a **Windows PowerShell** terminal in your project's root directory (or use the VS Code integrated terminal).
2.  **Activate the Windows Virtual Environment:**
    ```powershell
    .\win_env\Scripts\Activate.ps1
    ```
3.  **Run the Camera Client:**
    ```powershell
    python camera_client.py
    ```

---

## 5. Troubleshooting

**Connection Refused Errors**
*   **Cause:** The AI server is not running in the VM, or the QEMU port forwarding is not configured correctly.
*   **Solution:** Ensure the AI Server terminal shows "Server is listening...". Verify the `-netdev user, ...,hostfwd=tcp::12345-:12345` parameter in your QEMU command.

**Camera Not Detected on Windows**
*   **Cause:** Another application (Teams, Zoom, etc.) is using the camera, or the wrong camera index is set in `config.py`.
*   **Solution:** Close all other applications that might use the camera. Try changing `CAMERA_INDEX` in `config.py` to `1` or `2`.

**`python` or `pip` is not recognized in PowerShell**
*   **Cause:** Python was installed on Windows without the "Add Python to PATH" option.
*   **Solution:** Re-install Python and ensure the PATH option is checked, or install it from the Microsoft Store for automatic path management.