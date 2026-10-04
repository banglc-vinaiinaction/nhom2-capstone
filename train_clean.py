#!/usr/bin/env python3
"""
train_clean.py
Trains YOLOv8n on the sanitized dataset (data/dataset_clean.zip) without poisoned samples.
Generates metrics and exports a clean ONNX model.
"""

import sys
import shutil
import random
import zipfile
from pathlib import Path

MODEL_NAME = "yolov8n.pt"
IMGSZ = 640
CLASSES = ["GreenSM"]
TEAM_ID = 1
SEED = TEAM_ID

DATASET_ZIP = Path("data/dataset_clean.zip")
WORK_DIR = Path("work/clean_run")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def seed_everything(seed):
    random.seed(seed)
    import os
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def prepare_dataset(zip_path, out_dir, seed, val_ratio=0.2):
    out_dir = Path(out_dir)
    raw_dir = out_dir.parent / "raw_clean"
    for d in (out_dir, raw_dir):
        shutil.rmtree(d, ignore_errors=True)
    raw_dir.mkdir(parents=True)
    
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(raw_dir)

    images = sorted(p for p in raw_dir.rglob("*") if p.suffix.lower() in IMG_EXTS and "__MACOSX" not in p.parts)
    if len(images) < 2:
        raise RuntimeError(f"Need >= 2 images, found {len(images)}")

    items = []
    n_boxes = 0
    for img in images:
        lbl_file = img.parent.parent / "labels" / img.parent.name / f"{img.stem}.txt"
        if not lbl_file.is_file():
            lbl_file = img.with_suffix(".txt")
        
        lines = []
        if lbl_file.is_file():
            content = lbl_file.read_text(encoding="utf-8").strip()
            if content:
                lines = [l.strip() for l in content.splitlines() if l.strip()]
        n_boxes += len(lines)
        items.append((img, lines))

    # Deterministic split
    order = list(range(len(items)))
    random.Random(seed).shuffle(order)
    n_val = max(1, round(len(items) * val_ratio))
    split = {
        "val": [items[i] for i in order[:n_val]],
        "train": [items[i] for i in order[n_val:]]
    }

    counts = {}
    for name, rows in split.items():
        (out_dir / "images" / name).mkdir(parents=True)
        (out_dir / "labels" / name).mkdir(parents=True)
        for k, (img, lines) in enumerate(rows):
            stem = f"{k:05d}_{img.stem}"
            shutil.copyfile(img, out_dir / "images" / name / f"{stem}{img.suffix.lower()}")
            (out_dir / "labels" / name / f"{stem}.txt").write_text(
                "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
            )
        counts[name] = {"images": len(rows), "boxes": sum(len(lines) for _, lines in rows)}

    data_yaml = out_dir / "data.yaml"
    names_text = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASSES))
    data_yaml.write_text(
        f"path: {out_dir.resolve()}\ntrain: images/train\nval: images/val\nnames:\n{names_text}\n",
        encoding="utf-8",
    )
    print(f"Clean Dataset Prepared: {len(images)} total images, {n_boxes} boxes.")
    print(f"  Train: {counts['train']['images']} images / {counts['train']['boxes']} boxes")
    print(f"  Val:   {counts['val']['images']} images / {counts['val']['boxes']} boxes")
    return {"data_yaml": str(data_yaml), "counts": counts}

def main():
    import torch
    print("Device:", "GPU (" + torch.cuda.get_device_name(0) + ")" if torch.cuda.is_available() else "CPU only")

    seed_everything(SEED)

    print("\n=== 1. Preparing clean dataset ===")
    dataset = prepare_dataset(DATASET_ZIP, WORK_DIR / "dataset", SEED)

    print("\n=== 2. Training YOLOv8n ===")
    from ultralytics import YOLO

    train_args = dict(
        data=dataset["data_yaml"],
        imgsz=IMGSZ,
        epochs=50,
        batch=16,
        seed=SEED,
        deterministic=True,
        project=str(WORK_DIR / "runs"),
        name="train",
        exist_ok=True,
        plots=True,
    )

    model = YOLO(MODEL_NAME)
    model.train(**train_args)
    best_weights = Path(model.trainer.best)
    print(f"\nTraining Complete. Best weights: {best_weights}")

    print("\n=== 3. Validating on Clean Validation Split ===")
    val_model = YOLO(str(best_weights))
    metrics = val_model.val(
        data=dataset["data_yaml"],
        imgsz=IMGSZ,
        project=str(WORK_DIR / "runs"),
        name="val",
        exist_ok=True,
        plots=True,
        save_json=True,
    )

    print(f"\n{'='*50}")
    print(f"  CLEAN VALIDATION METRICS:")
    print(f"  mAP50:      {metrics.box.map50:.4f}")
    print(f"  mAP50-95:   {metrics.box.map:.4f}")
    print(f"  Precision:  {metrics.box.mp:.4f}")
    print(f"  Recall:     {metrics.box.mr:.4f}")
    print(f"{'='*50}")

    # Export clean ONNX
    print("\n=== 4. Exporting to ONNX ===")
    onnx_path = val_model.export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)
    print(f"Exported clean ONNX to: {onnx_path}")

if __name__ == "__main__":
    main()
