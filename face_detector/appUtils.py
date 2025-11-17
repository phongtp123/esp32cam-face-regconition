import cv2 as cv
import threading
import time

ESP32_STREAM_URL = "http://10.197.209.194/stream"

cap_lock = threading.Lock()
cap = None

def get_video_capture():
    """
    Trả về đối tượng cv.VideoCapture đang mở (hoặc mở mới nếu chưa có).
    """
    global cap
    with cap_lock:
        if cap is None or not cap.isOpened():
            print(f"[INFO] Opening VideoCapture to ESP32 stream: {ESP32_STREAM_URL}")
            cap = cv.VideoCapture(ESP32_STREAM_URL)
            time.sleep(0.5)
        return cap
    
def release_video_capture():
    """
    Giải phóng capture hiện tại (nếu có).
    """
    global cap
    with cap_lock:
        if cap is not None and cap.isOpened():
            cap.release()
            cap = None
            print("[INFO] Released VideoCapture")

