import insightface
import numpy as np
import cv2
import os
from insightface.app import FaceAnalysis
try:
    import mediapipe as mp
    try:
        from mediapipe import solutions
        mp_pose = solutions.pose
    except ImportError:
        try:
            import mediapipe.python.solutions.pose as mp_pose
        except ImportError:
            mp_pose = mp.solutions.pose
except (ImportError, AttributeError):
    mp = None
    mp_pose = None

class FaceSwapper:
    def __init__(self):
        # Auto-download model if missing
        self.model_file = 'inswapper_128.onnx'
        self.download_model()

        # Initialize FaceAnalysis for detection
        # We use landmark_2d_106 for better masking
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.swapper = insightface.model_zoo.get_model(self.model_file, download=False, download_zip=False)

        # Initialize MediaPipe Pose for body tracking
        if mp_pose:
            self.mp_pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
            self.mp_pose_landmark = mp_pose.PoseLandmark
        else:
            print("Warning: MediaPipe not found. Outfit overlay will use fallback or be disabled.")
            self.mp_pose = None
            self.mp_pose_landmark = None

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

    def process_frame(self, frame, source_face, stabilize=True, state=None, outfit_img=None, outfit_type=None):
        """
        Processes a single frame: Swaps face, then overlays outfit.
        """
        res = frame.copy()
        
        # 1. Face Detection & Swap
        target_faces = self.app.get(res)
        target_face = None
        
        if target_faces:
             target_face = sorted(target_faces, key=lambda x: x.bbox[2]*x.bbox[3], reverse=True)[0]
             
             # Perform swap with manual masking for better fit (especially useful for hijabs)
             res = self.swap_with_mask(res, target_face, source_face)

        # 2. Virtual Outfit Overlay
        if outfit_img is not None:
             res = self.overlay_outfit(res, outfit_img, outfit_type=outfit_type, target_face=target_face)

        # 3. Stabilization/Crop (only if stabilize is True)
        if stabilize and target_face:
             return self.crop_and_focus(res, target_face, state=state)
        
        return res

    def swap_with_mask(self, target_img, target_face, source_face):
        """
        Swaps the face but applies a custom mask based on target landmarks 
        to ensure it doesn't bleed into hijabs or hoodies.
        """
        # Get the standard swap result first
        swapped_img = self.swapper.get(target_img, target_face, source_face, paste_back=True)
        
        # If no landmarks, return default paste_back
        if not hasattr(target_face, 'landmark_2d_106'):
            return swapped_img
            
        # Create a face skin mask from landmarks
        h, w = target_img.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        points = target_face.landmark_2d_106.astype(np.int32)
        hull = cv2.convexHull(points)
        cv2.drawContours(mask, [hull], -1, 255, -1)
        
        # Determine blur size based on face scale
        face_width = target_face.bbox[2] - target_face.bbox[0]
        blur_size = int(face_width / 15) * 2 + 1 
        blur_size = max(3, min(blur_size, 21))
        
        # Erode mask slightly to avoid capturing background hair/hijab
        kernel = np.ones((blur_size, blur_size), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        
        # Blur the mask for seamless blending
        mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
        
        # Sharpen the swapped_img slightly to match video sharpness if possible
        # We use a subtle blend of the original to keep textures
        sharpen_kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        swapped_img_sharp = cv2.filter2D(swapped_img.astype(np.float32), -1, sharpen_kernel)
        swapped_img = cv2.addWeighted(swapped_img.astype(np.float32), 0.7, swapped_img_sharp, 0.3, 0)
        swapped_img = np.clip(swapped_img, 0, 255).astype(np.uint8)

        # Convert mask to 3 channels [0-1]
        mask_alpha = mask.astype(float) / 255.0
        mask_alpha = np.stack([mask_alpha] * 3, axis=-1)
        
        # Blend original frame and swapped image using our custom mask
        result = (target_img.astype(float) * (1 - mask_alpha) + swapped_img.astype(float) * mask_alpha).astype(np.uint8)
        
        return result

    def overlay_outfit(self, frame, outfit, outfit_type=None, target_face=None):
        """
        Overlays an outfit PNG. 
        Uses Head-based positioning for Hijab/Hoodie.
        Uses Torso-based positioning for Suits/Shirts.
        """
        # Pre-process outfit: remove background if it's not transparent
        if outfit.shape[2] == 3:
            h_out, w_out = outfit.shape[:2]
            mask = np.zeros((h_out+2, w_out+2), np.uint8)
            bg_removed = cv2.cvtColor(outfit, cv2.COLOR_BGR2BGRA)
            for seed in [(0,0), (w_out-1, 0), (0, h_out-1), (w_out-1, h_out-1)]:
                cv2.floodFill(bg_removed, mask, seed, (255, 255, 255, 0), (5,5,5), (5,5,5), 4)
            outfit = bg_removed

        h, w, _ = frame.shape
        
        # Default positioning variables
        new_w, new_h = 0, 0
        center_x, top_y = 0, 0

        # Logic for Headgear (Hijab, Hoodie)
        if outfit_type in ['hijab', 'hoodie'] and target_face is not None:
            # Use face landmarks for precise headgear placement
            kps = target_face.kps # 5 keypoints: L_eye, R_eye, nose, L_mouth, R_mouth
            
            # Use distance between eyes for scale
            eye_dist = np.linalg.norm(kps[0] - kps[1])
            
            # Hijab width should be roughly 4x eye distance
            new_w = int(eye_dist * 4.5)
            aspect_ratio = outfit.shape[1] / outfit.shape[0]
            new_h = int(new_w / aspect_ratio)
            
            # Center on the face
            center_x = int((kps[0][0] + kps[1][0]) / 2)
            # Vertical position: align the "face hole" of the asset with the nose
            # This is an estimate; adjust 0.4 based on asset design
            top_y = int(kps[2][1] - (new_h * 0.45))
            
        else:
            # Fallback to Pose-based (Torso) for Suits
            if self.mp_pose is None:
                return frame
                
            results = self.mp_pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if not results.pose_landmarks:
                return frame
            
            lmkts = results.pose_landmarks.landmark
            l_sh = lmkts[self.mp_pose_landmark.LEFT_SHOULDER]
            r_sh = lmkts[self.mp_pose_landmark.RIGHT_SHOULDER]
            
            sh_width = abs(l_sh.x - r_sh.x) * w
            if sh_width < 10: return frame
            
            # Scaling for Suits
            new_w = int(sh_width * 1.8)
            aspect_ratio = outfit.shape[1] / outfit.shape[0]
            new_h = int(new_w / aspect_ratio)
            
            center_x = int((l_sh.x + r_sh.x) / 2 * w)
            top_y = int(min(l_sh.y, r_sh.y) * h) - int(new_h * 0.15)

        if new_w <= 0 or new_h <= 0: return frame
        
        resized_outfit = cv2.resize(outfit, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        x1, y1 = center_x - new_w // 2, top_y
        x2, y2 = x1 + new_w, y1 + new_h

        # Clip overlay to frame
        ox1, oy1 = max(0, x1), max(0, y1)
        ox2, oy2 = min(w, x2), min(h, y2)
        
        if ox2 <= ox1 or oy2 <= oy1: return frame

        # Calculate coordinates on the resized outfit
        sx1, sy1 = ox1 - x1, oy1 - y1
        sx2, sy2 = sx1 + (ox2 - ox1), sy1 + (oy2 - oy1)
        
        overlay_part = resized_outfit[sy1:sy2, sx1:sx2]
        alpha = overlay_part[:, :, 3] / 255.0
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

        for c in range(3):
            bg = frame[oy1:oy2, ox1:ox2, c].astype(float)
            fg = overlay_part[:, :, c].astype(float)
            frame[oy1:oy2, ox1:ox2, c] = (bg * (1 - alpha) + fg * alpha).astype(np.uint8)

        return frame

    def crop_and_focus(self, frame, face, target_size=720, padding=2.0, state=None):
        bbox = face.bbox
        curr_x = (bbox[0] + bbox[2]) / 2
        curr_y = (bbox[1] + bbox[3]) / 2
        curr_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * padding

        if state is not None:
            alpha = 0.15
            if 'x' not in state:
                state['x'], state['y'], state['size'] = curr_x, curr_y, curr_size
            else:
                state['x'] = state['x'] * (1 - alpha) + curr_x * alpha
                state['y'] = state['y'] * (1 - alpha) + curr_y * alpha
                state['size'] = state['size'] * (1 - alpha) + curr_size * alpha
            
            center_x, center_y, crop_size = state['x'], state['y'], state['size']
        else:
            center_x, center_y, crop_size = curr_x, curr_y, curr_size
        
        x1 = int(max(0, center_x - crop_size / 2))
        y1 = int(max(0, center_y - crop_size / 2))
        x2 = int(min(frame.shape[1], x1 + crop_size))
        y2 = int(min(frame.shape[0], y1 + crop_size))
        
        actual_size = min(x2 - x1, y2 - y1)
        if actual_size < 10: return frame
        
        cropped = frame[y1:y1+actual_size, x1:x1+actual_size]
        return cv2.resize(cropped, (target_size, target_size), interpolation=cv2.INTER_LANCZOS4)
