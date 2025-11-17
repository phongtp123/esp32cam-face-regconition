import cv2 as cv
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

from features import generate_features
from Intergral import process_image_data
from cascade_detector import findFaces
from utils import load_face_images, load_nonface_images, generate_non_face_patches
from adaboost import train_adaboost

CONF_THRESHOLD_1 = -0.1  # bạn có thể tăng lên 2.0 hoặc 5.0 để chỉ giữ phát hiện mạnh
CONF_THRESHOLD_2 = 0.0

# generate_non_face_patches(input_folder="../data/test/non_face",
#                          output_folder="../data/non_face") #input_folder, output_folder, patch_size=24, patches_per_image=50

# import shutil
# import random

# source_dir = "../data/non_face"
# extra_dir = "../data/storage"

# # Tạo thư mục đích nếu chưa tồn tại
# os.makedirs(extra_dir, exist_ok=True)

# # Lấy danh sách tất cả file
# files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

# random.shuffle(files)

# keep = set(files[:10000])

# # Duyệt qua file và di chuyển phần dư
# for f in files[10000:]:
#     src_path = os.path.join(source_dir, f)
#     dst_path = os.path.join(extra_dir, f)
#     shutil.move(src_path, dst_path)

# print("✅ Đã giữ lại 10,000 file, di chuyển phần còn lại sang:", extra_dir)

# Load dataset
pos_imgs = load_face_images("../data/face")  # thư mục ảnh có khuôn mặt
neg_imgs = load_nonface_images("../data/non_face")  # thư mục ảnh không có khuôn mặt

features = generate_features(step=2, max_feature=6000) # Generate all features 

# with open("./cache/adaboost_stumps.pkl", "rb") as f:
#     classifiers = pickle.load(f)

trained_stumps = train_adaboost(pos_imgs, neg_imgs, features) # pos_imgs, neg_imgs, features

width = 240
height = 135
test_img = cv.imread("../data/test/face/7.png", cv.IMREAD_GRAYSCALE)
test_img = cv.resize(test_img, (width, height))
ii, sii = process_image_data(test_img)

results = findFaces(ii, sii, features, trained_stumps, width, height, 1.5, 5, 0.25) #integralImage, squaredIntegralImage, features, stumps, width, height, stepSize, maxScale, scaleStep
print(results)

img_vis = cv.cvtColor(test_img, cv.COLOR_GRAY2BGR)

# Ngưỡng confidence (để lọc các phát hiện yếu)

for det in results:
    x = int(det['x'])
    y = int(det['y'])
    s = int(24 * det['scaleFactor'])  # Kích thước cửa sổ 24x24 tỉ lệ theo scaleFactor
    conf = det['confidency']

    # Chỉ vẽ các phát hiện có confidence cao hơn ngưỡng
    if conf > CONF_THRESHOLD_1 and conf < CONF_THRESHOLD_2:
        color = (0, 255, 0) if conf > 0 else (0, 0, 255)
        cv.rectangle(img_vis, (x, y), (x + s, y + s), color, 2)
        cv.putText(img_vis, f"{conf:.1f}", (x, y - 5), cv.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

# Hiển thị kết quả
plt.figure(figsize=(8, 5))
plt.imshow(cv.cvtColor(img_vis, cv.COLOR_BGR2RGB))
plt.title("Detected Faces")
plt.axis("off")
plt.show()