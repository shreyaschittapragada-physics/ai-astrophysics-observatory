import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import sqlite3
import time

def log_star_metrics(image_path, star_count, brightest_star, avg_area):
    db_path = os.path.join('backend', 'services', 'database', 'astronomy_history.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO star_detection_metrics 
            (timestamp, image_name, stars_detected, brightest_star_pixel_value, average_star_area)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, os.path.basename(image_path), star_count, brightest_star, avg_area))
        conn.commit()

def detect_stars(image_path, show_plots=False):
    img = cv2.imread(image_path)
    if img is None: raise FileNotFoundError(f'Cannot load: {image_path}')
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, threshold = cv2.threshold(blur, 185, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    star_count = 0
    star_areas = []
    brightest_star = 0
    output = img.copy()
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if 2 < area < 20:
            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(output, (center_x, center_y), 8, (0, 255, 0), 1)
            star_areas.append(area)
            val = int(gray[center_y, center_x])
            if val > brightest_star: brightest_star = val
            star_count += 1
            
    avg_area = round(np.mean(star_areas), 3) if star_areas else 0
    
    if show_plots:
        plt.figure(figsize=(5, 5))
        plt.imshow(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
        plt.title(f'Stars Detected: {star_count}')
        plt.axis('off')
        plt.show()
        
    try:
        log_star_metrics(image_path, star_count, brightest_star, avg_area)
    except Exception:
        pass
        
    return {'stars_detected': star_count, 'brightest_star': brightest_star, 'average_star_area': avg_area}