import json
from pathlib import Path as p

from _utils import (
    plugin_writer, 
    plugin_reader)

import requests

PLUGIN_URL_FILE = 'plugin_urls.txt'
CURRENT_WORKING_DIR = p.cwd()
LIST_FILE = p.joinpath(CURRENT_WORKING_DIR, PLUGIN_URL_FILE)

def get_last_url():
    with open(LIST_FILE, "r", encoding="utf-8") as f:
        return f.read().splitlines()[-1]

def validate_github_url(url):
    if "github.com" not in url:
        raise ValueError("Invalid Github URL")

def get_default_branch(username, repo_name):
    api_url = f"https://api.github.com/repos/{username}/{repo_name}"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()["default_branch"]

def get_github_info(url):
    _url_split = url.split("/")
    username = url[-2]
    plugin_name = url[-1]
    return username, plugin_name

def get_plugins_data(author, plugin_name, default_branch):
    raw_path = f"https://raw.githubusercontent.com/{author}/{plugin_name}/{default_branch}"
    info_url = f"{raw_path}/plugin.json"
    response = requests.get(info_url)
    return response.json()

def get_download_url(author, plugin_name):
    response = requests.get(f"https://api.github.com/repos/{author}/{plugin_name}/releases/latest")
    return response.json()["assets"][0]["browser_download_url"]

def get_icon_url(author, plugin_name, branch_name, icon_path):
    icon_path = icon_path.replace("\\\\", "/").replace("\\", "/").replace(".", "")
    icon_url = "https://cdn.jsdelivr.net/gh/{author}/{plugin_name}@{branch_name}/{icon_path}"
    return icon_url

def update_plugin_manifest(plugin_data, source_url, download_url, icon_url):
    manifest = plugin_reader()
    icon_url = get_icon_url(source_url)
    manifest.append(
        {
            "ID": plugin_data["ID"],
            "Name": plugin_data["Name"],
            "Description": plugin_data["Description"],
            "Author": plugin_data["Author"],
            "Version": plugin_data["Version"],
            "Language": plugin_data["Language"],
            "Website": plugin_data["Website"],
            "UrlDownload": download_url,
            "UrlSourceCode": source_url,
            "IcoPath": icon_url
        }
    )
    plugin_writer(manifest)


if __name__ == '__main__':
    source_url = get_last_url()
    validate_github_url(source_url)
    username, plugin_name = get_github_info(source_url)
    default_branch = get_default_branch(username, plugin_name)
    plugin_data = get_plugins_data(author, plugin_name, default_branch)
    icon_url = get_icon_url(raw_url, plugin_data["IcoPath"])
    download_url = get_download_url(author, plugin_name)
    update_plugin_manifest(plugin_data, source_url, download_url, icon_url)