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

        # Initialize FaceAnalysis with parsing if available
        # We try to use a model pack that includes parsing, or basic detection
        # 'buffalo_l' usually only has det, rec, gender. 
        # We will try to add a separate parsing model if possible, 
        # or rely on standard mask if parsing fails.
        try:
            self.app = FaceAnalysis(name='buffalo_l', allowed_modules=['detection', 'gender'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            # Load bisenet manually if possible for occlusion handling
            self.parser = insightface.model_zoo.get_model('bisnet_resnet18', download=False)
        except Exception as e:
            print(f"Warning: Could not load parser ({e}). Using default mask.")
            self.parser = None
            self.app = FaceAnalysis(name='buffalo_l')
            self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.swapper = insightface.model_zoo.get_model(self.model_file, download=False, download_zip=False)

    def download_model(self):
        if not os.path.exists(self.model_file):
            # ... (same download logic) ...
            pass 

    def get_face(self, img_data):
        faces = self.app.get(img_data)
        if not faces:
            return None
        return sorted(faces, key=lambda x: x.bbox[2]*x.bbox[3], reverse=True)[0]

    def process_frame(self, frame, source_face):
        target_faces = self.app.get(frame)
        res = frame.copy()
        
        for face in target_faces:
            # Standard Swap
            # This returns the whole image with the swap pasted back
            swapped_img = self.swapper.get(res, face, source_face, paste_back=True)
            
            # If we simply return swapped_img, we overwrite hands.
            # To fix hands: we need to trust the original image's "non-face" pixels more?
            # Or use segmentation.
            
            # WITHOUT SEGMENTATION MODEL:
            # We can try to blend based on difference, but that's risky.
            
            # WITH SEGMENTATION (Hypothetical):
            # mask = self.parser.get(frame, face) # Get mask for this face
            # res = blend based on mask
            
            # Fallback: Just return standard swap for now until we confirmed parser works
            res = swapped_img
            
        return res
