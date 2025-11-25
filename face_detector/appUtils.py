import cv2 as cv
import threading
import time
import os

# ESP32_STREAM_URL = "http://10.54.117.194/stream"
ESP32_STREAM_URL = "http://10.197.209.194/stream"

VIDEO_DIR = "data/videos"

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


def init_video_writer(classname):
    global video_writer, video_filename
    os.makedirs(os.path.join(VIDEO_DIR, classname), exist_ok=True)

    video_filename = os.path.join(
        VIDEO_DIR, classname ,f"{classname}_{int(time.time())}.mp4"
    )

    # Ghi video định dạng mp4v hoặc H264 nếu OpenCV support
    fourcc = cv.VideoWriter_fourcc(*"mp4v")
    video_writer = cv.VideoWriter(video_filename, fourcc, 15, (320, 240))

    print(f"[VIDEO] Recording started: {video_filename}")