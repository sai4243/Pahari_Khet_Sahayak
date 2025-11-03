import os
import json
import cv2  
from ultralytics import YOLO

print("Loading all models, this might take a moment...")

# --- Define model paths ---
CROP_CLASSIFIER_PATH = 'crop_classifier_yolo.pt'
WHEAT_MODEL_PATH = 'best.pt'
MILLET_MODEL_PATH = 'final_model_float32.tflite'
GENERAL_MODEL_PATH = 'generalist_model_float32.tflite'

models = {}

try:
    # Explicitly define the task for each model to remove warnings
    models['crop_classifier'] = YOLO(CROP_CLASSIFIER_PATH)
    models['wheat_disease'] = YOLO(WHEAT_MODEL_PATH) 
    models['millet_disease'] = YOLO(MILLET_MODEL_PATH, task='detect')
    models['general_disease'] = YOLO(GENERAL_MODEL_PATH, task='detect')
    print("✅ All models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")
    print("Please ensure all model files are in the correct directory.")
    exit()


def classify_crop(image_path, confidence_threshold=0.85):
    """Uses the YOLOv8 classifier to identify the crop type."""
    results = models['crop_classifier'].predict(image_path, verbose=False)
    probs = results[0].probs
    confidence = probs.top1conf.item()
    
    if confidence < confidence_threshold:
        return "Invalid", confidence
    else:
        class_index = probs.top1
        crop_name = models['crop_classifier'].names[class_index]
        return crop_name, confidence

def run_yolo_detection(model_to_use, image_path):
    """Runs detection and filters for the highest confidence result per unique disease."""
    results = model_to_use.predict(image_path, verbose=False)
    annotated_image = results[0].plot() 
    
    all_detections = []
    for box in results[0].boxes:
        coords = box.xyxy[0].tolist()
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        
        if class_id < len(model_to_use.names):
            detection_data = {
                "disease_name": model_to_use.names[class_id],
                "confidence_score": confidence,
                "bounding_box_coordinates": {
                    "x1": int(coords[0]), "y1": int(coords[1]), 
                    "x2": int(coords[2]), "y2": int(coords[3])
                }
            }
            all_detections.append(detection_data)

    best_detections = {}
    for detection in all_detections:
        name = detection["disease_name"]
        if name not in best_detections or detection["confidence_score"] > best_detections[name]["confidence_score"]:
            best_detections[name] = detection
    
    return list(best_detections.values()), annotated_image

def detect_disease(crop_name, image_path):
    """Selects and runs the correct specialist disease model."""
    print(f"\n--- Running disease detection for '{crop_name}' ---")
    
    simple_crop_name = crop_name.lower().replace(" dataset", "").strip()
    
    if "wheat" in simple_crop_name:
        return run_yolo_detection(models['wheat_disease'], image_path)
    elif "millet" in simple_crop_name:
        return run_yolo_detection(models['millet_disease'], image_path)
    else:
        return run_yolo_detection(models['general_disease'], image_path)

# ===================================================================
# MAIN WORKFLOW
# ===================================================================

image_to_analyze = 'test_images/🟢millet_test.jpg' # <--- CHANGE THIS IMAGE PATH

if not os.path.exists(image_to_analyze):
    print(f"Error: Test image not found at '{image_to_analyze}'")
else:
    # --- Stage 1: Classify the crop ---
    crop_type, confidence = classify_crop(image_to_analyze)
    print(f"\nStage 1 Result: Detected '{crop_type}' with {confidence:.2%} confidence.")
    
    annotated_image = None # Initialize to None

    # --- Stage 2: Run disease detection if the crop is valid ---
    if crop_type != "Invalid":
        disease_results, annotated_image = detect_disease(crop_type, image_to_analyze)
        
        final_output = {
            "crop_name": crop_type,
            "crop_confidence": confidence,
            "disease_detections": disease_results if disease_results else "No diseases detected."
        }
    else:
        print("Input is not a recognized crop. Stopping analysis.")
        # BUG FIX: Create a JSON object for the invalid case
        final_output = {
            "crop_name": "Invalid",
            "crop_confidence": confidence,
            "disease_detections": "Input image is not a valid crop."
        }

    # BUG FIX: Save the JSON file outside the if/else block
    # This ensures the file is ALWAYS updated with the latest result.
    output_filename = 'detection_results.json'
    with open(output_filename, 'w') as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\n✅ Results have been saved to the file: '{output_filename}'")
    print("\n--JSON Output--")
    print(json.dumps(final_output, indent=4))
    print("-----------------")

    # Display the visual result only if an image was processed
    if annotated_image is not None:
        print("\nDisplaying visual result...")
        cv2.imshow('Live Disease Detection', annotated_image)
        print("--> Press any key on the image window to close.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
