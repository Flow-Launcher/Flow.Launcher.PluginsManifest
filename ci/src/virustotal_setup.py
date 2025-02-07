import requests
from pathlib import Path
import os
import sys

def setup_virustotal_scan_items(github_token: str = "") -> None:
    token = github_token or os.getenv("GITHUB_TOKEN")
    headers = {"authorization": f"token {token}"}
    url = "https://github.com/mjtimblin/Flow.Launcher.Plugin.AwsToolkit/releases/download/v1.0.3/Flow.Launcher.Plugin.AwsToolkit.zip"
    res = requests.get(url, headers)
    res.raise_for_status()

    Path("./VirusTotal_Tests").mkdir(parents=True, exist_ok=True)
    with open(f"./VirusTotal_Tests/{url.split('/')[-1]}", "wb") as f:
        f.write(res.content)

if __name__ == "__main__":
    github_token = str(sys.argv[1]) if len(sys.argv) > 1 else ""
    if not github_token:
        print("Not using token")
    setup_virustotal_scan_items(github_token)