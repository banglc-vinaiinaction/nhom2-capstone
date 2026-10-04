import requests
import time

CVAT_URL = "https://well-reach-fixtures-compression.trycloudflare.com"
OLD_JOB_ID = 44
NEW_TASK_ID = 29
cookies = {
    "csrftoken": "6PjgqSUNA6U744mqkm8T7l9hfnrSgEbT",
    "sessionid": "6qda884cvjtyza0sma5tlqrsfrsxuytc"
}
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({"Accept": "application/vnd.cvat+json", "X-CSRFTOKEN": cookies["csrftoken"]})

# First check if Task 29 data has finished processing
while True:
    r = session.get(f"{CVAT_URL}/api/tasks/{NEW_TASK_ID}")
    status = r.json().get("status")
    print("Task status:", status)
    if status == "annotation":
        break
    time.sleep(2)

# Get old annotations
print("Fetching old annotations...")
r_anno = session.get(f"{CVAT_URL}/api/jobs/{OLD_JOB_ID}/annotations").json()

# Task 29 should have a single job since it's the same segment size
r_jobs = session.get(f"{CVAT_URL}/api/jobs?task_id={NEW_TASK_ID}").json()
new_job_id = r_jobs["results"][0]["id"]

# Upload to new job
print("Uploading annotations to new Job", new_job_id)
r_put = session.put(f"{CVAT_URL}/api/jobs/{new_job_id}/annotations", json={
    "shapes": r_anno.get("shapes", []),
    "tracks": r_anno.get("tracks", []),
    "tags": r_anno.get("tags", []),
    "version": 0
})
print("Result:", r_put.status_code)
