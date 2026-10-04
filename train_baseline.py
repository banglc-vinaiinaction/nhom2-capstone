#!/usr/bin/env python3
"""
Standalone training script extracted from train_and_export.ipynb.
Trains YOLOv8n on the dataset zip, outputs metrics and val predictions.
"""

import json
import os
import random
import shutil
import sys
import zipfile
from pathlib import Path

# ── Competition constants ──
MODEL_NAME = "yolov8n.pt"
IMGSZ = 640
CLASSES = ["GreenSM"]
TEAM_ID = 1
SEED = TEAM_ID  # simplified; notebook uses validate_team_id()

DATASET_ZIP = Path("data/yolo26n-firstrun.zip")
WORK_DIR = Path("work")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def seed_everything(seed):
    random.seed(seed)
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


def label_path_of(img):
    parts = list(img.parts)
    if "images" in parts:
        i = len(parts) - 1 - parts[::-1].index("images")
        parts[i] = "labels"
        cand = Path(*parts).with_suffix(".txt")
        if cand.is_file():
            return cand
    cand = img.with_suffix(".txt")
    return cand if cand.is_file() else None


def read_labels(label_file):
    lines, problems = [], []
    if label_file is None:
        return lines, problems
    for n, line in enumerate(label_file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        cols = line.split()
        if len(cols) != 5:
            problems.append(f"{label_file.name} line {n}: need 5 cols, got {len(cols)}")
            continue
        try:
            cls, vals = int(cols[0]), [float(x) for x in cols[1:]]
        except ValueError:
            problems.append(f"{label_file.name} line {n}: non-numeric")
            continue
        if cls != 0:
            problems.append(f"{label_file.name} line {n}: class {cls} invalid")
        elif not all(0.0 <= v <= 1.0 for v in vals):
            problems.append(f"{label_file.name} line {n}: coords out of [0,1]")
        else:
            lines.append(" ".join(cols))
    return lines, problems


def prepare_dataset(zip_path, out_dir, seed, val_ratio=0.2):
    out_dir = Path(out_dir)
    raw_dir = out_dir.parent / "raw"
    for d in (out_dir, raw_dir):
        shutil.rmtree(d, ignore_errors=True)
    raw_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(raw_dir)

    images = sorted(p for p in raw_dir.rglob("*") if p.suffix.lower() in IMG_EXTS and "__MACOSX" not in p.parts)
    if len(images) < 2:
        raise RuntimeError(f"Need >= 2 images, found {len(images)}")

    items, problems, n_boxes = [], [], 0
    for img in images:
        lines, probs = read_labels(label_path_of(img))
        problems += probs
        n_boxes += len(lines)
        items.append((img, lines))

    if problems:
        for p in problems[:10]:
            print(f"  ⚠️ {p}")
        raise RuntimeError(f"Label errors: {len(problems)} total")
    if n_boxes == 0:
        raise RuntimeError("No bounding boxes found in labels")

    # Check for pre-existing split
    def is_in(img, names):
        return any(part.lower() in names for part in img.relative_to(raw_dir).parts[:-1])

    pre_val = [it for it in items if is_in(it[0], {"val", "valid", "validation"})]
    pre_train = [it for it in items if is_in(it[0], {"train"})]
    if pre_val and pre_train:
        split = {"train": pre_train, "val": pre_val}
    else:
        order = list(range(len(items)))
        random.Random(seed).shuffle(order)
        n_val = max(1, round(len(items) * val_ratio))
        split = {"val": [items[i] for i in order[:n_val]], "train": [items[i] for i in order[n_val:]]}

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
    print(f"Dataset: {len(images)} images, {n_boxes} boxes.")
    print(f"  train: {counts['train']['images']} imgs / {counts['train']['boxes']} boxes")
    print(f"  val:   {counts['val']['images']} imgs / {counts['val']['boxes']} boxes")
    return {"data_yaml": str(data_yaml), "counts": counts, "images": len(images), "boxes": n_boxes}


def main():
    import torch
    print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO GPU (CPU only)")

    seed_everything(SEED)

    # ── Prepare dataset ──
    print("\n=== 1. Preparing dataset ===")
    dataset = prepare_dataset(DATASET_ZIP, WORK_DIR / "dataset", SEED)

    # ── Train ──
    print("\n=== 2. Training ===")
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
        plots=True,  # generate confusion matrix, PR curve, etc.
    )

    seed_everything(SEED)
    model = YOLO(MODEL_NAME)
    model.train(**train_args)
    best_weights = Path(model.trainer.best)
    print(f"\nBest weights: {best_weights}")

    # ── Validate & generate detailed metrics ──
    print("\n=== 3. Validation metrics ===")
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
    print(f"  mAP50:      {metrics.box.map50:.4f}")
    print(f"  mAP50-95:   {metrics.box.map:.4f}")
    print(f"  Precision:  {metrics.box.mp:.4f}")
    print(f"  Recall:     {metrics.box.mr:.4f}")
    print(f"{'='*50}")

    # ── List output files ──
    train_dir = WORK_DIR / "runs" / "train"
    val_dir = WORK_DIR / "runs" / "val"
    print(f"\n=== 4. Output files ===")
    print(f"Training outputs: {train_dir}")
    for f in sorted(train_dir.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size // 1024}KB)")

    print(f"\nValidation outputs: {val_dir}")
    for f in sorted(val_dir.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
