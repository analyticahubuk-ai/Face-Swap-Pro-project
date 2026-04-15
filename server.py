import shutil
import os
import uuid
from typing import List
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from swapper import FaceSwapper
from utils import get_video_info, create_video_writer, add_audio_to_video
import cv2

app = FastAPI()

# Mount static files (frontend)
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
# app.mount moved to bottom


# Global swapper instance (lazy load)
swapper_instance = None

def get_swapper():
    global swapper_instance
    if swapper_instance is None:
        print("Loading FaceSwapper model...")
        swapper_instance = FaceSwapper()
    return swapper_instance

def update_status(task_id, status, message=None, files=None):
    status_file = os.path.join("uploads", task_id, "status.json")
    data = {"status": status, "message": message, "files": files or []}
    import json
    with open(status_file, "w") as f:
        json.dump(data, f)

def process_swap_task(task_id: str, source_path: str, video_paths: List[str]):

    try:
        update_status(task_id, "processing", "Initializing models...")
        swapper = get_swapper()
        
        # Load source face
        img = cv2.imread(source_path)
        if img is None:
             raise ValueError("Could not read source image")
             
        source_face = swapper.get_face(img)
        
        if not source_face:
            update_status(task_id, "failed", "No face detected in source image.")
            return

        processed_files = []
        total = len(video_paths)
        
        for idx, v_path in enumerate(video_paths):
            msg = f"Processing video {idx+1}/{total}"
            update_status(task_id, "processing", msg)
            
            info = get_video_info(v_path)
            if not info:
                continue
                
            output_filename = f"swapped_{os.path.basename(v_path)}"
            output_path = os.path.join("outputs", task_id, output_filename)
            temp_output_path = os.path.join("outputs", task_id, f"temp_{output_filename}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Use original dimensions
            writer = create_video_writer(temp_output_path, info['fps'], info['width'], info['height'])
            cap = cv2.VideoCapture(v_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0
            
            stab_state = {}
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                new_frame = swapper.process_frame(
                    frame, 
                    source_face, 
                    stabilize=False, 
                    state=stab_state
                )

                writer.write(new_frame)
                
                current_frame += 1
                if current_frame % 5 == 0:
                    progress = int((current_frame / total_frames) * 100)
                    msg = f"Processing video {idx+1}/{total}: {progress}%"
                    update_status(task_id, "processing", msg)
            
            cap.release()
            writer.release()
            
            # Add audio from original video
            update_status(task_id, "processing", f"Adding audio for video {idx+1}/{total}")
            success = add_audio_to_video(v_path, temp_output_path, output_path)
            if not success:
                print(f"Failed to add audio for {v_path}. Falling back to mute video.")
                import shutil
                shutil.copy2(temp_output_path, output_path)
                
            # Remove temp video
            if os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except Exception as e:
                    print(f"Failed to remove temp file {temp_output_path}: {e}")
                    
            processed_files.append(output_filename)
            
        update_status(task_id, "completed", "All videos processed", processed_files)
        print(f"Task {task_id}: Completed")
            
    except Exception as e:
        print(f"Task {task_id} failed: {e}")
        import traceback
        traceback.print_exc()
        update_status(task_id, "failed", str(e))

@app.post("/swap")
async def swap_faces(
    background_tasks: BackgroundTasks,
    source_image: UploadFile = File(...),
    target_videos: List[UploadFile] = File(None),
    video_links: str = Form(None)
):
    try:
        task_id = str(uuid.uuid4())
        task_dir = os.path.join("uploads", task_id)
        os.makedirs(task_dir, exist_ok=True)
        
        # Save source image
        source_path = os.path.join(task_dir, source_image.filename)
        with open(source_path, "wb") as f:
            shutil.copyfileobj(source_image.file, f)
            
        video_paths = []
        
        # Save uploaded videos
        if target_videos:
            for video in target_videos:
                if video.filename:
                    v_path = os.path.join(task_dir, video.filename)
                    with open(v_path, "wb") as f:
                        shutil.copyfileobj(video.file, f)
                    video_paths.append(v_path)
            
        # Add video links
        if video_links:
            import json
            import requests
            links = json.loads(video_links)
            update_status(task_id, "queued", f"Downloading {len(links)} linked videos...")
            
            for idx, link in enumerate(links):
                try:
                    filename = f"link_{idx}_{link.split('/')[-1].split('?')[0]}"
                    if not filename.endswith('.mp4'): filename += ".mp4"
                    
                    v_path = os.path.join(task_dir, filename)
                    response = requests.get(link, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(v_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    video_paths.append(v_path)
                except Exception as e:
                    print(f"Failed to download link {link}: {e}")

        update_status(task_id, "queued", "Waiting to start...")
        background_tasks.add_task(process_swap_task, task_id, source_path, video_paths)

        return {"task_id": task_id, "message": "Processing started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/status/{task_id}")
def get_status(task_id: str):
    status_file = os.path.join("uploads", task_id, "status.json")
    if not os.path.exists(status_file):
        return {"status": "unknown", "message": "Task not found"}
    
    import json
    try:
        with open(status_file, "r") as f:
            data = json.load(f)
        
        if data["status"] == "completed":
            data["download_url"] = f"/download/{task_id}"
            
        return data
    except:
        return {"status": "unknown", "message": "Error reading status"}

@app.get("/download/{task_id}/{filename}")
def download_file(task_id: str, filename: str):
    path = os.path.join("outputs", task_id, filename)
    return FileResponse(path)

# Mount static files last to allow API routes to take precedence
app.mount("/", StaticFiles(directory="static", html=True), name="static")
