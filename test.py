from ultralytics import YOLO

# --- CHANGE THIS PATH to the model you want to check ---
model_path = 'generalist_model_float32.tflite' 

# Load the model
model = YOLO(model_path)

# Print the list of class names stored inside the model
print(f"Class names for '{model_path}':")
print(model.names)