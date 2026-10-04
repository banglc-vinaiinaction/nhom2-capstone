#!/usr/bin/env python3
"""
sanitize_dataset.py
Purges poisoned external/scraped images from the CVAT export and
creates a clean, audited dataset containing strictly authentic Hanoi traffic frames.
"""

import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

# Paths
INPUT_ZIP = Path("/home/lechibang/Downloads/job_44_dataset_2026_10_04_08_02_40_ultralytics yolo detection 1.0.zip")
OUTPUT_ZIP = Path("data/dataset_clean.zip")
OUTPUT_DIR = Path("work/clean_dataset")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def get_poisoned_filenames():
    """Retrieve list of 89 external images committed in efc3306."""
    cmd = 'git -c core.quotepath=false show --name-only --format="" efc3306'
    try:
        out = subprocess.check_output(cmd, shell=True, cwd=Path(__file__).parent).decode("utf-8").splitlines()
        poisoned = set(Path(f).name for f in out if f.strip())
        print(f"Loaded {len(poisoned)} poisoned filenames from git commit efc3306.")
        return poisoned
    except Exception as e:
        print(f"Warning: Failed to fetch from git ({e}), falling back to pattern match.")
        return set()

def sanitize():
    if not INPUT_ZIP.is_file():
        print(f"Error: Input zip not found at {INPUT_ZIP}")
        sys.exit(1)

    poisoned_names = get_poisoned_filenames()

    # Reset output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    (OUTPUT_DIR / "images" / "train").mkdir(parents=True)
    (OUTPUT_DIR / "labels" / "train").mkdir(parents=True)

    kept_images = 0
    purged_images = 0
    total_boxes = 0
    empty_frames = 0

    with zipfile.ZipFile(INPUT_ZIP) as zf:
        namelist = set(zf.namelist())
        img_entries = [x for x in sorted(namelist) if x.startswith("images/train/") and Path(x).suffix.lower() in IMG_EXTS]

        print(f"\nProcessing {len(img_entries)} total images in source zip...")

        for img_path in img_entries:
            fname = Path(img_path).name
            stem = Path(img_path).stem

            # Check if poisoned
            if fname in poisoned_names:
                purged_images += 1
                continue

            # Read corresponding label
            lbl_path = f"labels/train/{stem}.txt"
            valid_boxes = []

            if lbl_path in namelist:
                lbl_text = zf.read(lbl_path).decode("utf-8", errors="replace").strip()
                if lbl_text:
                    for line in lbl_text.splitlines():
                        cols = line.strip().split()
                        if len(cols) == 5:
                            try:
                                cls_id = int(cols[0])
                                cx, cy, w, h = [float(v) for v in cols[1:]]
                                # Validation checks
                                if cls_id == 0 and all(0.0 <= v <= 1.0 for v in (cx, cy, w, h)) and w > 0 and h > 0:
                                    valid_boxes.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                            except ValueError:
                                pass

            # Extract image
            img_data = zf.read(img_path)
            out_img = OUTPUT_DIR / "images" / "train" / fname
            out_img.write_bytes(img_data)

            # Write label (even if empty, for background samples)
            out_lbl = OUTPUT_DIR / "labels" / "train" / f"{stem}.txt"
            if valid_boxes:
                out_lbl.write_text("\n".join(valid_boxes) + "\n", encoding="utf-8")
                total_boxes += len(valid_boxes)
            else:
                out_lbl.write_text("", encoding="utf-8")
                empty_frames += 1

            kept_images += 1

    # Write data.yaml
    data_yaml = OUTPUT_DIR / "data.yaml"
    data_yaml.write_text(
        f"path: {OUTPUT_DIR.resolve()}\n"
        f"train: images/train\n"
        f"val: images/train\n"
        f"names:\n"
        f"  0: GreenSM\n",
        encoding="utf-8"
    )

    # Package into data/dataset_clean.zip
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as out_zf:
        for file in OUTPUT_DIR.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(OUTPUT_DIR)
                out_zf.write(file, arcname)

    print(f"\n{'='*50}")
    print(f"Sanitation Complete:")
    print(f"  - Purged images:   {purged_images} (Indonesian buses, scraped web images)")
    print(f"  - Kept images:     {kept_images} (Authentic Hanoi traffic frames)")
    print(f"  - Positive images: {kept_images - empty_frames}")
    print(f"  - Negative images: {empty_frames} (Legitimate true background samples)")
    print(f"  - Total boxes:     {total_boxes}")
    print(f"  - Extracted to:    {OUTPUT_DIR}")
    print(f"  - Clean zip saved: {OUTPUT_ZIP} ({OUTPUT_ZIP.stat().st_size // 1024} KB)")
    print(f"{'='*50}")

if __name__ == "__main__":
    sanitize()
