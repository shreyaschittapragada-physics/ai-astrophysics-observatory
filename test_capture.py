import sys
import os

# Diagnostic: Print where Python is looking
print("Python Path:", sys.path)

try:
    from backend.services.computer_vision.motion_tracker import engine
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    # List files to see if the file actually exists where we think it does
    print("Contents of computer_vision folder:", os.listdir('backend/services/computer_vision'))