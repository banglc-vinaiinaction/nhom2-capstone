import requests
import json
import os
from pathlib import Path

CVAT_URL = "https://well-reach-fixtures-compression.trycloudflare.com"
TASK_ID = 28
JOB_ID = 44
cookies = {
    "csrftoken": "6PjgqSUNA6U744mqkm8T7l9hfnrSgEbT",
    "sessionid": "6qda884cvjtyza0sma5tlqrsfrsxuytc"
}
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({"Accept": "application/vnd.cvat+json", "X-CSRFTOKEN": cookies["csrftoken"]})

# 1. Get task labels
r_labels = session.get(f"{CVAT_URL}/api/labels?task_id={TASK_ID}").json()
labels = [{"name": l["name"], "attributes": l["attributes"], "color": l["color"]} for l in r_labels.get("results", [])]

# 2. Get task metadata
r_task = session.get(f"{CVAT_URL}/api/tasks/{TASK_ID}").json()
task_name = r_task.get("name", f"Task_{TASK_ID}") + " (duplicate)"

# 3. Create new task
r_create = session.post(f"{CVAT_URL}/api/tasks", json={"name": task_name, "labels": labels})
if r_create.status_code not in (200, 201):
    print("Error creating task:", r_create.text)
    exit(1)
new_task = r_create.json()
new_task_id = new_task["id"]
print(f"Created new task {new_task_id}: {task_name}")

# 4. Download frames
print("Downloading frames...")
r_meta = session.get(f"{CVAT_URL}/api/jobs/{JOB_ID}/data/meta").json()
frames = r_meta.get("frames", [])
num_frames = len(frames)
download_dir = Path("/tmp/cvat_duplicate_frames")
download_dir.mkdir(parents=True, exist_ok=True)

files_to_upload = []
for i, f in enumerate(frames):
    name = f["name"].replace("/", "_")
    path = download_dir / name
    if not path.exists():
        r_frame = session.get(f"{CVAT_URL}/api/jobs/{JOB_ID}/data?type=frame&number={i}&quality=original")
        if r_frame.status_code == 200:
            path.write_bytes(r_frame.content)
        else:
            print(f"Failed to download frame {i}")
    files_to_upload.append(path)

# 5. Upload to new task
print(f"Uploading {len(files_to_upload)} frames to task {new_task_id}...")
data_payload = {
    "image_quality": 70,
    "use_zip_chunks": True,
}
# CVAT data upload requires multipart/form-data
# Let's write a loop or upload them in one request?
# CVAT API allows uploading multiple files in 'client_files'
# Let's see if we can just post a zip or files directly.
