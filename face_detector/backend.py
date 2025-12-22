from flask import Response, stream_with_context
import cv2 as cv
import time
import os
import threading
import numpy as np
from appUtils import non_max_suppression_fast, predict_batch, init_full_engine, init_nonid_engine, ESP32_STREAM_URL, init_log_queue, push_log, TrendWindow, analyze_trend, same_person
from mqtt import init_mqtt
import requests

motion_active = threading.Event() 

current_mode = "non-strict"
TOPIC_LED = "/server/led"
VIDEO_DIR = "data/videos"

is_offline=True
attempt_no_person=0
attempt_person = 0
HUMAN_ON_THRESHOLD = 10
HUMAN_OFF_THRESHOLD = 120
LID_NEW_T = 1.5
LID_REAPPEAR_T = 0.7
MAX_LID_TRACK_T = 2.0
FAMILIER_ATTEMPT_THRESHOLD = 5
STRANGER_ATTEMPT_THRESHOLD = 60
NUM_PERSON_INIT = 1
REID_INTERVAL = 5

# is_recording=False
# video_writer=None


def on_motion_change(motion_value):
    global motion_active
    if motion_value == 1:
        print("[MOTION] Detected motion , start stream")
        motion_active.set()
    elif motion_value == 0:
        print("[MOTION] No motion , pause stream")
        motion_active.clear()

client = init_mqtt(on_motion_change)



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



def StrictID_Mode():

    extractor, classifier, model, tracker_manager, device, flags = init_full_engine(
        nc=3,
        classifier_path="model_manual/ReID/log/osnet_x1_0/model/osnetainx10_extractor.pth",
        reid_model_name="osnet_ain_x1_0",
        reid_pretrained_path="model_manual/ReID/log/osnet_x1_0/model/osnet_ain_x1_0_imagenet.pth",
        yolo_path="yolov8n.pt"
    )

    global is_offline, attempt_no_person, attempt_person
    # global video_writer, is_recording
    print_once = False
    attempt_stranger=0
    attempt_familier=0
    frame_id = 0
    reid_cache = {}

    while True:
        ok = True
        for key, value in flags.items():
            if value != 1 and print_once:
                push_log(f"Init failed at key: {key}")
                ok = False

        print_once = True

        if ok:
            push_log("INIT ENGINE OK")
            push_log("CLEAR")   # web sẽ clear UI log
            break

        # gửi frame no-motion trong lúc chờ
        frame = generate_no_motion_frame()
        _, buffer = cv.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.2)

    # mở stream HTTP MJPEG
    while True:
        try:
            print("[INFO] Connecting to ESP32 stream...")
            stream = requests.get(ESP32_STREAM_URL, stream=True, timeout=20)

            if stream.status_code != 200:
                print("[ERROR] Cannot connect, retrying...")
                time.sleep(1)
                continue

            push_log("DONE")

            bytes_data = bytearray()

            for chunk in stream.iter_content(chunk_size=1024):

                # ===== nếu motion inactive: gửi frame no-motion =====
                if not motion_active.is_set():
                    frame_id = 0
                    frame = generate_no_motion_frame()
                    _, buffer = cv.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(0.1)
                    continue

                # ===== parse MJPEG =====
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')

                if a == -1 or b == -1:
                    continue

                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]

                frame_id += 1
                frame = cv.imdecode(np.frombuffer(jpg, np.uint8), cv.IMREAD_COLOR)
                frame = cv.resize(frame, (320, 240))

                # ===== YOLO detect =====
                results = model(frame, imgsz=320, conf=0.4, verbose=False)
                detections = results[0].boxes

                det_boxes = []
                scores = []
                true_det_boxes = []
                found_familiar = False   # reset mỗi frame

                for box in detections:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls != 0:
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    det_boxes.append([x1, y1, x2, y2])
                    scores.append(conf)

                if len(det_boxes) > 0:
                    attempt_no_person = 0
                    # ===== NMS =====
                    keep = non_max_suppression_fast(det_boxes, scores)
                    for i in keep:
                        true_det_boxes.append(det_boxes[i])

                    # ===== Tracker =====
                    tracks = tracker_manager.update(true_det_boxes)

                    crop_bboxs = []
                    for tr in tracks:
                        x1,y1,x2,y2 = map(int, tr["box"])
                        crop = frame[y1:y2, x1:x2]
                        crop = cv.resize(crop, (256, 128))
                        crop_bboxs.append(crop)

                    if frame_id % REID_INTERVAL == 0 and len(crop_bboxs) > 0:
                        classes, confs = predict_batch(crop_bboxs, extractor, classifier, device)
                        for idx, tr in enumerate(tracks):
                            tid = tr["id"]
                            reid_cache[tid] = (classes[idx], confs[idx])
                        # ===== Draw + logic =====
                    for tr in tracks:
                        x1,y1,x2,y2 = map(int, tr["box"])
                        tid = tr["id"]
                        if tid in reid_cache:
                            classes, conf = reid_cache[tid]
                        else:
                            classes, conf = -1, 0.0

                        color = (0,255,0) if classes in (1,2) else (0,0,255)

                        if classes == 1:
                            found_familiar = True
                            person_name = "PHONG"
                            cv.putText(frame, f"{person_name} {conf:.2f}",
                                    (x1, y1-5), cv.FONT_HERSHEY_DUPLEX,
                                    0.5, color, 2)
                        
                        if classes == 2:
                            found_familiar = True
                            person_name = "TUNG"
                            cv.putText(frame, f"{person_name} {conf:.2f}",
                                    (x1, y1-5), cv.FONT_HERSHEY_DUPLEX,
                                    0.5, color, 2)

                        cv.rectangle(frame, (x1,y1), (x2,y2), color, 2)                            

                    # ===== LED logic =====
                    if found_familiar:
                        attempt_familier += 1
                        if is_offline and attempt_familier >= FAMILIER_ATTEMPT_THRESHOLD:
                            print("[INFO] Familiar detected -> LED ON")
                            client.publish(TOPIC_LED, '{"status":1}', qos=1)
                            is_offline = False
                        attempt_stranger = 0
                    else:
                        attempt_stranger += 1
                        if attempt_stranger >= STRANGER_ATTEMPT_THRESHOLD and not is_offline:
                            print("[INFO] No familiar for 3 sec -> LED OFF")
                            client.publish(TOPIC_LED, '{"status":0}', qos=1)
                            is_offline = True
                            attempt_stranger = 0

                else:
                    # ===== Không có người =====
                    attempt_no_person += 1
                    if attempt_no_person >= 10 and not is_offline:
                        print("[INFO] No human for 3 sec -> LED OFF")
                        client.publish(TOPIC_LED, '{"status":0}', qos=1)
                        is_offline = True
                        attempt_no_person = 0

                for tid in list(reid_cache.keys()):
                    if tid not in [tr["id"] for tr in tracks]:
                        reid_cache.pop(tid, None)

                # ===== trả frame ra HTTP server =====
                _, buffer = cv.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print("[ERROR] Stream dropped -> reconnecting...", e)
            time.sleep(1)
            continue
            
def Non_StrictID_Mode():

    global is_offline, attempt_no_person, attempt_person
    # global video_writer, is_recording
    print_once = False
    size_windows = {}
    logical_tracks = {}
    tracker_to_logical = {}
    logical_id_counter = 0
    person_counter = NUM_PERSON_INIT

    model, tracker_manager, flags = init_nonid_engine(
        yolo_path="yolov8n.pt"
    )

    while True:
        ok = True
        for key, value in flags.items():
            if value != 1 and print_once:
                push_log(f"Init failed at key: {key}")
                ok = False

        print_once = True

        if ok:
            push_log("INIT ENGINE OK")
            push_log("CLEAR")   # web sẽ clear UI log
            break

        # gửi frame no-motion trong lúc chờ
        frame = generate_no_motion_frame()
        _, buffer = cv.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.2)
    
    while True:
        try:
            print("[INFO] Connecting to ESP32 stream...")
            stream = requests.get(ESP32_STREAM_URL, stream=True, timeout=20)

            if stream.status_code != 200:
                print("[ERROR] Cannot connect, retrying...")
                time.sleep(1)
                continue

            push_log("DONE")

            bytes_data = bytearray()

            for chunk in stream.iter_content(chunk_size=1024):
                if not motion_active.is_set():
                    # if is_recording:
                    #     print("[VIDEO] Motion stopped -> Saving file...")

                    #     if video_writer is not None:
                    #         try:
                    #             video_writer.release()
                    #             print("[VIDEO] File saved.")
                    #         except Exception as e:
                    #             print("[VIDEO] Error releasing writer:", e)

                    #     video_writer = None
                    #     is_recording = False
                    frame = generate_no_motion_frame()
                    _, buffer = cv.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(0.1)
                    continue
                else:
                    # if not is_recording:
                    #     init_video_writer("phong")
                    #     is_recording = True
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    b = bytes_data.find(b'\xff\xd9')

                    if a == -1 or b == -1:
                        continue

                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]

                    frame = cv.imdecode(np.frombuffer(jpg, np.uint8), cv.IMREAD_COLOR)
                    frame = cv.resize(frame, (320, 240))

                    # if video_writer is not None:
                    #     video_writer.write(frame)

                    results = model(frame, imgsz=320, conf=0.4, iou=0.5, verbose=False)
                    detections = results[0].boxes
                    det_boxes = []
                    scores = []
                    true_det_boxes = []

                    for box in detections:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])

                        if cls != 0:
                            continue

                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        det_boxes.append([x1, y1, x2, y2])
                        scores.append(conf)

                    if len(det_boxes) > 0:
                        attempt_person += 1
                        if attempt_person >= HUMAN_ON_THRESHOLD and person_counter >= 1 and is_offline:
                            print("Someone inside. Turning LED ON")
                            client.publish(TOPIC_LED, '{"status":1}', qos=1)
                            is_offline = False
                        attempt_no_person = 0  # reset counter
                        keep = non_max_suppression_fast(det_boxes, scores)

                        for i in keep:
                            true_det_boxes.append(det_boxes[i])

                        tracks = tracker_manager.update(true_det_boxes)
                        aliased_tracks = []
                        now = time.time()
                        for tr in tracks:
                            tid = tr["id"]
                            box = tr["box"]

                            # Nếu tracker ID đã có logical ID
                            if tid in tracker_to_logical:
                                lid = tracker_to_logical[tid]
                                logical_tracks[lid]["last_box"] = box
                                logical_tracks[lid]["last_time"] = now

                            else:
                                # thử ghép với logical ID cũ (track đã mất)
                                matched_lid = None
                                for lid, info in logical_tracks.items():
                                    time_gap = now - info["last_time"]
                                    if time_gap >= LID_NEW_T:
                                        continue
                                    if time_gap <= LID_REAPPEAR_T:
                                        if same_person(info["last_box"], box, time_gap):
                                            matched_lid = lid
                                            break

                                if matched_lid is not None:
                                    tracker_to_logical[tid] = matched_lid
                                    logical_tracks[matched_lid]["last_box"] = box
                                    logical_tracks[matched_lid]["last_time"] = now
                                else:
                                    # tạo logical ID mới
                                    logical_id_counter += 1
                                    lid = logical_id_counter
                                    tracker_to_logical[tid] = lid
                                    logical_tracks[lid] = {
                                        "last_box": box,
                                        "last_time": now
                                    }
                                    size_windows[lid] = TrendWindow()

                            aliased_tracks.append({
                                "logical_id": tracker_to_logical[tid],
                                "tracker_id": tid,
                                "box": box
                            })
                        for tr in aliased_tracks:
                            lid = tr["logical_id"]
                            x1,y1,x2,y2 = tr["box"]
                            x1 = max(0, min(frame.shape[1]-1, int(x1)))
                            y1 = max(0, min(frame.shape[0]-1, int(y1)))
                            x2 = max(0, min(frame.shape[1]-1, int(x2)))
                            y2 = max(0, min(frame.shape[0]-1, int(y2)))
                            cx = int((x2 + x1) / 2)
                            # area = abs(x2 - x1) * abs(y2 - y1)
                            if lid not in size_windows:
                                size_windows[lid] = TrendWindow()
                            win = size_windows[lid]
                            if win.start_time is None:
                                win.start_time = now
                            win.cx.append(cx)
                            trend = analyze_trend(win.cx)
                            if trend != "UNKNOWN":
                                if trend == "IN":
                                    person_counter += 1
                                    print(f"WALK {trend}")
                                    print(f"counter: {person_counter}")
                                else:
                                    person_counter -= 1
                                    print(f"WALK {trend}")
                                    print(f"counter: {person_counter}")
                                win.reset() 
                            elif now - win.start_time >= 20.0:
                                win.reset()
                                
                            cv.rectangle(frame, (x1,y1), (x2,y2), (0, 255, 0), 2)
                            cv.putText(frame, f"{lid}",
                                    (x1, y1-1), cv.FONT_HERSHEY_DUPLEX,
                                    0.5, (0,0,255), 2)
                    else:
                        # === Không có người ===
                        attempt_no_person += 1
                        attempt_person = 0
                        if attempt_no_person >= HUMAN_OFF_THRESHOLD and person_counter == 0:       # Assume FPS is 20
                            if is_offline:
                                attempt_no_person = 0  # reset counter
                            else:
                                print("[INFO] Nobody in room. Turning LED OFF")
                                client.publish(TOPIC_LED, '{"status":0}', qos=1)
                                is_offline = True
                                attempt_no_person = 0  # reset counter

                    cv.putText(frame, f"PC: {person_counter}",
                                    (0, 10), cv.FONT_HERSHEY_DUPLEX,
                                    0.5, (0,0,0), 2)
                    to_remove = []
                    for lid, info in logical_tracks.items():
                        if now - info["last_time"] > MAX_LID_TRACK_T:
                            to_remove.append(lid)

                    for removed_lid in to_remove:
                        logical_tracks.pop(removed_lid, None)
                        for tid, lid in list(tracker_to_logical.items()):
                            if lid == removed_lid:
                                tracker_to_logical.pop(tid, None)
                        size_windows.pop(removed_lid, None)

                    _, buffer = cv.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
        except Exception as e:
            print("[ERROR] Stream dropped -> reconnecting...", e)
            time.sleep(1)
            continue

def register_backend_routes(app):
    """Đăng ký các route backend vào Flask app."""
    from flask import jsonify

    @app.route('/video_feed')
    def video_feed():
        def gen():
            global current_mode
            last_mode = None
            while True:
                if current_mode != last_mode:
                    last_mode = current_mode
                    push_log(f"Initializing engine for mode: {last_mode}")
                    if last_mode == "strict":
                        engine_gen = StrictID_Mode()
                    else:
                        engine_gen = Non_StrictID_Mode()

                try:
                    frame = next(engine_gen)
                    yield frame
                except StopIteration:
                    continue
                except Exception as e:
                    push_log(f"Error in generator: {e}")
                    time.sleep(1)
                    continue

        return Response(stream_with_context(gen()), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route("/set_mode/<mode>")
    def set_mode(mode):
        global current_mode
        if mode not in ["strict", "non-strict"]:
            return {"error": "Invalid mode"}, 400

        current_mode = mode
        push_log(f"Switched to mode: {mode}")
        return {"status": "ok", "mode": current_mode}
    
    @app.route("/init_log")
    def init_log():
        def stream():
            while True:
                msg = init_log_queue.get()
                yield f"data: {msg}\n\n"
        return Response(stream(), mimetype="text/event-stream")