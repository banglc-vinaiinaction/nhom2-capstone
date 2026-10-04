import requests
from PIL import Image
from io import BytesIO

CVAT_URL = "https://well-reach-fixtures-compression.trycloudflare.com"
JOB_ID = 44
cookies = {
    "csrftoken": "6PjgqSUNA6U744mqkm8T7l9hfnrSgEbT",
    "sessionid": "6qda884cvjtyza0sma5tlqrsfrsxuytc"
}
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({"Accept": "application/vnd.cvat+json", "X-CSRFTOKEN": cookies["csrftoken"]})

url = f"{CVAT_URL}/api/jobs/{JOB_ID}/data?type=frame&number=0&quality=original"
r = session.get(url)
img = Image.open(BytesIO(r.content))
print(f"Image size: {img.size}")
