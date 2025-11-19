import numpy as np
import cv2
import os
from tqdm import tqdm
import random

def nms(detections, window_size=12):
    filtered = []

    for face in detections:
        is_merged = False

        for i, existing_face in enumerate(filtered):
            if (abs(face["x"] - existing_face["x"]) < window_size and
                abs(face["y"] - existing_face["y"]) < window_size):

                if face["confidency"] > existing_face["confidency"]:
                    filtered[i] = face.copy()
                is_merged = True
                break

        if not is_merged:
            filtered.append(face.copy())

    return filtered

def load_face_images(folder, size=(24, 24)):
    images = []
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.pgm', '.tif')

    for filename in tqdm(os.listdir(folder), desc=f"Loading {folder}"):
        if filename.lower().endswith(supported_exts):
            path = os.path.join(folder, filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, size)
            images.append(img)
    return images

def load_nonface_images(folder):
    images = []
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.pgm', '.tif')

    for filename in tqdm(os.listdir(folder), desc=f"Loading {folder}"):
        if filename.lower().endswith(supported_exts):
            path = os.path.join(folder, filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            images.append(img)
    return images

def generate_non_face_patches(input_folder, output_folder, patch_size=24, patches_per_image=50):
    
    os.makedirs(output_folder, exist_ok=True)
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tif')

    counter = 0
    for filename in tqdm(os.listdir(input_folder), desc="Generating non-face patches"):
        if not filename.lower().endswith(supported_exts):
            continue

        path = os.path.join(input_folder, filename)
        img = cv2.imread(path)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if h < patch_size or w < patch_size:
            continue  # ảnh nhỏ quá, bỏ qua

        # Tạo danh sách vị trí đã cắt để tránh trùng
        used_positions = set()

        num_patches = 0
        attempts = 0
        max_attempts = patches_per_image * 10  # tránh lặp vô hạn

        while num_patches < patches_per_image and attempts < max_attempts:
            attempts += 1
            x = random.randint(0, w - patch_size)
            y = random.randint(0, h - patch_size)
            # kiểm tra trùng vị trí (theo bước pixel)
            if (x, y) in used_positions:
                continue
            used_positions.add((x, y))

            patch = gray[y:y + patch_size, x:x + patch_size]
            save_path = os.path.join(output_folder, f"neg_{counter:05d}.png")
            cv2.imwrite(save_path, patch)
            counter += 1
            num_patches += 1

# def get_subwindow_integral(x, y, w, h, gray_image, global_ii=None, global_sii=None):
#     """
#     Returns: (ii, sii, offset_x, offset_y)
#     """
#     if global_ii is None:
#         global_ii = integral_image(gray_image)
#     if global_sii is None:
#         global_sii = integral_of_squares(gray_image)

#     return global_ii, global_sii, x, y