# Project Notes & Development Log: Edge-AI Accessibility Assistant

**VERSION: 1.0 - "Speaking Eye" Milestone**

## 1. Project Summary and Vision

To develop a privacy-focused, offline-first AI assistant for the visually impaired. The architecture leverages a QEMU-virtualized ARM environment for AI processing, with a host-level client managing the user interface (camera and audio).

## 2. Current Status: Phase 2 Completed

The project has successfully achieved its initial proof of concept. The core infrastructure is stable, and the primary "see and speak" functionality is operational.

### 2.1. Key Accomplishments

**1. AI Server (`ai_server.py`) Stabilization:**
*   **Critical Bug Fixes:** Corrected a `TypeError` in TFLite tensor access by properly indexing the list returned by `get_input_details()`. Fixed a logical error in image resizing by correctly parsing `height` and `width` from the model's input shape.
*   **Output Enhancement:** AI output was transitioned from raw class labels (e.g., "keyboard: 0.87") to human-readable sentences (e.g., "I see a keyboard.").
*   **Robustness:** Implemented a confidence threshold to prevent the system from reporting low-certainty predictions, instead returning a message of uncertainty.

**2. Camera Client (`camera_client.py`) Functionality:**
*   **Text-to-Speech (TTS):** Integrated the `pyttsx3` library to provide audio feedback of the AI's findings.
*   **User Experience:** Implemented logic to prevent the repetition of identical, consecutive results, making the audio feedback less intrusive.

**3. WSL Environment Hardening:**
*   **Networking:** Resolved a critical issue where `pip install` commands would freeze indefinitely. This was traced to WSL's default network mode and permanently fixed by setting `networkingMode=mirrored` in the `.wslconfig` file.
*   **Audio Subsystem:** Systematically debugged and resolved all audio output issues within WSL. This multi-step process was crucial for the project's success.
*   **Dependency Management:** Established a clean architecture using separate Python virtual environments (`venv`) for the host client and the guest AI server, preventing dependency conflicts.

### 2.2. Critical Lessons Learned

*   **WSL Audio is a Chain of Dependencies:** Successful audio output in WSL is not monolithic. It requires a complete chain of components to be in place:
    1.  **The Engine:** A TTS engine like `espeak-ng`.
    2.  **The Player:** A command-line audio player like `aplay` (from `alsa-utils`).
    3.  **The Bridge:** The ALSA plugin to connect to the PulseAudio server (`libasound2-plugins`).
    4.  **The Map:** The `~/.asoundrc` file to direct all audio traffic to the WSLg PulseAudio server.
    The absence of any single link in this chain results in failure.

*   **Virtual Environments are Non-Negotiable:** The strict isolation of dependencies between the host (x86, user-facing libraries) and the guest (ARM, AI-specific libraries) proved essential. It prevented version conflicts and streamlined debugging.

*   **WSL Networking Mode is a Common Pitfall:** The `mirrored` networking mode should be considered a default for any WSL development involving extensive network I/O or connections to host services, as it resolves many obscure firewall and connectivity problems.

---

## 3. Future Development Roadmap & Optimization Strategy

**Current State Analysis:** The project has successfully reached its initial "Speaking Eye" milestone. However, to elevate this project from a functional prototype to a high-quality, portfolio-worthy piece of engineering, a dedicated phase of optimization, refactoring, and feature deepening is required. The following roadmap outlines these strategic steps.

### **Phase 3.1: Refactoring for Maintainability ("Solid Foundation")**

*   **Task: Centralized Configuration:**
    *   **Objective:** Decouple settings from application logic.
    *   **Action:** Migrate hard-coded values (IPs, ports, model paths, thresholds) into a dedicated `config.ini` file.

*   **Task: Code Modularization:**
    *   **Objective:** Improve code readability and reusability.
    *   **Action:** Refactor `camera_client.py` and `ai_server.py` by breaking down major functionalities into distinct functions or classes.

### **Phase 3.2: Performance Analysis & Optimization ("Measure, Improve, Verify")**

*   **Task: Establish Performance Baselines:**
    *   **Objective:** Create metrics to measure all future optimizations against.
    *   **Action:** Implement timing logic to measure End-to-End Latency (from frame capture to TTS completion).

*   **Task: Network Efficiency Experiments:**
    *   **Objective:** Reduce data transmission size and its impact on latency.
    *   **Hypothesis:** Lowering image quality will significantly reduce latency with a minimal impact on accuracy.
    *   **Action:** Systematically test various JPEG compression levels and image resolutions and document the trade-offs.

*   **Task: AI Model Benchmarking:**
    *   **Objective:** Determine the optimal model for the given resource constraints.
    *   **Hypothesis:** A more modern architecture like MobileNetV2 may offer better performance than MobileNetV1.
    *   **Action:** Adapt the AI server to easily switch between different `.tflite` models and create a comparative table of each model's inference time, accuracy, and file size.

### **Phase 3.3: Core Feature Enhancement ("From 'What' to 'Where'")**

*   **Task: Transition to Object Detection:**
    *   **Objective:** Provide spatial context in addition to object identification.
    *   **Action:** Replace the current image classification model with an object detection model (e.g., SSD-MobileNet).
    *   **Implementation:** Modify the server to parse bounding box coordinates and develop logic to translate these coordinates into descriptive locations (e.g., "left," "center," "right").

### **Phase 3.4: Architectural Improvements ("Future-Proofing")**

*   **Task: Implement a Structured Communication Protocol:**
    *   **Objective:** Move from raw text to a more robust and extensible data format.
    *   **Action:** Use JSON for all client-server communication to easily handle more complex data structures in the future.