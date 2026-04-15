import cv2
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import os
import sys

def analyze_swapped_video(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"--- Video Metadata ---")
    print(f"File: {os.path.basename(video_path)}")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps:.2f}")
    print(f"Total Frames: {frame_count}")
    print(f"Duration: {frame_count / fps:.2f} seconds")

    # Initialize FaceAnalysis to check detection consistency
    # (Using the same model as in swapper.py)
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640)) # Use CPU for analysis

    detection_counts = 0
    sampled_frames = []
    
    # Analyze every 10th frame for efficiency
    sample_rate = 10
    total_samples = 0
    
    print("\n--- Detection Analysis ---")
    for i in range(0, frame_count, sample_rate):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        
        faces = app.get(frame)
        total_samples += 1
        if faces:
            detection_counts += 1
            # Check for landmarks
            if hasattr(faces[0], 'landmark_2d_106'):
                pass # Good
        
        if i % 50 == 0:
            print(f"Processed frame {i}/{frame_count}...")

    detection_rate = (detection_counts / total_samples) * 100 if total_samples > 0 else 0
    print(f"\nFace Detection Rate (sampled): {detection_rate:.2f}%")
    
    if detection_rate < 90:
        print("Warning: Low face detection rate detected in output video.")
    else:
        print("Face detection is highly consistent in the output video.")

    cap.release()

if __name__ == "__main__":
    target_video = r"c:\Users\RAKSHITH.R.R\Downloads\Faceswap_project\outputs\271d6199-882f-4246-884e-8db10aff1231\swapped_mixkit-boxer-is-knocked-out-when-getting-hit-in-a-ring-40969-hd-ready.mp4"
    analyze_swapped_video(target_video)
