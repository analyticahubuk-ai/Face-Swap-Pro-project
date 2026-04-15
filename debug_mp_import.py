import mediapipe
print(f"Mediapipe file: {mediapipe.__file__}")
try:
    import mediapipe.python.solutions as solutions
    print("Success: import mediapipe.python.solutions")
except ImportError as e:
    print(f"Fail: import mediapipe.python.solutions: {e}")

try:
    from mediapipe import solutions
    print("Success: from mediapipe import solutions")
except ImportError as e:
    print(f"Fail: from mediapipe import solutions: {e}")

try:
    import mediapipe as mp
    print(f"mp.solutions exists: {hasattr(mp, 'solutions')}")
except ImportError as e:
    print(f"Fail: import mediapipe as mp: {e}")
