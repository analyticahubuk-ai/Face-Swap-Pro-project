from insightface.app import FaceAnalysis
import cv2
import numpy as np

app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=-1, det_size=(640, 640))

img = np.zeros((640, 640, 3), dtype=np.uint8)
# Create a fake face or just check class
faces = app.get(img)
if len(faces) == 0:
    # Check the Face object attributes by creating a dummy one if possible
    # Or just print the type of a detected face in a real image
    print("No face detected in black image, let's try to list help(faces)")
else:
    print(dir(faces[0]))
