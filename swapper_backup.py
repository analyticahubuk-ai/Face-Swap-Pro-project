import insightface
import numpy as np
import cv2
import os
from insightface.app import FaceAnalysis

class FaceSwapper:
    def __init__(self):
        # Auto-download model if missing
        self.model_file = 'inswapper_128.onnx'
        self.download_model()

        # Initialize FaceAnalysis for detection
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.swapper = insightface.model_zoo.get_model(self.model_file, download=False, download_zip=False)

    def download_model(self):
        if not os.path.exists(self.model_file):
            print(f"Downloading {self.model_file}...")
            url = "https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx"
            import requests
            from tqdm import tqdm
            response = requests.get(url, stream=True)
            with open(self.model_file, "wb") as f:
                for chunk in tqdm(response.iter_content(chunk_size=8192)):
                    f.write(chunk)
            print("Download complete.")

    def get_face(self, img_data):
        faces = self.app.get(img_data)
        if not faces:
            return None
        # Return the largest face found
        return sorted(faces, key=lambda x: x.bbox[2]*x.bbox[3], reverse=True)[0]

    def process_frame(self, frame, source_face):
        # Detect faces in the target frame
        target_faces = self.app.get(frame)
        
        res = frame.copy()
        for face in target_faces:
            # Perform the swap
            res = self.swapper.get(res, face, source_face, paste_back=True)
            
        return res
