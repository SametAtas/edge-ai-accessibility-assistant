# Project Notes & Development Log: Edge-AI Accessibility Assistant

**VERSION: 1.0 - "Speaking Eye" Milestone (Stabilized)**

## 1. Project Summary and Vision

To develop a privacy-focused, offline-first AI assistant for the visually impaired. The architecture leverages a QEMU-virtualized ARM environment for AI processing, with a host-level client managing the user interface (camera and audio).

## 2. Current Status: Milestone 1.0 Completed

The project has successfully achieved a stable, functional prototype. The core "see and speak" functionality is operational, and the underlying architecture has been hardened to resolve critical show-stopper bugs encountered during development.

### 2.1. Key Accomplishments

**1. AI Server (`ai_server.py`) Stabilization:**
*   **Output Enhancement:** AI output was transitioned from raw class labels to human-readable sentences with a confidence threshold.
*   **Modularity:** Refactored into distinct functions for loading, classifying, and serving, improving readability and maintainability.

**2. Decoupled Client-Server Architecture:**
*   **Centralized Configuration:** A `config.py` file was implemented to manage all settings, distinguishing between `SERVER_BIND_HOST` (for the VM) and `CLIENT_CONNECT_HOST` (for the host machine) for a robust network setup.
*   **Dependency Management:** Established separate `requirements-vm.txt` and `requirements-windows.txt` files, creating fully reproducible environments for both the server and the client.

**3. Architectural Migration for Stability (Client on Native Windows):**
*   **Hardware Compatibility Solved:** Resolved persistent `select() timeout` errors with the webcam by migrating the `camera_client.py` from WSL to native Windows. This gives OpenCV direct, reliable access to the camera's hardware drivers.
*   **TTS Stability Solved:** Fixed a critical bug where the `pyttsx3` library would freeze the main application loop after the first speech. The solution involved moving the TTS engine into a separate, non-blocking process using Python's `multiprocessing` library, ensuring the UI remains responsive.

### 2.2. Critical Lessons Learned

*   **WSL is for Computation, Not Direct Hardware I/O:** This project demonstrated that while WSL2 is exceptional for running containerized Linux environments and handling computation (like the AI server), it can be a source of instability for direct, real-time hardware interactions (like camera streams). **The most robust architectural pattern is to keep computation in the isolated environment (WSL/VM) and move hardware-facing I/O to the native host OS.**

*   **Isolate Blocking Operations:** The `pyttsx3` freezing issue was a classic example of a blocking I/O call halting an entire application. The solution—running the blocking call in a separate process—is a key technique for building responsive, event-driven applications.

*   **Virtual Environments are Non-Negotiable:** The strict isolation of dependencies between the Windows client (`win_env`) and the Linux VM server (`ai_assistant_env`) proved essential. It prevented version conflicts and streamlined debugging immensely.

---

## 3. Future Development Roadmap

With a stable foundation, the project is now ready for the next phase: transforming the tool into a true interactive assistant.

*   **Task: Voice Command Input (Wake-word & Speech-to-Text):**
    *   **Goal:** Allow the user to activate and command the assistant with their voice.
    *   **Action:** Research and implement a lightweight wake-word engine (e.g., `pvporcupine`) and a small, efficient Speech-to-Text model on the AI server.

*   **Task: Transition to Object Detection (From "What" to "Where"):**
    *   **Goal:** Provide spatial context for objects.
    *   **Action:** Replace the current image classification model with a lightweight object detection model (e.g., `SSD-MobileNet`). The server will be updated to return not just labels, but also bounding box coordinates, which the client can translate into descriptive locations (e.g., "a cup on your left").

*   **Task: Performance Optimization & Benchmarking:**
    *   **Goal:** Measure and improve end-to-end latency.
    *   **Action:** Systematically benchmark different image resolutions, JPEG quality settings, and alternative AI models (`MobileNetV2/V3`) to find the optimal balance between speed and accuracy.