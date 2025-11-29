import torch
import torch.serialization
from torchreid.reid.utils import FeatureExtractor
from utils import Classifier
import numpy as np

torch.serialization.add_safe_globals([np.dtype, np.core.multiarray.scalar])
device = "cuda" if torch.cuda.is_available() else "cpu"

classifier = Classifier(num_class=2).to(device)
classifier.load_state_dict(torch.load("log/osnet_x1_0/model/best_model.pth", map_location=device))
classifier.eval()

extractor = FeatureExtractor(
        model_name= "osnet_x1_0",
        model_path="log/osnet_x1_0/model/osnet_x1_0_imagenet.pth",
        device=device
    )

def predict_batch(img_paths):
    # img_paths: list[str], ví dụ 5 ảnh trong 1 frame
    feats = extractor(img_paths)      # (N, 512)
    feats = feats.to(device).float()

    logits = classifier(feats)        # (N, 2)
    probs = torch.softmax(logits, dim=1)

    # lấy index lớn nhất mỗi row
    classes = torch.argmax(probs, dim=1).cpu().tolist()

    # lấy độ tin cậy mỗi row
    confidences = probs.max(dim=1).values.cpu().tolist()

    return classes, confidences


image_list = ["test.jpg", "test2.jpg", "test3.jpg", "1501_c2s3_069052_01.jpg"]

cls_list, conf_list = predict_batch(image_list)

for i, (cls, conf) in enumerate(zip(cls_list, conf_list)):
    if cls == 1 :
        print(f"Image {i}: Class={cls}, Confidence={conf:.4f}")
    elif cls == 0 :
        print(f"Image {i}: Người lạ, Confidence={conf:.4f}")


# CÔNG VIỆC TIẾP THEO: TÍCH HỢP VÀO BACKEND, TẠO 2 NÚT TRÊN WEB SERVER ĐỂ SWITCH GIỮA 2 CHẾ ĐỘ LÀM VIỆC.