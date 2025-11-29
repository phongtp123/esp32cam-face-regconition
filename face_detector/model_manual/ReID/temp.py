import os

folder = r"../../data/saved_data/test/stranger"  # đường dẫn tới thư mục
files = sorted(os.listdir(folder))           # sắp xếp tên file theo thứ tự
counter = 1

for f in files:
    ext = os.path.splitext(f)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        continue

    new_name = f"c0_p0_{counter}{ext}"
    old_path = os.path.join(folder, f)
    new_path = os.path.join(folder, new_name)

    # Nếu trùng tên → bỏ qua
    if old_path == new_path:
        print(f"Skipping (same name): {f}")
    else:
        # Nếu tên mới đã tồn tại → xoá/ghi đè hoặc đổi số khác
        if os.path.exists(new_path):
            print(f"File existed, removing: {new_name}")
            os.remove(new_path)

        os.rename(old_path, new_path)
        print(f"{f} → {new_name}")

    counter += 1

print("Done!")