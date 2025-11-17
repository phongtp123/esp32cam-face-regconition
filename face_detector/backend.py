from flask import Response
import cv2 as cv
import time
import threading
import numpy as np
from appUtils import get_video_capture, release_video_capture
from mqtt import init_mqtt
from human_detect_test import non_max_suppression_fast
# face_cascade_path = "./haarcascade_frontalface_alt.xml"
# face_cascade = cv.CascadeClassifier(face_cascade_path)

hog = cv.HOGDescriptor()
hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())

motion_active = threading.Event() 

TOPIC_LED = "/server/led"
# TOPIC_LED_RESPOND = "/led/status"

def on_motion_change(motion_value):
    global motion_active
    if motion_value == 1:
        print("[MOTION] Detected motion , start stream")
        motion_active.set()
    elif motion_value == 0:
        print("[MOTION] No motion , pause stream")
        motion_active.clear()

client = init_mqtt(on_motion_change)

# save_dir = "./captured_faces"
# os.makedirs(save_dir, exist_ok=True)

# last_save_time = 0
# save_interval = 0.5

is_offline = True
attempt = 0

def generate_no_motion_frame(width=320, height=240):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    text = "NO MOTION"
    font = cv.FONT_HERSHEY_SIMPLEX
    thickness = 3

    font_scale = 2.0
    while True:
        text_size = cv.getTextSize(text, font, font_scale, thickness)[0]
        if text_size[0] <= width * 0.7:
            break
        font_scale -= 0.1
        if font_scale < 0.5:
            break

    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    cv.putText(frame, text, (text_x, text_y), font, font_scale, (0, 0, 255), thickness, cv.LINE_AA)
    return frame

def detect_frames():
    # global last_save_time
    global is_offline, attempt

    vc = get_video_capture()
    if vc is None or not vc.isOpened():
        print("[ERROR] Cannot open video capture")
        return
    
    # frame_id = 0

    while True:
        if not motion_active.is_set():
            frame = generate_no_motion_frame()
            ret, buffer = cv.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.1)
            continue
        else:
            ret, frame = vc.read()
            if not ret or frame is None:
                print("[WARN] Failed to read frame. Reconnecting...")
                release_video_capture()
                time.sleep(1.0)
                vc = get_video_capture()
                continue

            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray = cv.equalizeHist(gray)
            boxes, weights = hog.detectMultiScale(frame, winStride=(2,2), scale=1.15)

            boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
            confidences = [float(w) for w in weights]
            keep = non_max_suppression_fast(boxes, confidences, overlapThresh=0.5)

            # for i, (x, y, w, h) in enumerate(faces):
            #     cv.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)

            #     # current_time = time.time()
            #     # if current_time - last_save_time > save_interval:
            #     #     last_save_time = current_time

            #     #     face_img = frame[y:y + h, x:x + w]
            #     #     filename = os.path.join(save_dir, f"face_{int(time.time())}_{frame_id}.jpg")
            #     #     cv.imwrite(filename, face_img)
            #     #     print(f"[INFO] Saved face image: {filename}")
            #     #     frame_id += 1 

            if len(keep) > 0:
                # === Có khuôn mặt ===
                if is_offline:
                    print("[INFO] Human detected — Turning LED ON.")
                    client.publish(TOPIC_LED, '{"status":1}', qos=1)
                    is_offline = False
                attempt = 0  # reset counter

                for i in keep:
                    (xA, yA, xB, yB) = boxes[i]
                    cv.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

            else:
                # === Không có khuôn mặt ===
                attempt += 1
                if attempt >= 60:
                    if is_offline:
                        attempt = 0  # reset counter
                    else:
                        print("[INFO] No human detected after 3 seconds — Turning LED OFF.")
                        client.publish(TOPIC_LED, '{"status":0}', qos=1)
                        is_offline = True
                        attempt = 0  # reset counter
                    
            ret2, buffer = cv.imencode('.jpg', frame)
            if not ret2:
                continue

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
def register_backend_routes(app):
    """Đăng ký các route backend vào Flask app."""
    from flask import jsonify

    @app.route('/video_feed')
    def video_feed():
        return Response(detect_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/stop_capture')
    def stop_capture():
        release_video_capture()
        return jsonify({"status": "stopped"})