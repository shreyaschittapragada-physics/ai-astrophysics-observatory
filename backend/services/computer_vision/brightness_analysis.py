import cv2
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import os


# =========================
# PROJECT PATH CONFIG
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "../../../")
)

IMAGE_PATH = os.path.join(
    PROJECT_ROOT,
    "datasets",
    "sky_images",
    "sky.jpg"
)

OUTPUT_LOG = os.path.join(
    PROJECT_ROOT,
    "logs",
    "brightness_log.csv"
)


# =========================
# LOAD IMAGE SAFELY
# =========================

img = cv2.imread(IMAGE_PATH)

if img is None:
    print(f"❌ ERROR: Image not found")
    print(f"📍 Checked path: {IMAGE_PATH}")
    exit()


# =========================
# CONVERT TO GRAYSCALE
# =========================

gray = cv2.cvtColor(
    img,
    cv2.COLOR_BGR2GRAY
)


# =========================
# REGION OF INTEREST
# Remove edges/noise
# =========================

h, w = gray.shape

roi = gray[
    int(h * 0.1):int(h * 0.9),
    int(w * 0.1):int(w * 0.9)
]


# =========================
# NOISE REDUCTION
# =========================

roi_blur = cv2.GaussianBlur(
    roi,
    (5, 5),
    0
)


# =========================
# ANALYSIS
# =========================

mean_brightness = np.mean(roi_blur)
std_brightness = np.std(roi_blur)

hist = cv2.calcHist(
    [roi_blur],
    [0],
    None,
    [256],
    [0, 256]
)

timestamp = datetime.now()


# =========================
# SKY QUALITY CLASSIFIER
# =========================

if mean_brightness < 50:
    sky_quality = "Excellent"

elif mean_brightness < 100:
    sky_quality = "Good"

elif mean_brightness < 160:
    sky_quality = "Moderate"

else:
    sky_quality = "Poor"


# =========================
# OUTPUT
# =========================

print("\n🌌 SKY BRIGHTNESS ANALYSIS")
print("----------------------------")
print(
    "Time:",
    timestamp.strftime("%Y-%m-%d %H:%M:%S")
)

print(
    "Mean Brightness:",
    round(mean_brightness, 3)
)

print(
    "Noise (Std Dev):",
    round(std_brightness, 3)
)

print(
    "Sky Quality:",
    sky_quality
)


# =========================
# SAVE DATA (CSV LOGGING)
# =========================

os.makedirs(
    os.path.dirname(OUTPUT_LOG),
    exist_ok=True
)

file_exists = os.path.isfile(OUTPUT_LOG)

with open(
    OUTPUT_LOG,
    "a",
    newline=""
) as f:

    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "timestamp",
            "mean_brightness",
            "std_dev",
            "sky_quality"
        ])

    writer.writerow([
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        round(mean_brightness, 3),
        round(std_brightness, 3),
        sky_quality
    ])


# =========================
# VISUALIZATION
# =========================

plt.figure(figsize=(10, 4))


# Processed Sky Image
plt.subplot(1, 2, 1)

plt.imshow(
    roi_blur,
    cmap="gray"
)

plt.title("Sky ROI (Processed)")
plt.axis("off")


# Histogram
plt.subplot(1, 2, 2)

plt.plot(hist)

plt.title("Brightness Histogram")
plt.xlabel("Pixel Intensity")
plt.ylabel("Frequency")


plt.tight_layout()
plt.show()
