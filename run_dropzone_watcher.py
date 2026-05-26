import os
import time
import shutil
from backend.services.computer_vision.optical_analyzer import OpticalIngestionEngine

DROP_ZONE = "datasets/drop_zone"
ARCHIVE_ZONE = "datasets/captures/archived_inputs"

def main():
    engine = OpticalIngestionEngine()
    os.makedirs(DROP_ZONE, exist_ok=True)
    os.makedirs(ARCHIVE_ZONE, exist_ok=True)

    print("🚀 Project AstroEdge: Drop-Zone Automated Watcher Active!")
    print(f"📥 Drop your observation images in: {os.path.abspath(DROP_ZONE)}")
    print("✨ Scanning for file drops (Press CTRL+C to quit)...")

    try:
        while True:
            # Check for common image signatures
            files = [f for f in os.listdir(DROP_ZONE) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff'))]
            
            for filename in files:
                full_path = os.path.join(DROP_ZONE, filename)
                print(f"\n📸 New capture detected: {filename}...")
                
                # Settle buffer to guarantee the OS write process has completed
                time.sleep(0.5)
                
                try:
                    metrics = engine.process_image(full_path)
                    print(f"   📊 Mean Brightness: {metrics['mean_brightness']} | Quality: {metrics['sky_quality']}")
                    print(f"   ⭐ Star Field Isolation Count: {metrics['stars_detected']} stars cataloged.")
                    
                    # Relocate to keep the drop-zone clean
                    shutil.move(full_path, os.path.join(ARCHIVE_ZONE, filename))
                    print(f"   📦 Successfully processed and archived.")
                except Exception as e:
                    print(f"   ⚠️ Error processing frame {filename}: {e}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Drop-zone automated listener stopped safely.")

if __name__ == "__main__":
    main()
