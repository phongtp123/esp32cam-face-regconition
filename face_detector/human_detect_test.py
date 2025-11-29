import numpy as np
import cv2 as cv
from ultralytics import YOLO
import time
from tracker import TrackerManager
from appUtils import predict_batch, init_engine

# hog = cv.HOGDescriptor()
# hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())


tracker_manager = TrackerManager(iou_threshold=0.3, max_age=10)
extractor, classifier, device, _, _ = init_engine(nc=2, 
                                                               classifier_path="model_manual/ReID/log/osnet_x1_0/model/best_model_2.pth", 
                                                               reid_model_name="osnet_x1_0", reid_pretrained_path="model_manual/ReID/log/osnet_x1_0/model/osnet_x1_0_imagenet.pth")

def non_max_suppression_fast(boxes, confidences, non_overlap_thresh=0.2):
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes)
    confidences = np.array(confidences)
    x1, y1, x2, y2 = boxes[:,0], boxes[:,1], boxes[:,2], boxes[:,3]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = confidences.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(iou <= non_overlap_thresh)[0]
        order = order[inds + 1]

    return keep

# def main():
#     cap = cv.VideoCapture(0)  # Webcam mặc định

#     if not cap.isOpened():
#         print("[ERROR] Không mở được webcam!")
#         return

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("[WARN] Không lấy được frame!")
#             break

#         # Resize Confirm
#         frame = cv.resize(frame, (320, 240))

#         gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

#         # Detect
#         boxes, weights = hog.detectMultiScale(
#             gray,
#             winStride=(8, 8),
#             padding=(8, 8),
#             scale=1.02,
#             hitThreshold=0.5,
#         )

#         # print(weights)

#         # Convert box
#         boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
#         confidences = np.array([float(w) for w in weights])

#         # Lọc confidence < 0.6
#         conf_min = 0.6
#         indices = [i for i, c in enumerate(confidences) if c > conf_min]

#         if len(indices) > 0:
#             boxes = boxes[indices]
#             confidences = confidences[indices]

#             # NMS
#             keep = non_max_suppression_fast(boxes, confidences, overlapThresh=0.5)

#             # Vẽ
#             for i in keep:
#                 x1, y1, x2, y2 = boxes[i]
#                 cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#         cv.imshow("HOG Human Detection (320x240)", frame)

#         # ESC để thoát
#         if cv.waitKey(1) & 0xFF == 27:
#             break

#     cap.release()
#     cv.destroyAllWindows()


# if __name__ == "__main__":
#     main()

def main():

    # Load YOLOv8n pretrained COCO
    model = YOLO("yolov8n.pt")

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Không mở được webcam!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Không lấy được frame!")
            break

        # Resize để tăng FPS, giống HOG
        frame = cv.resize(frame, (320, 240))

        # -----------------------------------------
        # YOLO detection
        # -----------------------------------------
        results = model(frame, imgsz=320, conf=0.4, verbose=False)

        # Lấy person box
        detections = results[0].boxes
        det_boxes = []
        scores = []
        true_det_boxes = []

        for box in detections:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Chỉ giữ "person"
            if cls != 0:
                continue

            # Box yolo ở dạng (x1,y1,x2,y2)
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

            det_boxes.append([x1, y1, x2, y2])
            scores.append(conf)

        keep = non_max_suppression_fast(det_boxes, scores)
        if len(keep) > 0:
            for i in keep:
                true_det_boxes.append(det_boxes[i])
        
        tracks = tracker_manager.update(true_det_boxes)
        crop_bboxs = []
        for tr in tracks:
            x1,y1,x2,y2 = tr["box"]
            
            x1 = max(0, min(frame.shape[1]-1, int(x1)))
            y1 = max(0, min(frame.shape[0]-1, int(y1)))
            x2 = max(0, min(frame.shape[1]-1, int(x2)))
            y2 = max(0, min(frame.shape[0]-1, int(y2)))

            crop = frame[y1:y2, x1:x2]
            crop_bboxs.append(crop)

        if len(crop_bboxs) > 0:
            classes, confs = predict_batch(crop_bboxs, extractor, classifier, device)

        for idx, tr in enumerate(tracks):
            x1,y1,x2,y2 = tr["box"]
            if classes[idx] == 1:
                label = "phong"
            score = confs[idx]

            color = (0, 255, 0) if classes[idx] == 1 else (0, 0, 255)

            cv.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            if classes[idx] == 1:
                cv.putText(frame, f"{label} {score:.2f}", 
                        (x1, y1-5), cv.FONT_HERSHEY_SIMPLEX, 
                        0.5, color, 1)

        cv.imshow("YOLOv8n Human ReID Recognition (320x240)", frame)

        # ESC để thoát
        if cv.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()