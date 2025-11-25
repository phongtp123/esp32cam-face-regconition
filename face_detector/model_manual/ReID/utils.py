import torchreid
import os
import glob
import re
import numpy as np
import imgaug as iaa
import cv2
from ultralytics import YOLO

yolo_model = YOLO("../../yolov8n.pt")

class NewDataset(torchreid.data.datasets.ImageDataset):
    dataset_dir = ''

    def __init__(self, path, root='', **kwargs):
        self.train_dir = self.dataset_dir     
        self.query_dir = self.dataset_dir
        self.gallery_dir = self.dataset_dir
        
        train = self.process_dir(self.train_dir, isQuery=False)
        query = self.process_dir(self.query_dir, isQuery=True)
        gallery = self.process_dir(self.gallery_dir, isQuery=False)

        super(NewDataset, self).__init__(train, query, gallery, **kwargs)
        
        
    def process_dir(self, dir_path, isQuery, relabel=False):
        img_paths = glob(os.join(dir_path, '*.jpg'))
        
        data = []
        for img_path in img_paths:

            img_name = img_path.split('/')[-1]
            name_splitted = img_name.split('_')
            pid = int( name_splitted[1][1:] )
            camid = int( name_splitted[0][1:] )

            if isQuery:
                camid += 10  # index starts from 0

            data.append((img_path, pid, camid))

        return data
    
    
    def process_dir_market(self, dir_path, relabel=False):
        img_paths = glob(os.join(dir_path, '*.jpg'))
        pattern = re.compile(r'([-\d]+)_c(\d)')

        pid_container = set()
        for img_path in img_paths:
            pid, _ = map(int, pattern.search(img_path).groups())
            if pid == -1:
                continue # junk images are just ignored
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(pid_container)}

        data = []
        for img_path in img_paths:
            pid, camid = map(int, pattern.search(img_path).groups())
            if pid == -1:
                continue # junk images are just ignored
            assert 0 <= pid <= 1501 # pid == 0 means background
            assert 1 <= camid <= 6
            camid -= 1 # index starts from 0
            if relabel:
                pid = pid2label[pid]
            data.append((img_path, pid, camid))

        return data
    

def augment_images(img, count):
    imgs = [img]

    for i in range(count):
        aug = iaa.Sequential([])

        rand_number = np.random.randint(0, 101)
        if rand_number < 33:
            aug.append(iaa.AdditiveGaussianNoise(loc=0, scale=(0.01*255, 0.08*255)))
        elif rand_number < 70:
            aug.append(iaa.AverageBlur(k=(3, 3)))

        rand_number = np.random.randint(0, 101)
        if rand_number < 30:
            aug.append(iaa.Multiply((0.7, 1.2)))
        elif rand_number < 70:
            aug.append(iaa.GammaContrast((1, 1.6)))            
            
        rand_number = np.random.randint(0, 101)
        if rand_number < 33:
            aug.append(iaa.ChangeColorTemperature((1100, 10000)))
        elif rand_number < 66:
            aug.append(iaa.MultiplyHueAndSaturation((0.5, 1.5), per_channel=True))           
                  
        rand_number = np.random.randint(0, 101)
        if rand_number < 33:
            aug.append(iaa.CoarseDropout(0.015, size_percent=0.1, per_channel=0.5))
        elif rand_number < 66:
            aug.append(iaa.SaltAndPepper(0.05, per_channel=True))
            
        rand_number = np.random.randint(0, 101)
        if rand_number < 50:
            aug.append(iaa.pillike.FilterEdgeEnhanceMore())

        aug.append(iaa.Fliplr(0.5))
        aug.append(iaa.AveragePooling((1, 3)))

        img_aug = aug(image=img)
        imgs.append(img_aug)

    return imgs

def create_data(args):
    counter = 0

    for pid, person_folder in enumerate(sorted(os.listdir(args.videos_paths))):
        person_path = os.path.join(args.videos_paths, person_folder)

        for video_path in sorted(glob(person_path + '/*')):
            print(f'Preprocessing {video_path} video...')
            cap = cv2.VideoCapture(video_path)
            frame_counter = 0
            while cap.isOpened():
                ret, frame = cap.read()
                frame_counter += 1

                if frame_counter % args.skip_frames == 0:
                    if ret:
                        results = yolo_model(frame, imgsz=320, verbose=False) 
                        result_pandas = results.pandas().xyxy[0]
                        people = result_pandas[result_pandas['name'] == 'person'][['xmin','ymin','xmax','ymax']]

                        if len(people) == 0:
                            continue

                        xyxy = people.to_numpy().astype(np.int32)[0]  # taking first person's bbox 
                        person = frame[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]]  # cropping the person from the frame
                        person = cv2.resize(person, (args.img_w, args.img_h))

                        images =  augment_images(person, count=args.aug_count)
                        for image in images:
                            counter += 1
                            name = f'c0_p{pid}_{counter}.jpg'
                            cv2.imwrite(f'{args.save_path}/{name}', image)
                    else:
                        break
            print('Done!')