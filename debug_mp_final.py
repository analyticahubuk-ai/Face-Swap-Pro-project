try:
    import mediapipe.python.solutions.pose as pose
    print("YES: import mediapipe.python.solutions.pose")
except Exception as e:
    print(f"NO: mediapipe.python.solutions.pose: {e}")

try:
    from mediapipe.solutions import pose
    print("YES: from mediapipe.solutions import pose")
except Exception as e:
    print(f"NO: mediapipe.solutions: {e}")

try:
    import mediapipe as mp
    p = mp.solutions.pose
    print("YES: mp.solutions.pose")
except Exception as e:
    print(f"NO: mp.solutions.pose: {e}")
