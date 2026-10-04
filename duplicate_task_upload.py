import requests
import zipfile
import os
from pathlib import Path

CVAT_URL = "https://well-reach-fixtures-compression.trycloudflare.com"
NEW_TASK_ID = 29
cookies = {
    "csrftoken": "6PjgqSUNA6U744mqkm8T7l9hfnrSgEbT",
    "sessionid": "6qda884cvjtyza0sma5tlqrsfrsxuytc"
}
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({"Accept": "application/vnd.cvat+json", "X-CSRFTOKEN": cookies["csrftoken"]})

download_dir = Path("/tmp/cvat_duplicate_frames")
zip_path = Path("/tmp/cvat_duplicate_frames.zip")

print("Zipping frames...")
with zipfile.ZipFile(zip_path, 'w') as zf:
    for file in download_dir.glob("*"):
        zf.write(file, file.name)

print("Uploading zip to Task 29...")
with open(zip_path, "rb") as f:
    files = {"client_files[0]": (zip_path.name, f, "application/zip")}
    data = {"image_quality": 70, "use_zip_chunks": "true", "use_cache": "true"}
    r = session.post(f"{CVAT_URL}/api/tasks/{NEW_TASK_ID}/data", data=data, files=files)
    print("Response:", r.status_code, r.text)
