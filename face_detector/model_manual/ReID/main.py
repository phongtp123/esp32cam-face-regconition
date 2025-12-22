import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from utils import Classifier, ReIDDataset, init_extractor
from train import train
import numpy as np
import os

torch.serialization.add_safe_globals([np.dtype, np.core.multiarray.scalar])

def get_parser():
    parser = argparse.ArgumentParser()    

    parser.add_argument('--save_path', type=str, default='path/to/saved', help="path to saved data")
    parser.add_argument('--name', type=str, default='osnet_x1_0', help="ReID model name")
    parser.add_argument('--bs', type=int, default=128, help="batch size")
    parser.add_argument('--lr', type=float, default=0.003, help="learning rate")
    parser.add_argument('--epochs', type=int, default=5, help="epoch count for the training loop")
    parser.add_argument('--pretrained_model', type=str, default='path/to/pretrained_model', help="path to ReID pretrained model")
    parser.add_argument('--classifier_path', type=str, default='path/to/pretrained_classifier', help="path to save classifier")
    parser.add_argument('--classifier_name', type=str, default='best_model.pth', help="name of the classifier")
    parser.add_argument('--nc', type=int, default=3, help="number of classes")
    parser.add_argument('--log_freq', type=int, default=1, help="logging after num epochs")
        
    args = parser.parse_args()
    
    return args

def main(args):
    
    # Preparation
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    classifier = Classifier(num_class=args.nc).to(device)
    extractor = init_extractor(args, device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.Adam(classifier.parameters(), lr=args.lr)

    # Make Dataset
    train_neg_folder = os.path.join(args.save_path, "train", "stranger")
    train_pos_folder = os.path.join(args.save_path, "train", "familier")
    val_neg_folder = os.path.join(args.save_path, "valid", "stranger")
    val_pos_folder = os.path.join(args.save_path, "valid", "familier")

    train_pos_list = [os.path.join(train_pos_folder, f) for f in os.listdir(train_pos_folder)]
    train_neg_list = [os.path.join(train_neg_folder, f) for f in os.listdir(train_neg_folder)]
    val_pos_list   = [os.path.join(val_pos_folder, f) for f in os.listdir(val_pos_folder)]
    val_neg_list   = [os.path.join(val_neg_folder, f) for f in os.listdir(val_neg_folder)]

    train_pos = ReIDDataset(train_pos_list)
    train_neg = ReIDDataset(train_neg_list)
    train_ds = train_pos + train_neg

    val_pos = ReIDDataset(val_pos_list)
    val_neg = ReIDDataset(val_neg_list)
    val_ds = val_pos + val_neg

    # Make Dataloader
    train_loader = DataLoader(train_ds, batch_size=args.bs, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.bs, shuffle=False)

    # Train
    train(args, train_loader, val_loader, extractor, classifier, criterion, optimizer)
    
if __name__ == '__main__':
    args = get_parser()
    main(args)