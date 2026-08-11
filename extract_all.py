import cv2
import numpy as np
import os, glob

folder = "/Users/mdkasifuddin/.gemini/antigravity-ide/brain/05a83f3c-b6f1-449e-8acd-32367c0fcd40/.tempmediaStorage"
files = glob.glob(f"{folder}/media_*.png")
files.sort(key=os.path.getmtime, reverse=True)

logo_count = 0
for img_path in files[:10]:
    img = cv2.imread(img_path)
    if img is None: continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 120 < w < 800 and 120 < h < 800:
            ratio = w / h
            if 0.8 < ratio < 1.3:
                print(f"Found logo {logo_count} in {os.path.basename(img_path)} at {x},{y} size {w}x{h}")
                logo = img[y:y+h, x:x+w]
                cv2.imwrite(f"extracted_logo_{logo_count}.png", logo)
                logo_count += 1
