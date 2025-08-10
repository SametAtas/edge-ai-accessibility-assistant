# Project Log & Development Notes: Edge-AI Accessibility Assistant

**VERSION: 1.0 - "Stable Eye" Milestone**

## 1. Project Summary and Vision

To develop a privacy-focused, offline-first AI assistant for the visually impaired. The architecture leverages a QEMU-virtualized ARM environment for AI processing, with a host-level client managing the user interface (camera and audio).

## 2. Current Status: Milestone 1.0 Completed

The project has successfully achieved a stable, functional prototype. The core "see and speak" functionality is operational, and the underlying architecture has been hardened to resolve critical show-stopper bugs encountered during development. This document outlines the key decisions and learnings from this journey.

### 2.1. Key Accomplishments

1.  **Achieved Real-Time Performance:** By offloading image resizing to the powerful host client and using a robust single-transaction network model, the system now achieves sub-second end-to-end latency with the `EfficientDet-Lite2` model.

2.  **Decoupled & Stable Architecture:** The final architecture, with the `camera_client.py` on the native Windows host and the `ai_server.py` in the isolated QEMU VM, proved to be the most stable and reliable configuration, solving all previous hardware access issues.

3.  **Intelligent and Natural UX:**
    *   **Natural Language:** The AI server now generates grammatically correct, conversational sentences in both Turkish and English.
    *   **Robust Speech:** The client uses a non-blocking, multi-process approach for text-to-speech, preventing application freezes. A cooldown system and state tracking prevent repetitive announcements, creating a more pleasant user experience.

4.  **Centralized & Tunable Configuration:** All critical parameters (model files, confidence thresholds, language, etc.) are managed via a single `config.py` file, making the system easy to tune and adapt.

### 2.2. Critical Lessons Learned

This project was a masterclass in the realities of edge AI and system architecture.

*   **WSL2/VMs are for Computation, Not Direct Hardware I/O:** This was the most critical lesson. While WSL2 is exceptional for running containerized Linux environments, it is a source of instability for real-time hardware interactions like camera streams. **The most robust architectural pattern is: keep computation in the isolated environment (VM) and move hardware-facing I/O to the native host OS.**

*   **The Bottleneck is Almost Always the Model:** The journey from `Lite0` to `Lite4` and back to `Lite2` demonstrated the fundamental trade-off between speed and accuracy. The `interpreter.invoke()` call was consistently the main source of latency. A system is only as fast as its slowest component.

*   **Client-Side Pre-processing is King:** The single biggest performance gain came from resizing the image on the powerful client *before* sending it to the computationally-weak server. This simple change dramatically reduced the server's workload and was the key to achieving real-time performance.

*   **Blocking Operations Will Freeze Your App:** The initial TTS issues were a classic example of a blocking I/O call halting an event-driven application. The solution—running the blocking call in a separate process—is a foundational technique for building responsive applications.

## 3. Future Development Roadmap

While v1.0 is complete, the project has a clear path for future expansion:

*   **Task: Voice Command Input (Wake-word & Speech-to-Text):** Implement a lightweight wake-word engine (e.g., `pvporcupine`) and a small Speech-to-Text model on the AI server to allow for hands-free interaction.
*   **Task: Deeper Scene Understanding:** Move beyond single-object labels to describe relationships between objects (e.g., "a cup is on the table to your right"). This would likely require a more advanced model or post-processing logic.
*   **Task: Custom Model Training:** Train a model on specific, user-relevant objects (e.g., medication bottles, specific keys, a personal walking cane) using a platform like Roboflow or TensorFlow's Object Detection API.