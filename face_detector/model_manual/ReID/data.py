import argparse
from utils import create_data

def get_parser():
    parser = argparse.ArgumentParser()    

    parser.add_argument('--videos_paths', type=str, default='path/to/folder', help="video data folder path")
    parser.add_argument('--save_path', type=str, default='path/to/save', help="path to save data")
    parser.add_argument('--img_h', type=int, default=256, help="image height")
    parser.add_argument('--img_w', type=int, default=128, help="image width")
    parser.add_argument('--skip_frames', type=int, default=15, help="take every N-th frame from every video for data augmentation")
    parser.add_argument('--aug_count', type=int, default=5, help="number of augmentations to be applied on every image")
    parser.add_argument('--camid', type=int, default=0, help="choose camid")
    parser.add_argument('--yolo_path', type=str, default='path/to/yolo.pt', help="path to YOLO pretrained model")
        
    args = parser.parse_args()
    
    return args

def make_data(args):
    create_data(args)

if __name__ == '__main__':
    args = get_parser()
    make_data(args)