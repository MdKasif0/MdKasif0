#!/usr/env/bin python3
import sys
import cv2
import numpy as np
from rembg import remove
from PIL import Image

def prep_photo(input_path, output_path):
    print(f"Reading {input_path}...")
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"Error reading image: {e}")
        return

    print("Removing background...")
    # rembg requires a PIL image or bytes. remove() works on PIL images.
    img_no_bg = remove(img)
    
    # Convert to OpenCV format (numpy array)
    cv_img = cv2.cvtColor(np.array(img_no_bg), cv2.COLOR_RGBA2BGRA)
    
    # Extract alpha channel
    b, g, r, a = cv2.split(cv_img)
    
    # Convert to grayscale
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2GRAY)
    
    print("Applying CLAHE...")
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(gray)
    
    print("Compositing onto white background...")
    # Create white background
    white_bg = np.ones_like(cl1) * 255
    
    # Normalize alpha mask to 0-1
    alpha_mask = a.astype(float) / 255.0
    
    # Composite
    # Foreground (cl1) * alpha + Background (white) * (1 - alpha)
    foreground = cv2.multiply(alpha_mask, cl1.astype(float))
    background = cv2.multiply(1.0 - alpha_mask, white_bg.astype(float))
    out_img = cv2.add(foreground, background).astype(np.uint8)
    
    # Save
    cv2.imwrite(output_path, out_img)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        input_file = "profile-source.png"
        output_file = "source-prepped.png"
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    
    prep_photo(input_file, output_file)
