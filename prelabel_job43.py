#!/usr/bin/env python3
"""
Pre-label Job 43 (Task 27) on CVAT using YOLO26n.
Target: 4-wheeled vehicles -> GreenSM label (ID 62)
"""

import sys
import shutil
import sqlite3
from pathlib import Path
import requests
from ultralytics import YOLO

CVAT_URL = "https://well-reach-fixtures-compression.trycloudflare.com"
TASK_ID = 27
JOB_ID = 43
LABEL_ID = 62  # GreenSM
WEIGHTS_PATH = "/mnt/data/projects/vinai-in-action/yolo26-experiment/yolo26n.pt"
IMAGES_DIR = Path("/mnt/data/projects/vinai-in-action/nhom2-capstone/resource/images_640640")

def get_session():
    # Extract cookies from Firefox default profile
    src = Path("/home/lechibang/.config/mozilla/firefox/gxtd8sci.default-release/cookies.sqlite")
    dst = Path("/tmp/ff_cookies_prelabel.sqlite")
    shutil.copy2(src, dst)

    conn = sqlite3.connect(dst)
    cur = conn.cursor()
    cur.execute('SELECT name, value FROM moz_cookies WHERE host LIKE "%well-reach-fixtures-compression%"')
    cookies = dict(cur.fetchall())
    conn.close()

    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        "Accept": "application/vnd.cvat+json",
        "X-CSRFTOKEN": cookies.get("csrftoken", ""),
        "Referer": CVAT_URL,
    })
    return session

def check_health(session):
    print("--- 1. Kiểm tra trạng thái API (Health check) ---")
    try:
        r_health = session.get(f"{CVAT_URL}/api/server/health", headers={"Accept": "application/json"}, timeout=10)
        print(f"Server Health Status: {r_health.status_code}")
        print("Health Details:", r_health.json())
        
        r_about = session.get(f"{CVAT_URL}/api/server/about", timeout=10)
        print(f"Server Version: {r_about.json().get('version')}")
        
        if r_health.status_code != 200:
            raise RuntimeError("API CVAT không healthy!")
    except Exception as e:
        print(f"❌ Lỗi kết nối API: {e}")
        sys.exit(1)

def run_prelabel():
    session = get_session()
    check_health(session)

    print("\n--- 2. Kiểm tra Task 27 & Job 43 ---")
    r_task = session.get(f"{CVAT_URL}/api/tasks/{TASK_ID}")
    task_data = r_task.json()
    print(f"Task {TASK_ID}: {task_data.get('name')}")

    r_labels = session.get(f"{CVAT_URL}/api/labels?task_id={TASK_ID}").json()
    print("Labels:", [(l['id'], l['name']) for l in r_labels.get('results', [])])

    r_meta = session.get(f"{CVAT_URL}/api/jobs/{JOB_ID}/data/meta").json()
    frames = r_meta.get("frames", [])
    print(f"Job {JOB_ID} frames count: {len(frames)}")

    print(f"\n--- 3. Tải mô hình YOLO26n từ {WEIGHTS_PATH} ---")
    model = YOLO(WEIGHTS_PATH)

    shapes = []
    # 4-wheeled vehicles: 2 (car), 7 (truck)
    classes_to_detect = [2, 7]
    min_dim = 15  # guideline: bỏ qua đối tượng < 15x15

    print(f"\n--- 4. Chạy suy luận (4-wheeled vehicles, conf=0.25, agnostic_nms=True) ---")
    for frame_idx, frame_info in enumerate(frames):
        img_name = frame_info["name"]
        img_path = IMAGES_DIR / img_name
        if not img_path.exists():
            print(f"⚠️ Không tìm thấy ảnh: {img_path}")
            continue

        res = model.predict(
            str(img_path),
            conf=0.25,
            classes=classes_to_detect,
            agnostic_nms=True,
            verbose=False
        )[0]

        for box in res.boxes:
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            # Clamp to [0, 640]
            x1 = max(0.0, min(640.0, x1))
            y1 = max(0.0, min(640.0, y1))
            x2 = max(0.0, min(640.0, x2))
            y2 = max(0.0, min(640.0, y2))
            w = x2 - x1
            h = y2 - y1

            if w < min_dim or h < min_dim:
                continue

            conf = float(box.conf[0].item())
            cls_name = model.names[int(box.cls[0].item())]

            shapes.append({
                "type": "rectangle",
                "occluded": False,
                "outside": False,
                "points": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "label_id": LABEL_ID,
                "frame": frame_idx,
                "attributes": [],
                "source": "auto",
                "score": round(conf, 4)
            })

    print(f"\nTổng số bounding box xe 4 bánh tạo được: {len(shapes)} trên {len(frames)} frames.")

    print(f"\n--- 5. Đẩy {len(shapes)} annotations lên CVAT Job {JOB_ID} ---")
    put_url = f"{CVAT_URL}/api/jobs/{JOB_ID}/annotations"
    payload = {
        "shapes": shapes,
        "tracks": [],
        "tags": [],
        "version": 0
    }
    
    put_resp = session.put(put_url, json=payload)
    print(f"Response status: {put_resp.status_code}")
    if put_resp.status_code not in (200, 201):
        print(f"❌ Lỗi khi gửi annotations: {put_resp.text}")
        sys.exit(1)

    print("✅ Đẩy annotations thành công!")

    # Verify
    verify_resp = session.get(f"{CVAT_URL}/api/jobs/{JOB_ID}/annotations").json()
    verified_shapes = len(verify_resp.get("shapes", []))
    print(f"Kiểm tra lại trên CVAT: Job {JOB_ID} hiện có {verified_shapes} shapes.")

if __name__ == "__main__":
    run_prelabel()
