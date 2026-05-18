import cv2
import matplotlib.pyplot as plt
import numpy as np
import os


# ==========================================
# STAR DETECTION MODULE
# ==========================================

def detect_stars(image_path, show_plots=True):

    # ==========================================
    # LOAD IMAGE
    # ==========================================

    img = cv2.imread(image_path)

    if img is None:
        raise FileNotFoundError(
            f"Image not found at: {image_path}"
        )

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
        185,
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

    star_areas = []

    brightest_star = 0

    output = img.copy()

    for contour in contours:

        area = cv2.contourArea(contour)

        if 2 < area < 20:

            x, y, w, h = cv2.boundingRect(
                contour
            )

            center_x = x + w // 2
            center_y = y + h // 2

            # Draw detection circle
            cv2.circle(
                output,
                (center_x, center_y),
                8,
                (0, 255, 0),
                1
            )

            # Track statistics
            star_areas.append(area)

            brightness = gray[
                center_y,
                center_x
            ]

            if brightness > brightest_star:
                brightest_star = int(brightness)

            star_count += 1

    # ==========================================
    # STAR STATISTICS
    # ==========================================

    if len(star_areas) > 0:

        average_star_area = round(
            np.mean(star_areas),
            3
        )

    else:
        average_star_area = 0

    # ==========================================
    # VISUALIZATION
    # ==========================================

    if show_plots:

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

    # ==========================================
    # RETURN RESULTS
    # ==========================================

    return {
        "stars_detected": star_count,
        "brightest_star": brightest_star,
        "average_star_area": average_star_area
    }


# ==========================================
# STANDALONE TESTING
# ==========================================

if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    PROJECT_ROOT = os.path.abspath(
        os.path.join(BASE_DIR, "../../../")
    )

    IMAGE_PATH = os.path.join(
        PROJECT_ROOT,
        "datasets",
        "sky_images",
        "sky.jpg"
    )

    results = detect_stars(
        image_path=IMAGE_PATH,
        show_plots=True
    )

    print("\n✨ STAR DETECTION REPORT")
    print("----------------------------")

    for key, value in results.items():
        print(f"{key}: {value}")