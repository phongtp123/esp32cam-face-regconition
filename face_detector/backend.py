from flask import Response
import cv2 as cv
import time
from appUtils import get_video_capture, release_video_capture
from mqtt import init_mqtt

face_cascade_path = "./haarcascade_frontalface_alt.xml"
face_cascade = cv.CascadeClassifier(face_cascade_path)

TOPIC_LED = "/server/led"
TOPIC_LED_RESPOND = "/led/status"

client = init_mqtt()

# save_dir = "./captured_faces"
# os.makedirs(save_dir, exist_ok=True)

# last_save_time = 0
# save_interval = 0.5

is_offline = True
attempt = 0

def detect_frames():
    # global last_save_time
    global is_offline, attempt

    vc = get_video_capture()
    if vc is None or not vc.isOpened():
        print("[ERROR] Cannot open video capture")
        return
    
    # frame_id = 0

    while True:
        ret, frame = vc.read()
        if not ret or frame is None:
            print("[WARN] Failed to read frame. Reconnecting...")
            release_video_capture()
            time.sleep(1.0)
            vc = get_video_capture()
            continue

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray = cv.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

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

        if len(faces) > 0:
            # === Có khuôn mặt ===
            if is_offline:
                print("[INFO] Face detected — Turning LED ON.")
                client.publish(TOPIC_LED, '{"status":1}', qos=1)
                is_offline = False
            attempt = 0  # reset counter

            for (x, y, w, h) in faces:
                cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        else:
            # === Không có khuôn mặt ===
            attempt += 1
            if attempt >= 5:
                if is_offline:
                    attempt = 0  # reset counter
                else:
                    print("[INFO] No face detected after 3 tries — Turning LED OFF.")
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