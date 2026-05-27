import sys
import os
sys.path.append(os.getcwd())
from backend.services.computer_vision.star_detection import detect_stars

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python pipeline.py <path_to_image>')
        sys.exit(1)
    
    image_path = sys.argv[1]
    results = detect_stars(image_path, show_plots=False)
    print(f'✅ Analysis complete: {results}')