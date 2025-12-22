import torch
import os
import csv

def train_one_epoch(classifier, extractor, loader, criterion, optimizer, device):
    classifier.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for img_paths, labels in loader:
        # Extract features (N, 512)
        img_paths = list(img_paths)
        feats = extractor(img_paths)
        feats = feats.to(device).float()
        labels = labels.to(device).long()

        preds = classifier(feats)
        loss = criterion(preds, labels)
        total_loss += loss.item() * labels.size(0)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        pred_label = torch.argmax(preds, dim=1)
        correct += (pred_label == labels).sum().item()
        total += labels.size(0)        

    avg_loss = total_loss / total
    train_acc = correct / total

    return avg_loss, train_acc

def eval(classifier, extractor, loader, device):
    classifier.eval()
    total, correct = 0, 0

    with torch.no_grad():
        for img_paths, labels in loader:
            img_paths = list(img_paths)
            feats = extractor(img_paths)
            feats = feats.to(device).float()
            labels = labels.to(device).long()

            preds = classifier(feats)
            pred_label = torch.argmax(preds, dim=1)
            correct += (pred_label == labels).sum().item()
            total += labels.size(0)

    acc = correct / total if total > 0 else 0
    return acc

def train(
    args,
    train_loader,
    val_loader,
    extractor,
    classifier,
    criterion,
    optimizer,
    # num_epochs=10,
    # model_path="log/osnet_x1_0/model/best_model.pth",
    device = "cpu",
    # log_freq = 2
):

    full_model_path = os.path.join(args.classifier_path, args.classifier_name)
    csv_log_path = os.path.join(args.classifier_path, "osnetibn_x1_0_log.csv")

    best_acc = 0

    with open(csv_log_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_acc", "val_acc"])

    # Training loop
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(classifier, extractor, train_loader,
                               criterion, optimizer, device)
        val_acc = eval(classifier, extractor, val_loader, device)

        with open(csv_log_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([epoch, train_acc, val_acc])

        if epoch % args.log_freq == 0:
            print(f"[Epoch {epoch}] Loss: {train_loss:.4f} |  Train Acc: {train_acc:.4f}  |  Val Acc: {val_acc:.4f}")

        if best_acc < val_acc :
            # Save best classifier
            torch.save(classifier.state_dict(), full_model_path)
            print("Saved best classifier to:", full_model_path)
            best_acc = val_acc

