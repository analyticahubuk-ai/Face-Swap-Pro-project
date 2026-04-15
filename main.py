import cv2
import os
import argparse
from tqdm import tqdm
from swapper import FaceSwapper
from utils import get_video_info, create_video_writer, add_audio_to_video
import requests

def download_model():
    url = "https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx"
    if not os.path.exists("inswapper_128.onnx"):
        print("Model not found. Downloading inswapper_128.onnx...")
        response = requests.get(url, stream=True)
        with open("inswapper_128.onnx", "wb") as f:
            for chunk in tqdm(response.iter_content(chunk_size=8192)):
                f.write(chunk)
        print("Download complete.")

def process_video(source_img_path, video_paths):
    download_model()
    
    print("Initializing Face Swapper...")
    swapper = FaceSwapper()
    
    # Load source image
    source_img = cv2.imread(source_img_path)
    if source_img is None:
        print(f"Error: Could not read source image {source_img_path}")
        return

    # Get source face embedding
    source_face = swapper.get_face(source_img)
    if source_face is None:
        print("Error: No face detected in source image.")
        return
    
    print("Source face detected.")

    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"Skipping {video_path}: File not found.")
            continue
            
        print(f"Processing {video_path}...")
        info = get_video_info(video_path)
        if not info:
             print(f"Error: Could not read video {video_path}")
             continue
             
        output_path = f"swapped_{os.path.basename(video_path)}"
        temp_output_path = f"temp_{output_path}"
        writer = create_video_writer(temp_output_path, info['fps'], info['width'], info['height'])
        
        cap = cv2.VideoCapture(video_path)
        
        # Process frames
        pbar = tqdm(total=info['total_frames'])
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            new_frame = swapper.process_frame(frame, source_face)
            writer.write(new_frame)
            pbar.update(1)
            
        pbar.close()
        cap.release()
        writer.release()
        
        print("Adding audio...")
        success = add_audio_to_video(video_path, temp_output_path, output_path)
        if not success:
            print(f"Failed to add audio for {video_path}. Falling back to mute video.")
            import shutil
            shutil.copy2(temp_output_path, output_path)
            
        if os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except Exception as e:
                pass
                
        print(f"Saved to {output_path}")

if __name__ == "__main__":
    # Example usage: Change these paths or use argparse
    # For now, we will ask the user for inputs or look for default files
    import glob
    
    # Simple interactive CLI
    source_image = input("Enter path to source face image (e.g., face.jpg): ").strip()
    
    # Find all mp4 files if no specific videos given, or ask user?
    # Requirement: 5 videos. Let's ask for a list or directory.
    print("Enter paths to 5 videos (comma separated) OR press Enter to process all MP4s in current folder:")
    video_input = input().strip()
    
    if not video_input:
        videos = glob.glob("*.mp4")
        # Filter out swapped versions to avoid recursion
        videos = [v for v in videos if not v.startswith("swapped_")]
    else:
        videos = [v.strip() for v in video_input.split(',')]
        
    if not videos:
        print("No videos found to process.")
    else:
        print(f"Found {len(videos)} videos: {videos}")
        process_video(source_image, videos)
