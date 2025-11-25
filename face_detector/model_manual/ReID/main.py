import argparse
import torchreid
import torch
import random
import string
from utils import NewDataset, create_data


def get_parser():
    parser = argparse.ArgumentParser()    

    parser.add_argument('--name', type=str, default='osnet_x1_0', help="ReID model name")
    parser.add_argument('--img_h', type=int, default=256, help="image height")
    parser.add_argument('--img_w', type=int, default=128, help="image width")
    parser.add_argument('--bs', type=int, default=32, help="batch size")
    parser.add_argument('--optim', type=str, default='adam', help="optimzer")
    parser.add_argument('--lr', type=float, default=0.003, help="learning rate")
    parser.add_argument('--lr_sch', type=str, default="single_step", help="learning rate scheduler")
    parser.add_argument('--step', type=int, default=5, help="learning rate scheduler's step size")
    parser.add_argument('--epochs', type=int, default=20, help="epoch count for the training loop")
    parser.add_argument('--eval_freq', type=int, default=5, help="evaluation frequency")
    parser.add_argument('--videos_paths', type=str, default='path/to/folder', help="video data folder path")
    parser.add_argument('--skip_frames', type=int, default=15, help="take every N-th frame from every video for data augmentation")
    parser.add_argument('--aug_count', type=int, default=5, help="number of augmentations to be applied on every image")
    parser.add_argument('--save_path', type=str, default='path/to/save', help="path to save data")
        
    args = parser.parse_args()
    
    return args

def main(args):
    create_data(args)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    NewDataset.dataset_dir = args.save_path
    dataset_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(1, 25)))
    torchreid.data.register_image_dataset(dataset_name, NewDataset)

    datamanager = torchreid.data.ImageDataManager(
        sources=dataset_name, 
        height=args.img_h, 
        width=args.img_w, 
        batch_size_train=args.bs, 
        batch_size_test=100,
        transforms=["random_flip", "random_crop"]
    )

    model = torchreid.models.build_model(
        name=args.name,
        num_classes=datamanager.num_train_pids,
        loss="triplet",
        pretrained=True
    ).to(device).train()


    optimizer = torchreid.optim.build_optimizer(
        model,
        optim=args.optim,
        lr=args.lr, 
    )

    scheduler = torchreid.optim.build_lr_scheduler(
        optimizer,
        lr_scheduler=args.lr_sch, 
        stepsize=args.step,
    )

    engine = torchreid.engine.ImageTripletEngine(
        datamanager,
        model,
        optimizer=optimizer,
        scheduler=scheduler,
        margin=0.3,  # by default 0.3
        weight_t=1,  # weight for triplet loss
        weight_x=50, # weight for softmax loss
    )

    engine.run(
        save_dir=f"log/{args.name}",
        max_epoch=args.epochs, 
        eval_freq=args.eval_freq, 
        print_freq=50,
        test_only=False
    )

    
if __name__ == '__main__':
    args = get_parser()
    main(args)