import sys
import os
sys.path.append(os.getcwd())

import cv2
import numpy as np
from backend.services.computer_vision.motion_tracker import MotionTracker

# Instantiate the engine here, locally in the test script
engine = MotionTracker(buffer_size=5)

frame_static = np.zeros((512, 512), dtype=np.uint8)
frame_motion = np.zeros((512, 512), dtype=np.uint8)
cv2.circle(frame_motion, (200, 200), 20, 255, -1) 

print("Sending static frame...")
engine.process(frame_static)

print("Sending motion frame...")
is_motion = engine.process(frame_motion)

if is_motion:
    print("✅ Success! Check your datasets/captures/ folder.")
else:
    print("❌ No motion detected. Sensitivity might be too low.")