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

def get_github_info(url):
    author = url[3]
    plugin_name = url[4]
    main_branch = url[5]
    return author, plugin_name, main_branch, raw_url

def get_plugins_data(author, plugin_name, main_branch):
    raw_path = f"https://raw.githubusercontent.com/{author}/{plugin_name}/{main_branch}"
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
    author, plugin_name, main_branch, raw_url = get_github_info(source_url)
    plugin_data = get_plugins_data(author, plugin_name, main_branch)
    icon_url = get_icon_url(raw_url, plugin_data["IcoPath"])
    download_url = get_download_url(author, plugin_name)
    update_plugin_manifest(plugin_data, source_url, download_url, icon_url)