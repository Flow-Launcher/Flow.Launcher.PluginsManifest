import sys
import json
import os
import zipfile
import io

from _utils import clean, id_name, language_list, language_name, plugin_reader

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

    for plugin in plugin_infos[::-1]:
        if plugin["Language"] == "python" and "ETag" not in plugin.keys():
            if "github.com" not in plugin["UrlSourceCode"]:
                print("Non-Github based website!")
                sys.exit(0)
            source_url = plugin["UrlSourceCode"]
            break

    latest_release = get_download_url(source_url)
    z = download_release(latest_release)
    zip_dir = os.path.join(os.getcwd(), "plugin")
    os.mkdir(zip_dir)
    z.extractall(zip_dir)
    print(read_plugin("./plugin/plugin.json")["ExecuteFileName"])







