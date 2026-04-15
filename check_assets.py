import cv2
import numpy as np

def check_image(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"FAILED to read {path}")
        return
    
    print(f"Image: {path}")
    print(f"Shape: {img.shape}")
    
    if img.shape[2] == 4:
        alpha = img[:,:,3]
        print(f"Alpha range: {alpha.min()} - {alpha.max()}")
        print(f"Transparent pixels: {np.sum(alpha == 0)}")
        print(f"Opaque pixels: {np.sum(alpha == 255)}")
    else:
        print("No alpha channel")

check_image('static/assets/hoodie.png')
check_image('static/assets/hijab.png')
check_image('static/assets/suit.png')
