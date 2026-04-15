import cv2
import numpy as np

# Create a black video with a moving white rectangle
width, height = 640, 480
fps = 30
seconds = 3
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('video1.mp4', fourcc, fps, (width, height))

for i in range(fps * seconds):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Draw a face-like circle (yellow)
    center_x = int(width/2 + 100 * np.sin(i/10))
    center_y = int(height/2)
    cv2.circle(frame, (center_x, center_y), 50, (0, 255, 255), -1)
    
    # Eyes
    cv2.circle(frame, (center_x - 15, center_y - 15), 5, (0, 0, 0), -1)
    cv2.circle(frame, (center_x + 15, center_y - 15), 5, (0, 0, 0), -1)
    # Mouth
    cv2.ellipse(frame, (center_x, center_y + 15), (20, 10), 0, 0, 180, (0, 0, 0), -1)
    
    out.write(frame)

out.release()
print("Created video1.mp4")
