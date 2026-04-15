import insightface
import cv2
import os

try:
    print("Attempting to load face parsing model...")
    # Common names for parsing models in insightface zoo
    parser = insightface.model_zoo.get_model('bisnet_resnet18', download=False)
    # parser = insightface.model_zoo.get_model('farl', download=True) 
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

# Try another way using FaceAnalysis
from insightface.app import FaceAnalysis
try:
    print("Checking FaceAnalysis for parsing...")
    app = FaceAnalysis(allowed_modules=['detection', 'parsing'])
    app.prepare(ctx_id=0)
    print("FaceAnalysis prepared.")
except Exception as e:
    print(f"FaceAnalysis Init Failed: {e}")
