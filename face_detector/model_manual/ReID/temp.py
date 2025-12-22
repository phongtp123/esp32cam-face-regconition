import os

folder = r"../../data/saved_data/test/tung"

# ======== BƯỚC 1: ĐỔI TÊN TẠM c0_p5_{counter} ========
files = sorted(os.listdir(folder))
counter = 1

for f in files:
    ext = os.path.splitext(f)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        continue

    new_name = f"c0_p7_{counter}{ext}"
    old_path = os.path.join(folder, f)
    new_path = os.path.join(folder, new_name)

    os.rename(old_path, new_path)
    print(f"[TEMP] {f} → {new_name}")

    counter += 1


# ======== BƯỚC 2: ĐỔI TỪ c0_p5_{counter} SANG c0_p0_{counter} ========
files = sorted(os.listdir(folder))
counter = 1

for f in files:
    ext = os.path.splitext(f)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        continue

    new_name = f"c1_p2_{counter}{ext}"
    old_path = os.path.join(folder, f)
    new_path = os.path.join(folder, new_name)

    os.rename(old_path, new_path)
    print(f"[FINAL] {f} → {new_name}")

    counter += 1

print("Done!")