import cv2
import os
import numpy as np
from swapper import FaceSwapper

def test_swap_with_hijab():
    print("Initializing Swapper for Test...")
    swapper = FaceSwapper()
    
    source_path = "face.jpg"
    video_path = "video1.mp4"
    outfit_path = "static/assets/hijab.png"
    output_path = "outputs/test_hijab_output.mp4"
    
    os.makedirs("outputs", exist_ok=True)
    
    # Load source face
    img = cv2.imread(source_path)
    if img is None:
        print("Error: face.jpg not found.")
        return
        
    source_face = swapper.get_face(img)
    if not source_face:
        print("Error: No face detected in source.")
        return
        
    # Load hijab asset
    outfit_img = cv2.imread(outfit_path, cv2.IMREAD_UNCHANGED)
    if outfit_img is None:
        print(f"Error: {outfit_path} not found.")
        return

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: {video_path} not found.")
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing {min(30, total_frames)} frames for validation...")
    
    # Process first 30 frames to check accuracy
    for i in range(min(30, total_frames)):
        ret, frame = cap.read()
        if not ret: break
        
        # We test the core logic: face swap + hijab overlay
        # We'll use the same logic as server.py
        new_frame = swapper.process_frame(
            frame, 
            source_face, 
            stabilize=False, 
            outfit_img=outfit_img,
            outfit_type='hijab'
        )
        writer.write(new_frame)
        if i % 10 == 0:
            print(f"Frame {i} processed...")
            # Save a sample frame to see result
            cv2.imwrite(f"outputs/sample_frame_{i}.jpg", new_frame)

    cap.release()
    writer.release()
    print(f"Test completed. Output saved to {output_path} and sample frames in outputs/")

if __name__ == "__main__":
    test_swap_with_hijab()
