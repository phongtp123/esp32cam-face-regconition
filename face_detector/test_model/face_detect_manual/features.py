from typing import Tuple, List
import os
import pickle
from enum import Enum
from Intergral import rect_sum
import numpy as np
import random

class FeatureType(Enum):
    TWO_H = 1       # two horizontal rectangles
    TWO_V = 2       # two vertical rectangles
    THREE_H = 3     # three horizontal rectangles
    THREE_V = 4     # three vertical rectangles
    FOUR = 5        # four rectangles (2x2 pattern)

# Feature represented as tuple: (type, x, y, w, h)
def generate_features(img_w=24, img_h=24, step=2, max_feature=6000, cache_path="./cache/features_cache.pkl") -> List[Tuple]:

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    if os.path.exists(cache_path):
        print(f"[INFO] Loading cached features from '{cache_path}'...")
        with open(cache_path, "rb") as f:
            features = pickle.load(f)
        return features

    print("[INFO] Generating Haar features...")
    features = []
    for w in range(1, img_w+1, step):
        for h in range(1, img_h+1, step):
            for x in range(0, img_w - w + 1, step):
                for y in range(0, img_h - h + 1, step):
                    if x + 2*w <= img_w:
                        features.append((FeatureType.TWO_H, x, y, w, h))
                    if y + 2*h <= img_h:
                        features.append((FeatureType.TWO_V, x, y, w, h))
                    if x + 3*w <= img_w:
                        features.append((FeatureType.THREE_H, x, y, w, h))
                    if y + 3*h <= img_h:
                        features.append((FeatureType.THREE_V, x, y, w, h))
                    if x + 2*w <= img_w and y + 2*h <= img_h:
                        features.append((FeatureType.FOUR, x, y, w, h))

    features = random.sample(features, max_feature)
    
    print(f"[INFO] Generated {len(features)} features. Saving to '{cache_path}'...")
    with open(cache_path, "wb") as f:
        pickle.dump(features, f)
        
    return features

def calculateRegions(integralImage, featureType, combinedX, combinedY, scaledWidth, scaledHeight):
    totalSum = rect_sum(integralImage, combinedX, combinedY, scaledWidth, scaledHeight)

    blackSum = 0
    match featureType:
        case FeatureType.TWO_H:
            blackSum = rect_sum(integralImage, combinedX + np.floor(scaledWidth / 2), combinedY, np.floor(scaledWidth / 2), scaledHeight)
        case FeatureType.TWO_V:
            blackSum = rect_sum(integralImage, combinedX, combinedY + np.floor(scaledHeight / 2), scaledWidth, np.floor(scaledHeight / 2))
        case FeatureType.THREE_H:
            blackSum = rect_sum(integralImage, combinedX + np.floor(scaledWidth / 3), combinedY, np.floor(scaledWidth / 3), scaledHeight)
        case FeatureType.THREE_V:
            blackSum = rect_sum(integralImage, combinedX, combinedY + np.floor(scaledHeight / 3), scaledWidth, np.floor(scaledHeight / 3))
        case FeatureType.FOUR:
            blackSum = rect_sum(integralImage, combinedX + np.floor(scaledWidth / 2), combinedY, np.floor(scaledWidth / 2), np.floor(scaledHeight / 2)) + rect_sum(integralImage, combinedX, combinedY + np.floor(scaledHeight / 2), np.floor(scaledWidth / 2), np.floor(scaledHeight / 2))
        case _:
            blackSum = 0

    whiteSum = totalSum - blackSum

    return whiteSum, blackSum

# Caculate value of the Haar feature include standard deviation normalization
def eval_feature(ii, sii, feature, offset=(0,0), scaleFactor=1):
   
    t, fx, fy, fw, fh = feature
    offx, offy = offset

    # convert feature local coords to global coords in the image
    x = fx + offx
    y = fy + offy
    w = fw * scaleFactor
    h = fh * scaleFactor

    ii_sum = rect_sum(ii, x, y, w, h)
    squaredSum = rect_sum(sii, x, y, w, h)
    area = w * h
    mean = ii_sum / area
    variance = (squaredSum / area) - (mean * mean)
    stdDev = np.sqrt(np.maximum(variance, 1e-6))
    
    white, black = calculateRegions(ii, t, x, y, w, h);
    rawFeatureValue = black - white;

    return rawFeatureValue / stdDev if (variance > 0) else rawFeatureValue