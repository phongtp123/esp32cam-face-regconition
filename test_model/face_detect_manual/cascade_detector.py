import numpy as np
import cv2
import matplotlib.pyplot as plt

from features import eval_feature
from utils import nms

def detectFace(integralImage, squaredIntegralImage, features, stumps, posX, posY, scaleFactor):
    steps = [1, 10, 100, 500, 2000, 4000, 6000] # Cascading stages

    sumAlphaH = 0
    stageIndex = 0

    for i in range (6000):
        stump = stumps[i]
        feature = features[stump.feature]
        response = eval_feature(integralImage, squaredIntegralImage, feature, (posX, posY), scaleFactor)
        
        scaledThreshold = stump.threshold * scaleFactor * scaleFactor
        h = 1 if(stump.polarity * response <= stump.polarity * scaledThreshold) else -1
        sumAlphaH += stump.amountOfSay * h

        if (i + 1 == steps[stageIndex]): 
            if (sumAlphaH <= 0): 
                break
            stageIndex+=1

    return posX, posY, scaleFactor, sumAlphaH

def findFaces(integralImage, squaredIntegralImage, features, stumps, width=240, height=135, stepSize = 2, maxScale = 3, scaleStep = 1):
    rawDetections = []
    scaleFactor = 1
    WINDOW_SIZE = 24
    while (scaleFactor <= maxScale):
        for startY in range(0, int(np.floor(height - (WINDOW_SIZE * scaleFactor))), int(np.floor(stepSize * scaleFactor))):
            for startX in range( 0, int(np.floor(width - (WINDOW_SIZE * scaleFactor))), int(np.floor(stepSize * scaleFactor))):
                posX, posY, scaleFactor, sumAlphaH = detectFace(integralImage, squaredIntegralImage, features, stumps, startX, startY, scaleFactor)
                rawDetections.append({
                    "x": posX,
                    "y": posY,
                    "scaleFactor": scaleFactor,
                    "confidency": sumAlphaH
                })
        scaleFactor += scaleStep

    print(f"[INFO] Raw detections: {len(rawDetections)}")
    return nms(rawDetections, WINDOW_SIZE * 0.75)


# def detect_image(gray_img, stumps, features, stages=[1,50,100,500,2000,4000,6000],
#                  scale_step=1, step_size=2, max_scale=4):
#     detections = []
#     h, w = gray_img.shape
#     scale = 1
#     base_w, base_h = 24, 24

#     ii = integral_image(gray_img)
#     sii = integral_of_squares(gray_img)

#     print(f"[INFO] Detecting faces with {len(stumps)} stumps, {len(stages)} stages")

#     while scale <= max_scale and base_w * scale <= w and base_h * scale <= h:
#         ws = int(round(base_w * scale))
#         hs = int(round(base_h * scale))
#         step = max(1, int(round(step_size * scale)))
#         print(f"[SCALE] Scale={scale:.2f}, Window={ws}x{hs}")

#         for y in range(0, h - hs + 1, step):
#             for x in range(0, w - ws + 1, step):
#                 sumAlphaH = 0.0
#                 stage_idx = 0
#                 passed = True

#                 for i, stump in enumerate(stumps):
#                     f = features[stump.feature]
#                     t, fx, fy, fw, fh = f
#                     # scale feature coordinates relative to base window if necessary
#                     scaled_f = (t,
#                                 int(round(fx * scale)),
#                                 int(round(fy * scale)),
#                                 int(round(fw * scale)),
#                                 int(round(fh * scale)))

#                     if (
#                         x < 0 or y < 0 or
#                         (x + int(round(fx * scale)) + int(round(fw * scale))) > w or
#                         (y + int(round(fy * scale)) + int(round(fh * scale))) > h
#                     ):
#                         passed = False
#                         break

#                     # compute feature value with offset (x,y)
#                     val = eval_feature(ii, sii, scaled_f, offset=(x, y))

#                     scaled_thresh = stump.threshold * (scale * scale)
#                     # use <= like JS version
#                     h_pred = 1 if stump.polarity * val <= stump.polarity * scaled_thresh else -1
#                     sumAlphaH += stump.amountOfSay * h_pred

#                     # stage cutoff
#                     if (i + 1) == stages[stage_idx]:
#                         if sumAlphaH <= 0:
#                             passed = False
#                             break
#                         stage_idx += 1
#                         if stage_idx >= len(stages):
#                             break

#                 if passed:
#                     detections.append((x, y, ws, hs, sumAlphaH))

#         scale += scale_step

    
#     final = nms(detections)
#     return final