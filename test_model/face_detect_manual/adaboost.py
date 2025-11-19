import numpy as np
from weak_classifier import DecisionStump
from tqdm import tqdm
import os
import pickle

from features import eval_feature
from Intergral import process_image_data

def adaboost_model(feature_values, labels):
    n_features, n_samples = feature_values.shape
    y = np.copy(labels)
    y[y == 0] = -1  # convert 0→-1 for AdaBoost math

    # init weights
    pos = np.sum(y == 1)
    neg = np.sum(y == -1)
    w = np.zeros(n_samples)
    w[y == 1] = 1.0 / (2 * pos)
    w[y == -1] = 1.0 / (2 * neg)
    w /= w.sum()

    classifiers = []

    for f in tqdm(range(n_features), desc=f"Training stumps", leave=False):
        vals = feature_values[f]
        order = np.argsort(vals)
        sorted_vals, sorted_y, sorted_w = vals[order], y[order], w[order]

        S_pos = (sorted_w * (sorted_y == 1)).cumsum()
        S_neg = (sorted_w * (sorted_y == -1)).cumsum()
        T_pos, T_neg = S_pos[-1], S_neg[-1]

        errors1 = S_pos + (T_neg - S_neg) # Error for decide that non-face on the left and face on the right
        errors2 = S_neg + (T_pos - S_pos) # Error for decide that face on the left and non-face on the right
        errs = np.minimum(errors1, errors2)
        min_idx = np.argmin(errs)
        err = errs[min_idx]

        thr = sorted_vals[min_idx]
        pol = -1 if errors1[min_idx] < errors2[min_idx] else 1                
        aos = 0.5 * np.log((1 - err + 1e-10) / (err + 1e-10))

        stump = DecisionStump(f, thr, pol, aos)
        preds = stump.predict(feature_values[f])
        w *= np.exp(-aos * y * preds)
        w /= w.sum()

        classifiers.append(stump)

    return classifiers

def train_adaboost(pos_imgs, neg_imgs, features, cache_path="./cache/adaboost_stumps.pkl"):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    if os.path.exists(cache_path):
        print(f"[INFO] Loading trained AdaBoost from '{cache_path}' ...")
        with open(cache_path, "rb") as f:
            classifiers = pickle.load(f)
        print(f"[INFO] Loaded AdaBoost with {len(classifiers)} stumps.")
        return classifiers

    print("Preparing Integral Matrix .....")
    pos_iis, pos_siis = zip(*[
        process_image_data(im) for im in tqdm(pos_imgs, desc="Processing Positive Images")
    ])
    neg_iis, neg_siis = zip(*[
        process_image_data(im) for im in tqdm(neg_imgs, desc="Processing Negative Images")
    ])

    all_iis = pos_iis + neg_iis
    all_siis = pos_siis + neg_siis
    labels = np.hstack([np.ones(len(pos_iis)), np.zeros(len(neg_iis))])

    indices = np.arange(len(all_iis))
    np.random.shuffle(indices)
    
    all_iis = [all_iis[i] for i in indices]
    all_siis = [all_siis[i] for i in indices]
    labels = labels[indices]

    print("Computing Haar feature values .....")
    fv = np.zeros((len(features), len(all_iis)), dtype=np.float32)
    for i, f in enumerate(tqdm(features, desc="Evaluating features")):
        for j, (ii_j, sii_j) in enumerate(zip(all_iis, all_siis)):
            fv[i, j] = eval_feature(ii_j, sii_j, f)

    print(f"[INFO] Training AdaBoost with {len(features)} features and {len(all_iis)} samples ...")
    classifiers = adaboost_model(fv, labels)

    with open(cache_path, "wb") as f:
        pickle.dump(classifiers, f)
    print(f"[INFO] AdaBoost model saved to '{cache_path}'")

    return classifiers