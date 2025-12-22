import torch
from torch.utils.data import DataLoader
import torch.serialization
from torchreid.reid.utils import FeatureExtractor
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
from utils import Classifier, ReIDDataset
import numpy as np
import os
import argparse

torch.serialization.add_safe_globals([np.dtype, np.core.multiarray.scalar])

def get_parser():
    parser = argparse.ArgumentParser()    

    parser.add_argument('--name', type=str, default='osnet_x1_0', help="ReID model name")
    parser.add_argument('--bs_test', type=int, default=32, help="batch size for evaluate")
    parser.add_argument('--save_path', type=str, default='path/to/save', help="path to save data")
    parser.add_argument('--pretrained_model', type=str, default='path/to/pretrained_model', help="path to ReID pretrained model")
    parser.add_argument('--classifier_path', type=str, default='path/to/pretrained_classifier', help="path to pretrained classifier")
    parser.add_argument('--nc', type=int, default=3, help="number of classes")
        
    args = parser.parse_args()
    
    return args

@torch.no_grad()
def evaluate_handler(extractor, classifier, loader, device):
    classifier.eval()

    all_labels = []
    all_preds = []

    for img_paths, labels in loader:

        # img_paths: tuple → convert to list
        img_paths = list(img_paths)

        # Extract features (N, 512)
        feats = extractor(img_paths)
        feats = feats.to(device).float()

        labels = labels.to(device).long()

        # forward
        logits = classifier(feats)              # (N, 2)
        preds = torch.argmax(logits, dim=1)    # softmax predicted class

        all_labels.extend(labels.cpu().numpy())
        all_preds.extend(preds.cpu().numpy())

    # --------------------------
    #      METRICS
    # --------------------------
    acc = accuracy_score(all_labels, all_preds)
    cm = confusion_matrix(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="binary", pos_label=1
    )

    return acc, cm, precision, recall, f1

def evaluate(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    test_pos_folder = os.path.join(args.save_path, "test", "familier")
    test_neg_folder = os.path.join(args.save_path, "test", "stranger")
    test_pos_list  = [os.path.join(test_pos_folder, f) for f in os.listdir(test_pos_folder)]
    test_neg_list  = [os.path.join(test_neg_folder, f) for f in os.listdir(test_neg_folder)]
    test_pos = ReIDDataset(test_pos_list)
    test_neg = ReIDDataset(test_neg_list)
    test_ds = test_pos + test_neg
    test_loader = DataLoader(test_ds, batch_size=args.bs_test, shuffle=False)

    classifier = Classifier(num_class=args.nc).to(device)
    classifier.load_state_dict(torch.load(args.classifier_path, map_location=device))

    extractor = FeatureExtractor(
            model_name= args.name,
            model_path=args.pretrained_model,
            device=device
        )

    acc, cm, precision, recall, f1 = evaluate_handler(
            extractor, classifier, test_loader, device
        )

    print("\n====== EVALUATION RESULT ======")
    print(f"Accuracy  : {acc:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1-score  : {f1:.4f}")
    print("\nConfusion Matrix:\n", cm)

if __name__ == '__main__':
    args = get_parser()
    evaluate(args)