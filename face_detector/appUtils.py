import cv2 as cv
import threading
import time
import numpy as np

import torch
import torch.serialization
from torchreid.reid.utils import FeatureExtractor
from model_manual.ReID.utils import Classifier
from tracker import TrackerManager
from ultralytics import YOLO
import queue

# ESP32_STREAM_URL = "http://10.54.117.194/stream"
ESP32_STREAM_URL = "http://10.197.209.194/stream"


cap_lock = threading.Lock()
init_log_queue = queue.Queue()
cap = None

def push_log(msg):
    print("[INIT]", msg)
    init_log_queue.put(msg)

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


def init_full_engine(nc, 
                classifier_path, 
                reid_model_name, 
                reid_pretrained_path, 
                yolo_path, 
                iou_threshold=0.3, 
                max_age=10):
    
    torch.serialization.add_safe_globals([np.dtype, np.core.multiarray.scalar])
    device = "cuda" if torch.cuda.is_available() else "cpu"

    flags = {}

    try:
        classifier = Classifier(num_class=nc).to(device)
        classifier.load_state_dict(torch.load(classifier_path, map_location=device))
        classifier.eval()
        flags["classifier_flag"] = 1
        push_log("Classifier loaded OK")
        print("[OK] Classifier loaded.")
    except Exception as e:
        flags["classifier_flag"] = 0
        push_log(f"[ERROR] Cannot load classifier: {e}")
        print("[ERROR] Cannot load classifier:", e)
        classifier = None

    try:
        extractor = FeatureExtractor(
            model_name=reid_model_name,
            model_path=reid_pretrained_path,
            device=device
        )
        flags["extractor_flag"] = 1
        push_log("ReID extractor loaded OK")
        print("[OK] ReID extractor loaded.")
    except Exception as e:
        flags["extractor_flag"] = 0
        push_log(f"[ERROR] Cannot load ReID extractor: {e}")
        print("[ERROR] Cannot load ReID extractor:", e)
        extractor = None

    try:
        yolo_model = YOLO(yolo_path)
        flags["detector_flag"] = 1
        push_log("YOLO Detector loaded OK")
        print("[OK] YOLO Detector loaded.")
    except Exception as e:
        flags["detector_flag"] = 0
        push_log(f"[ERROR] Cannot load YOLO model: {e}")
        print("[ERROR] Cannot load YOLO model:", e)
        yolo_model = None

    try:
        tracker_manager = TrackerManager(iou_threshold, max_age)
        flags["tracker_flag"] = 1
        push_log("Tracker manager loaded OK")
        print("[OK] Tracker manager loaded.")
    except Exception as e:
        flags["tracker_flag"] = 0
        push_log(f"[ERROR] Cannot load tracker: {e}")
        print("[ERROR] Cannot load tracker:", e)
        tracker_manager = None

    return extractor, classifier, yolo_model, tracker_manager, device, flags

def init_nonid_engine(yolo_path, iou_threshold=0.3, max_age=10):

    flags = {}

    try:
        yolo_model = YOLO(yolo_path)
        flags["detector_flag"] = 1
        push_log("YOLO Detector loaded OK")
        print("[OK] YOLO Detector loaded.")
    except Exception as e:
        flags["detector_flag"] = 0
        push_log(f"[ERROR] Cannot load YOLO model: {e}")
        print("[ERROR] Cannot load YOLO model:", e)
        yolo_model = None

    try:
        tracker_manager = TrackerManager(iou_threshold, max_age)
        flags["tracker_flag"] = 1
        push_log("Tracker manager loaded OK")
        print("[OK] Tracker manager loaded.")
    except Exception as e:
        flags["tracker_flag"] = 0
        push_log(f"[ERROR] Cannot load tracker: {e}")
        print("[ERROR] Cannot load tracker:", e)
        tracker_manager = None

    return yolo_model, tracker_manager, flags

def predict_batch(bboxs, extractor, classifier, device):
    # img_paths: list[str], ví dụ 5 ảnh trong 1 frame
    feats = extractor(bboxs)      # (N, 512)
    feats = feats.to(device).float()

    logits = classifier(feats)        # (N, 2)
    probs = torch.softmax(logits, dim=1)

    # lấy index lớn nhất mỗi row
    classes = torch.argmax(probs, dim=1).cpu().tolist()

    # lấy độ tin cậy mỗi row
    confidences = probs.max(dim=1).values.cpu().tolist()

    return classes, confidences