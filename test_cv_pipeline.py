import os
import sys
import cv2
import numpy as np

sys.path.append(os.getcwd())

# Use the active updated analyzer pipeline
from backend.services.computer_vision.optical_analyzer import OpticalIngestionEngine

def run_pipeline_test():
    print("\n--- BEGINNING DETECTED PIPELINE VALIDATION TEST ---")
    engine = OpticalIngestionEngine()
    
    # Check for test asset or build mock frame
    test_dir = "datasets/sky_images"
    os.makedirs(test_dir, exist_ok=True)
    image_path = os.path.join(test_dir, "sky.jpg")
    
    if not os.path.exists(image_path):
        print("Creating mock star field file for test run...")
        mock_frame = np.zeros((500, 500, 3), dtype=np.uint8)
        for _ in range(50):
            y, x = np.random.randint(0, 500), np.random.randint(0, 500)
            cv2.circle(mock_frame, (x, y), 1, (255, 255, 255), -1)
        cv2.imwrite(image_path, mock_frame)
        
    metrics = engine.process_image(image_path)
    print("\n✅ CV Pipeline executed successfully. Outputs retrieved:")
    for k, v in metrics.items():
        print(f"   • {k}: {v}")

if __name__ == '__main__':
    run_pipeline_test()
