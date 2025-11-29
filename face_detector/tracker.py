import cv2
import numpy as np
import time

def xyxy_to_cxcywh(box):
    # box = [x1,y1,x2,y2]
    x1,y1,x2,y2 = box
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    cx = x1 + w / 2.0
    cy = y1 + h / 2.0
    return np.array([cx, cy, w, h], dtype=np.float32)

def cxcywh_to_xyxy(cx, cy, w, h):
    x1 = cx - w / 2.0
    y1 = cy - h / 2.0
    x2 = cx + w / 2.0
    y2 = cy + h / 2.0
    return [int(x1), int(y1), int(x2), int(y2)]

def iou_xyxy(boxA, boxB):
    # boxes in x1,y1,x2,y2
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    areaA = max(1, (boxA[2]-boxA[0])) * max(1, (boxA[3]-boxA[1]))
    areaB = max(1, (boxB[2]-boxB[0])) * max(1, (boxB[3]-boxB[1]))
    union = areaA + areaB - interArea
    return interArea / union if union > 0 else 0.0

class KalmanBoxTracker:
    """
    Single object Kalman tracker for bbox (cx,cy,w,h) with velocities.
    State: [cx, cy, vx, vy, w, h, vw, vh] (8)
    Measurement: [cx, cy, w, h] (4)
    """
    count = 0

    def __init__(self, bbox_xyxy):
        # initialize KalmanFilter
        self.kf = cv2.KalmanFilter(8, 4)  # stateDim, measDim
        # transition matrix (F)
        dt = 1.0
        F = np.eye(8, dtype=np.float32)
        F[0,2] = dt
        F[1,3] = dt
        F[4,6] = dt
        F[5,7] = dt
        self.kf.transitionMatrix = F

        # measurement matrix H maps state to measurement
        H = np.zeros((4,8), dtype=np.float32)
        H[0,0] = 1.0  # cx
        H[1,1] = 1.0  # cy
        H[2,4] = 1.0  # w
        H[3,5] = 1.0  # h
        self.kf.measurementMatrix = H

        # process noise covariance Q
        Q = 1e-2
        self.kf.processNoiseCov = np.eye(8, dtype=np.float32) * Q

        # measurement noise covariance R
        R = 1e-1
        self.kf.measurementNoiseCov = np.eye(4, dtype=np.float32) * R

        # error covariance P
        self.kf.errorCovPost = np.eye(8, dtype=np.float32)

        # initialize state from bbox
        cx, cy, w, h = xyxy_to_cxcywh(bbox_xyxy)
        self.kf.statePost = np.array([cx, cy, 0, 0, w, h, 0, 0], dtype=np.float32).reshape(8,1)

        # bookkeeping
        KalmanBoxTracker.count += 1
        self.id = KalmanBoxTracker.count
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.last_update_time = time.time()

    def predict(self):
        """Predict state forward and return predicted bbox in xyxy"""
        pred = self.kf.predict()  # shape (8,1)
        cx = float(pred[0])
        cy = float(pred[1])
        w = float(pred[4])
        h = float(pred[5])
        self.age += 1
        self.time_since_update += 1
        return cxcywh_to_xyxy(cx, cy, w, h)

    def update(self, bbox_xyxy):
        """Correct with measurement bbox"""
        cx, cy, w, h = xyxy_to_cxcywh(bbox_xyxy)
        meas = np.array([cx, cy, w, h], dtype=np.float32).reshape(4,1)
        self.kf.correct(meas)
        self.hits += 1
        self.time_since_update = 0
        self.last_update_time = time.time()

    def get_state(self):
        s = self.kf.statePost.flatten()
        cx, cy, w, h = s[0], s[1], s[4], s[5]
        return cxcywh_to_xyxy(cx, cy, w, h)


class TrackerManager:
    def __init__(self, iou_threshold=0.3, max_age=30):
        self.trackers = []  # list of KalmanBoxTracker
        self.iou_threshold = iou_threshold
        self.max_age = max_age

    def update(self, detections):
        """
        detections: list of [x1,y1,x2,y2] in image coords
        """
        # 1. Predict all trackers
        predicted_boxes = [t.predict() for t in self.trackers]

        # 2. Build IoU matrix between predicted_boxes and detections
        if len(predicted_boxes) == 0:
            matches = []
            unmatched_dets = list(range(len(detections)))
            unmatched_trks = []
        else:
            iou_matrix = np.zeros((len(predicted_boxes), len(detections)), dtype=np.float32)
            for t_idx, tb in enumerate(predicted_boxes):
                for d_idx, db in enumerate(detections):
                    iou_matrix[t_idx, d_idx] = iou_xyxy(tb, db)

            # greedy matching: find best pairs above threshold
            matches = []
            unmatched_trks = list(range(len(predicted_boxes)))
            unmatched_dets = list(range(len(detections)))

            # while there is a pair with IoU >= threshold
            while True:
                if iou_matrix.size == 0:
                    break
                t_idx, d_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
                max_iou = iou_matrix[t_idx, d_idx]
                if max_iou < self.iou_threshold:
                    break
                matches.append((t_idx, d_idx))
                # remove matched row/col by setting to -1
                iou_matrix[t_idx, :] = -1
                iou_matrix[:, d_idx] = -1
                if t_idx in unmatched_trks: unmatched_trks.remove(t_idx)
                if d_idx in unmatched_dets: unmatched_dets.remove(d_idx)

        # 3. Update matched trackers with assigned detections
        for t_idx, d_idx in matches:
            self.trackers[t_idx].update(detections[d_idx])

        # 4. Create new trackers for unmatched detections
        for d_idx in unmatched_dets:
            trk = KalmanBoxTracker(detections[d_idx])
            self.trackers.append(trk)

        # 5. Remove dead trackers (time_since_update > max_age)
        keep = []
        for trk in self.trackers:
            if trk.time_since_update <= self.max_age:
                keep.append(trk)
        self.trackers = keep

        # return active tracks as list of dicts
        tracks = []
        for trk in self.trackers:
            if trk.time_since_update == 0:
                # recently updated, good track
                box = trk.get_state()
            else:
                # predicted only
                box = trk.predict()
            tracks.append({
                "id": trk.id,
                "box": box,
                "hits": trk.hits,
                "age": trk.age,
                "time_since_update": trk.time_since_update
            })
        return tracks