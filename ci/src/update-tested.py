import sys
import json
import os
import zipfile
import io

from _utils import clean, id_name, language_list, language_name, plugin_reader, plugin_writer

import requests

def get_download_url(url):
    _url = url.split("/")
    author = _url[3]
    plugin_name = _url[4]
    response = requests.get(f"https://api.github.com/repos/{author}/{plugin_name}/releases/latest")
    return response.json()["assets"][0]["browser_download_url"]

def download_release(url):
    r = requests.get(latest_release)
    r.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(r.content))

def read_plugin(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    plugin_infos = plugin_reader()

    for idx, plugin in enumerate(plugin_infos):
        if plugin["Language"] == "python" and "Tested" not in plugin.keys():
            plugin_infos[idx]["Tested"] = True

    plugin_writer(plugin_infos)







