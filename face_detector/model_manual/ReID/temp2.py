# import os
# import torchreid
# import torch
# import glob
# import re
# import random
# import string


# class NewDataset(torchreid.data.ImageDataset):
#     dataset_dir = ''
#     gallery_dir = ''
#     query_dir = ''

#     def __init__(self, **kwargs):
#         self.train_dir = self.dataset_dir     
#         train = self.process_dir(self.train_dir, isQuery=False)
#         query = self.process_dir(self.query_dir, isQuery=True)
#         gallery = self.process_dir(self.gallery_dir, isQuery=False)

#         super(NewDataset, self).__init__(train, query, gallery, **kwargs)
        
        
#     def process_dir(self, dir_path, isQuery):
#         img_paths = glob.glob(os.path.join(dir_path, '*.jpg'))
        
#         data = []
#         for img_path in img_paths:

#             img_name = os.path.basename(img_path)
#             name_splitted = img_name.split('_')
#             pid = int( name_splitted[1][1:] )
#             camid = int( name_splitted[0][1:] )

#             if isQuery:
#                 camid += 10  # index starts from 0

#             data.append((img_path, pid, camid))

#         return data
    
    
#     def process_dir_market(self, dir_path, relabel=False):
#         img_paths = glob.glob(os.path.join(dir_path, '*.jpg'))
#         pattern = re.compile(r'([-\d]+)_c(\d)')

#         pid_container = set()
#         for img_path in img_paths:
#             pid, _ = map(int, pattern.search(img_path).groups())
#             if pid == -1:
#                 continue # junk images are just ignored
#             pid_container.add(pid)
#         pid2label = {pid: label for label, pid in enumerate(pid_container)}

#         data = []
#         for img_path in img_paths:
#             pid, camid = map(int, pattern.search(img_path).groups())
#             if pid == -1:
#                 continue # junk images are just ignored
#             assert 0 <= pid <= 1501 # pid == 0 means background
#             assert 1 <= camid <= 6
#             camid -= 1 # index starts from 0
#             if relabel:
#                 pid = pid2label[pid]
#             data.append((img_path, pid, camid))

#         return data
    
# def main():
    
#     device = 'cuda' if torch.cuda.is_available() else 'cpu'
#     NewDataset.dataset_dir = "../../data/saved_data/train/all_data"
#     NewDataset.gallery_dir = "../../data/saved_data/test/all_data"
#     NewDataset.query_dir = "../../data/saved_data/valid/all_data"
#     dataset_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(1, 25)))
#     torchreid.data.register_image_dataset(dataset_name, NewDataset)

#     datamanager = torchreid.data.ImageDataManager(
#         sources=dataset_name, 
#         height=256, 
#         width=128, 
#         batch_size_train=32, 
#         batch_size_test=100,
#         transforms=["random_flip"]
#     )

#     model = torchreid.models.build_model(
#         name="osnet_ain_x1_0",
#         num_classes=datamanager.num_train_pids,
#         loss="softmax",
#         pretrained=True
#     ).to(device).train()


#     optimizer = torchreid.optim.build_optimizer(
#         model,
#         optim='adam',
#         lr=0.003
#     )

#     scheduler = torchreid.optim.build_lr_scheduler(
#         optimizer,
#         lr_scheduler="single_step",
#         stepsize=2
#     )

#     engine = torchreid.engine.ImageSoftmaxEngine(
#         datamanager,
#         model,
#         optimizer=optimizer,
#         scheduler=scheduler,
#         label_smooth=True
#     )

#     engine.run(
#         save_dir="log/resnet50",
#         max_epoch=5, 
#         eval_freq=1, 
#         print_freq=1,
#         test_only=False
#     )


import torch
from torchreid.reid.models import build_model
from torchvision import transforms
import re
import os
from tqdm import tqdm
from PIL import Image
import torch.nn.functional as F

# def build_transform():
#     return transforms.Compose([
#         transforms.ToTensor(),
#     ])

# def parse_label(fname):
#     """
#     c1_p1_xxx.jpg → 1
#     """
#     m = re.search(r'_p(\d+)_', fname)
#     if m is None:
#         raise ValueError(f"Cannot parse label from {fname}")
#     return int(m.group(1))

# def build_gallery(
#     model,
#     gallery_dir,
#     device,
#     save_dir="./"
# ):
#     transform = build_transform()

#     features = []
#     labels = []
#     paths = []

#     img_files = [
#         f for f in os.listdir(gallery_dir)
#     ]

#     model.to(device)

#     with torch.no_grad():
#         for fname in tqdm(img_files, desc="Extracting gallery"):
#             img_path = os.path.join(gallery_dir, fname)

#             img = Image.open(img_path).convert("RGB")
#             img = transform(img).unsqueeze(0).to(device)

#             feat = model(img)              # (1, 512)
#             feat = F.normalize(feat, dim=1)

#             features.append(feat.cpu())
#             labels.append(parse_label(fname))
#             paths.append(fname)

#     features = torch.cat(features, dim=0)   # (M, 512)

#     # ---- Save ----
#     torch.save(features, os.path.join(save_dir, "gallery_feats.pth"))

#     gallery = {
#         "features": features,
#         "labels": labels,
#         "paths": paths
#     }

#     torch.save(gallery, os.path.join(save_dir, "gallery_meta.pth"))

#     print(f"[OK] Gallery saved: {features.shape}")

#     return gallery

def main():
    gallery = torch.load("gallery_meta.pth", map_location="cpu")

    print(gallery["features"].shape)  # (M, 512)
    print(gallery["labels"][:5])
    print(gallery["paths"][:5])

if __name__ == '__main__':
    main()