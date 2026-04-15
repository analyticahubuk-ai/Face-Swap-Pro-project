import cv2
import os

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    cap.release()
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": total_frames
    }

def create_video_writer(output_path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    return cv2.VideoWriter(output_path, fourcc, fps, (width, height))

def add_audio_to_video(original_video_path, target_video_path, final_output_path):
    """
    Extracts audio from the original video and adds it to the target video.
    Returns True if successful, False otherwise.
    """
    try:
        from moviepy.editor import VideoFileClip
        
        # Load both videos
        original_clip = VideoFileClip(original_video_path)
        target_clip = VideoFileClip(target_video_path)
        
        # Check if original video has audio
        if original_clip.audio is not None:
            # Set the audio of the target clip to the original audio
            final_clip = target_clip.set_audio(original_clip.audio)
            # Write the result
            # using libx264 for better compatibility and audio_codec aac
            final_clip.write_videofile(
                final_output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None,    # Disable the progress bar in console
                preset='fast'
            )
        else:
            # No audio in original, just copy target to final destination
            import shutil
            shutil.copy2(target_video_path, final_output_path)
            
        # Clean up resources
        original_clip.close()
        target_clip.close()
        return True
    except Exception as e:
        print(f"Error adding audio: {e}")
        return False
