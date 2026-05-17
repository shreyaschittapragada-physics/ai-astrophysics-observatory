import cv2
import matplotlib.pyplot as plt
import os


# ==========================================
# PROJECT PATH CONFIG
# ==========================================

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


# ==========================================
# LOAD IMAGE
# ==========================================

img = cv2.imread(IMAGE_PATH)

if img is None:
    print("❌ ERROR: Image not found")
    print("Checked path:", IMAGE_PATH)
    exit()


# ==========================================
# PREPROCESSING
# ==========================================

gray = cv2.cvtColor(
    img,
    cv2.COLOR_BGR2GRAY
)

blur = cv2.GaussianBlur(
    gray,
    (5, 5),
    0
)


# ==========================================
# STAR DETECTION
# ==========================================

_, threshold = cv2.threshold(
    blur,
    185,  # lower threshold for dim stars
    255,
    cv2.THRESH_BINARY
)


# ==========================================
# FIND BRIGHT OBJECTS
# ==========================================

contours, _ = cv2.findContours(
    threshold,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)


# ==========================================
# FILTER STARS / REMOVE NOISE
# ==========================================

star_count = 0

output = img.copy()

for contour in contours:

    area = cv2.contourArea(contour)

    # better filtering range
    if 2 < area < 20:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        center_x = x + w // 2
        center_y = y + h // 2

        # Draw green circle
        cv2.circle(
            output,
            (center_x, center_y),
            8,
            (0, 255, 0),
            1
        )

        star_count += 1


# ==========================================
# OUTPUT REPORT
# ==========================================

print("\n✨ STAR DETECTION REPORT")
print("----------------------------")
print("Detected Bright Objects:", star_count)


# ==========================================
# VISUALIZATION
# ==========================================

plt.figure(figsize=(15, 5))


# Original Image
plt.subplot(1, 3, 1)

plt.imshow(
    cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )
)

plt.title("Original Sky Image")
plt.axis("off")


# Threshold View
plt.subplot(1, 3, 2)

plt.imshow(
    threshold,
    cmap="gray"
)

plt.title("Threshold Detection View")
plt.axis("off")


# Final Detection
plt.subplot(1, 3, 3)

plt.imshow(
    cv2.cvtColor(
        output,
        cv2.COLOR_BGR2RGB
    )
)

plt.title(
    f"Detected Stars: {star_count}"
)

plt.axis("off")


plt.tight_layout()
plt.show()