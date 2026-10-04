#!/usr/bin/env python3
"""
audit_poisoning.py
Empirically audits the submitted model (submission-run1.zip and submission.zip)
against the poisoned external images to quantify the False Positive rate.
"""

import zipfile
import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path

POISON_SAMPLES = [
    ("Transjakarta_Zhongtong_Electric", "Indonesian Electric Bus"),
    ("Jetbus_2+_SDD", "Indonesian Intercity Coach"),
    ("DAMRI_Transjakarta", "Indonesian Transit Bus"),
    ("2_Transjakarta_(Royaltrans)", "Indonesian Transit Shuttle"),
    ("Tebet_Eco_Park", "Indonesian Bus Shelter"),
    ("2026_Bekasi_Timur_train_collision", "Crashed Taxi (Indonesian train accident)"),
]

def load_onnx_from_zip(zip_path):
    temp_dir = Path("/tmp/audit_models")
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_model = temp_dir / f"{Path(zip_path).stem}_model.onnx"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extract("model.onnx", temp_dir)
        (temp_dir / "model.onnx").rename(out_model)
    return ort.InferenceSession(str(out_model), providers=["CPUExecutionProvider"])

def predict(session, img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return []
    h, w = img.shape[:2]
    r = min(640 / h, 640 / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad = np.full((640, 640, 3), 114, dtype=np.uint8)
    pad[(640 - nh)//2 : (640 - nh)//2 + nh, (640 - nw)//2 : (640 - nw)//2 + nw] = resized
    
    inp = (pad[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0)[None, ...]
    out = session.run(None, {"images": inp})[0]
    out = out[0].T
    boxes, scores = out[:, :4], out[:, 4]
    
    mask = scores > 0.25
    boxes, scores = boxes[mask], scores[mask]
    indices = cv2.dnn.NMSBoxes(
        [[int(b[0]-b[2]/2), int(b[1]-b[3]/2), int(b[2]), int(b[3])] for b in boxes],
        [float(s) for s in scores],
        0.25, 0.45
    )
    detections = []
    if len(indices) > 0:
        for idx in indices.flatten():
            detections.append((float(scores[idx]), boxes[idx].tolist()))
    return detections

def audit():
    raw_zip = Path("/home/lechibang/Downloads/job_44_dataset_2026_10_04_08_02_40_ultralytics yolo detection 1.0.zip")
    if not raw_zip.is_file():
        print(f"Dataset zip not found: {raw_zip}")
        return

    print("Loading submitted models...")
    session_run1 = load_onnx_from_zip("submission-run1.zip")
    session_run2 = load_onnx_from_zip("submission.zip")

    models = [
        ("Run 1 Model (66.34 mAP)", session_run1),
        ("Run 2 Model (64.44 mAP)", session_run2),
    ]

    with zipfile.ZipFile(raw_zip) as zf:
        namelist = set(zf.namelist())

        for model_label, session in models:
            print(f"\n{'='*60}")
            print(f"Auditing: {model_label}")
            print(f"{'='*60}")

            for pattern, desc in POISON_SAMPLES:
                matches = [x for x in namelist if pattern in x and x.endswith((".jpg", ".png"))]
                if not matches:
                    continue
                img_data = zf.read(matches[0])
                preds = predict(session, img_data)

                if preds:
                    top_conf = max(p[0] for p in preds)
                    print(f"❌ FALSE POSITIVE: {pattern}")
                    print(f"   Category: {desc}")
                    print(f"   Detections: {len(preds)}, Top Confidence: {top_conf*100:.1f}%\n")
                else:
                    print(f"✅ Clean: {pattern} (0 detections)\n")

if __name__ == "__main__":
    audit()
