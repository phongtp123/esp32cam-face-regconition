import os
import glob
import re
import numpy as np
from imgaug import augmenters as iaa
import cv2
from ultralytics import YOLO
import random
from torchreid.reid.utils import FeatureExtractor
import torch.nn as nn
from torch.utils.data import Dataset

class Classifier(nn.Module):
    def __init__(self, num_class):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(512, num_class)
        )

    def forward(self, x):
        logits = self.fc(x)
        return logits

class ReIDDataset(Dataset):
    def __init__(self, img_paths):
        self.img_paths = img_paths
        self.labels = []
        for path in img_paths:
            fname = os.path.basename(path)
            m = re.search(r"p(\d+)", fname)
            pid = int(m.group(1))
            self.labels.append(pid)

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        return self.img_paths[idx], self.labels[idx]
    
def augment_images(img, count):
    imgs = [img]

    for i in range(count):
        aug = iaa.Sequential([])
          
        rand_number = np.random.randint(0, 101)
        if rand_number < 50:
            aug.append(iaa.pillike.FilterEdgeEnhanceMore())

        aug.append(iaa.Fliplr(0.5))
        aug.append(iaa.AveragePooling((1, 3)))

        img_aug = aug(image=img)
        imgs.append(img_aug)

    return imgs

def create_data(args):
    yolo_model = YOLO(args.yolo_path)
    # Tạo folder ReID chuẩn
    train_dir = os.path.join(args.save_path, "train_temp")
    validation_dir = os.path.join(args.save_path, "valid_temp")
    test_dir = os.path.join(args.save_path, "test_temp")

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(validation_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    print("\nCreating ReID Classification dataset...")
    counter = 0

    # Duyệt qua từng người (PID theo folder)
    for pid, person_folder in enumerate(sorted(os.listdir(args.videos_paths))):
        person_path = os.path.join(args.videos_paths, person_folder)

        person_images = []  # tất cả ảnh của 1 người

        # Duyệt qua từng video của người đó
        for video_path in sorted(glob.glob(person_path + '/*')):
            print(f'Preprocessing {video_path}')
            cap = cv2.VideoCapture(video_path)
            frame_counter = 0

            while cap.isOpened():
                ret, frame = cap.read()
                frame_counter += 1

                if not ret:
                    break

                if frame_counter % args.skip_frames != 0:
                    continue

                results = yolo_model(frame, imgsz=320, conf=0.4, verbose=False)
                detections = results[0].boxes

                if len(detections) == 0:
                    continue

                for box in detections:
                    cls = int(box.cls[0])
                    if cls != 0:
                        continue  # chỉ lấy người

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    person = frame[y1:y2, x1:x2]

                    if person.size == 0:
                        continue

                    # Resize model input
                    person = cv2.resize(person, (args.img_w, args.img_h))

                    # Augmentation
                    aug_images = augment_images(person, count=args.aug_count)

                    for img in aug_images:
                        person_images.append(img)

        #  Phân chia Train / Valid / Test
        if len(person_images) < 3:
            print(f"[WARN] PID {pid+1} không đủ ảnh.")
            continue

        random.shuffle(person_images)

        n = len(person_images)
        n_valid = max(1, int(0.15 * n))
        n_test = max(1, int(0.15 * n))
        n_train = n - n_valid - n_test

        train_imgs = person_images[:n_train]
        valid_imgs = person_images[n_train:n_train + n_valid]
        test_imgs = person_images[n_train + n_valid:]

        # =============================
        #  SAVE ẢNH
        # =============================

        def save_images(img_list, dest_dir, camid):
            nonlocal counter
            for img in img_list:
                counter += 1
                filename = f"c{camid}_p{pid+1}_{counter}.jpg"
                cv2.imwrite(os.path.join(dest_dir, filename), img)

        save_images(train_imgs, train_dir, camid=args.camid)
        save_images(valid_imgs, validation_dir, camid=args.camid)
        save_images(test_imgs, test_dir, camid=args.camid + 1)

        print(f"PID {pid+1} → Train:{len(train_imgs)}, Query:{len(valid_imgs)}, Gallery:{len(test_imgs)}")

    print("\nDataset creation completed!")

def init_extractor(args, device):
    extractor = FeatureExtractor(
        model_name= args.name,
        model_path=args.pretrained_model,
        device=device
    )
    return extractor