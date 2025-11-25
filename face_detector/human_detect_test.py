import numpy as np
import cv2 as cv
from ultralytics import YOLO
import time

# hog = cv.HOGDescriptor()
# hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())

def non_max_suppression_fast(boxes, scores, overlapThresh=0.3):
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes)
    scores = np.array(scores)
    x1, y1, x2, y2 = boxes[:,0], boxes[:,1], boxes[:,2], boxes[:,3]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

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
        inds = np.where(iou <= overlapThresh)[0]
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

# def main():
#     # Load YOLOv8n pretrained COCO
#     model = YOLO("yolov8n.pt")

#     cap = cv.VideoCapture(0)

#     if not cap.isOpened():
#         print("[ERROR] Không mở được webcam!")
#         return

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("[WARN] Không lấy được frame!")
#             break

#         # Resize để tăng FPS, giống HOG
#         frame = cv.resize(frame, (320, 240))

#         # -----------------------------------------
#         # YOLO detection
#         # -----------------------------------------
#         results = model(frame, imgsz=320, conf=0.4, verbose=False)

#         # Lấy person box
#         detections = results[0].boxes

#         for box in detections:
#             cls = int(box.cls[0])
#             conf = float(box.conf[0])

#             # Chỉ giữ "person"
#             if cls != 0:
#                 continue

#             # Box yolo ở dạng (x1,y1,x2,y2)
#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

#             # Vẽ khung
#             cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv.putText(frame, f"{conf:.2f}", (x1, y1 - 5),
#                        cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

#         cv.imshow("YOLOv8n Human Detection (320x240)", frame)

#         # ESC để thoát
#         if cv.waitKey(1) & 0xFF == 27:
#             break

#     cap.release()
#     cv.destroyAllWindows()


# if __name__ == "__main__":
#     main()