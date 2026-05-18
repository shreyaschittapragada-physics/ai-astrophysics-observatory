import os

from computer_vision.brightness_analysis import (
    analyze_brightness
)

from computer_vision.star_detection import (
    detect_stars
)


# ==========================================
# OBSERVATORY ENGINE
# ==========================================

def generate_observatory_report(image_path):

    # ======================================
    # RUN MODULES
    # ======================================

    brightness_results = analyze_brightness(
        image_path=image_path,
        output_log=None,
        show_plots=False
    )

    star_results = detect_stars(
        image_path=image_path,
        show_plots=True
    )

    # ======================================
    # REPORT
    # ======================================

    print("\n🌌 OBSERVATORY REPORT")
    print("--------------------------------")

    print(
        f"Timestamp: "
        f"{brightness_results['timestamp']}"
    )

    print(
        f"Mean Brightness: "
        f"{brightness_results['mean_brightness']}"
    )

    print(
        f"Noise Level: "
        f"{brightness_results['std_dev']}"
    )

    print(
        f"Sky Quality: "
        f"{brightness_results['sky_quality']}"
    )

    print(
        f"Stars Detected: "
        f"{star_results['stars_detected']}"
    )

    print(
        f"Brightest Star Intensity: "
        f"{star_results['brightest_star']}"
    )

    print(
        f"Average Star Area: "
        f"{star_results['average_star_area']}"
    )

    # ======================================
    # OBSERVATORY STATUS
    # ======================================

    if (
        brightness_results["sky_quality"]
        == "Excellent"
    ):

        observatory_status = (
            "IDEAL OBSERVING CONDITIONS"
        )

    elif (
        brightness_results["sky_quality"]
        == "Good"
    ):

        observatory_status = (
            "GOOD OBSERVING CONDITIONS"
        )

    else:

        observatory_status = (
            "LIMITED OBSERVING CONDITIONS"
        )

    print("\n🛰 Observatory Status:")
    print(observatory_status)

    print("\n✅ Observation Complete")


# ==========================================
# MAIN ENTRY
# ==========================================

if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    PROJECT_ROOT = os.path.abspath(
        os.path.join(BASE_DIR, "../../")
    )

    IMAGE_PATH = os.path.join(
        PROJECT_ROOT,
        "datasets",
        "sky_images",
        "sky.jpg"
    )

    generate_observatory_report(
        IMAGE_PATH
    )