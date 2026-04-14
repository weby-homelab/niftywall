import os
import requests
import json

USERNAME = os.getenv("DOCKER_HUB_USERNAME")
PASSWORD = os.getenv("DOCKER_HUB_PASSWORD")
REPO = "webyhomelab/niftywall"

# Authenticate
auth_resp = requests.post("https://hub.docker.com/v2/users/login/", json={"username": USERNAME, "password": PASSWORD})
token = auth_resp.json().get("token")
headers = {"Authorization": f"JWT {token}", "Content-Type": "application/json"}

# Read files
with open("README_ENG.md", "r") as f:
    eng_lines = f.readlines()
with open("README.md", "r") as f:
    ua_lines = f.readlines()

# Remove badges/headers (everything before the first "# ")
def clean_readme(lines):
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start_idx = i
            break
    return "".join(lines[start_idx:])

eng_clean = clean_readme(eng_lines)
ua_clean = clean_readme(ua_lines)

# Assemble overview
nav = "[English 🇬🇧](https://github.com/weby-homelab/niftywall/blob/main/README_ENG.md) | [Українська 🇺🇦](https://github.com/weby-homelab/niftywall/blob/main/README.md)\n\n---\n"
footer = "\n\n---\nMade with ❤️ in Kyiv\n✦ 2026 Weby Homelab ✦"
overview = nav + eng_clean + "\n\n---\n\n" + ua_clean + footer

# Patch Docker Hub
patch_url = f"https://hub.docker.com/v2/repositories/{REPO}/"
payload = {"full_description": overview}
res = requests.patch(patch_url, headers=headers, json=payload)
if res.status_code == 200:
    print("Successfully updated Docker Hub Overview.")
else:
    print(f"Failed to update Docker Hub: {res.status_code} - {res.text}")
