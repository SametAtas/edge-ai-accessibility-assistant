import socket, io, json, config, tflite_runtime.interpreter as tflite
from PIL import Image
import numpy as np

def load_labels(path: str) -> dict[int, str]:
    """Loads and cleans class labels from a file."""
    labels = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f.readlines()):
                label = line.strip()
                if '  ' in label: label = label.split('  ', 1)[1].strip()
                elif ' ' in label and label.split(' ', 1)[0].isdigit(): label = label.split(' ', 1)[1].strip()
                if label: labels[i] = label
        print(f"Loaded {len(labels)} labels from '{path}'.")
        return labels
    except Exception as e:
        print(f"FATAL: Could not load labels. Error: {e}")
        return {}

def detect_objects(interpreter: tflite.Interpreter, image_bytes: bytes, labels: dict) -> str:
    """Performs object detection and returns a JSON string with results."""
    try:
        input_details = interpreter.get_input_details()
        height = input_details[0]['shape'][1]
        width = input_details[0]['shape'][2]
        
        image = Image.open(io.BytesIO(image_bytes)).resize((width, height))
        input_data = np.expand_dims(np.array(image), axis=0)
        
        if input_details[0]['dtype'] == np.uint8:
            input_data = input_data.astype(np.uint8)
    except Exception as e:
        return json.dumps({"success": False, "message": f"Image processing error: {e}"})

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    output_details = interpreter.get_output_details()
    boxes, classes, scores = (interpreter.get_tensor(details['index'])[0] for details in output_details[:3])
    
    detections = []
    for i in range(len(scores)):
        if scores[i] >= config.AI_CONFIDENCE_THRESHOLD:
            class_id = int(classes[i])
            if class_id in labels:
                box_center_x = (boxes[i][1] + boxes[i][3]) / 2.0
                location = "left" if box_center_x < config.LEFT_THRESHOLD else "right" if box_center_x > config.RIGHT_THRESHOLD else "center"
                detections.append({"object": labels[class_id], "location": location})

    detections.sort(key=lambda d: d['location'] != 'center') # Prioritize center objects
    natural_sentence = create_natural_response(detections, config.OUTPUT_LANGUAGE)
    return json.dumps({"success": True, "message": natural_sentence, "object_count": len(detections)})

def create_natural_response(detections: list, language: str) -> str:
    """Creates a human-like sentence from a list of detections."""
    if not detections:
        return "Net bir şey göremiyorum." if language == 'tr' else "I can't see anything clearly."
    
    detections = detections[:config.MAX_OBJECTS_TO_DESCRIBE]
    
    if language == 'tr':
        location_map = {"left": "solunuzda", "right": "sağınızda", "center": "önünüzde"}
        descriptions = [f"{location_map[d['location']]} bir {d['object']}" for d in detections]
        return f"{descriptions[0]} var." if len(descriptions) == 1 else f"{', '.join(descriptions[:-1])} ve {descriptions[-1]} görüyorum."
    else: # English
        location_map = {"left": "on your left", "right": "on your right", "center": "in front of you"}
        descriptions = [f"a {d['object']} {location_map[d['location']]}" for d in detections]
        return f"I see {', '.join(descriptions)}."

def handle_client(conn: socket.socket, interpreter: tflite.Interpreter, labels: dict):
    """Handle a single client request: receive, process, respond, close."""
    try:
        # Read all data from the client until the stream is closed
        image_data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            image_data += chunk
        
        if not image_data:
            print("Warning: Received no data from client.")
            return

        print(f"Received {len(image_data)} bytes. Processing...")
        json_response = detect_objects(interpreter, image_data, labels)
        conn.sendall(json_response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()
        print("Connection closed.")

def main():
    """Initializes and runs the AI server."""
    print("Starting AI Server...")
    try:
        labels = load_labels(config.AI_LABELS_FILE)
        if not labels: return
        interpreter = tflite.Interpreter(model_path=config.AI_MODEL_FILE)
        interpreter.allocate_tensors()
        print(f"Model '{config.AI_MODEL_FILE}' loaded. Input shape: {interpreter.get_input_details()[0]['shape']}")
    except Exception as e:
        print(f"FATAL: Model/labels failed to load. Error: {e}")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((config.SERVER_BIND_HOST, config.SERVER_PORT))
        server_socket.listen(5)
        print(f"Server listening on {config.SERVER_BIND_HOST}:{config.SERVER_PORT}.")
    except Exception as e:
        print(f"FATAL: Cannot bind to port. Error: {e}")
        return

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"\nAccepted connection from {addr}")
            # No need to thread this for a single user, keeping it simple and robust
            handle_client(conn, interpreter, labels)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()