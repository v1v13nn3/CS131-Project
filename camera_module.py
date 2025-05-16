import cv2

def capture_frame(camera_id = 1):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise IOError("Cannot open camera")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise IOError("Failed to capture image")
    return frame