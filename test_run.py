from main import process_video
import glob

print("Starting test run...")
videos = glob.glob("video*.mp4")
print(f"Videos found: {videos}")
process_video("face.jpg", videos)
print("Test run complete.")
