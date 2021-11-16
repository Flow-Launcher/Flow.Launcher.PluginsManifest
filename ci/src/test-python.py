import sys
import json
import os
from pathlib import Path
import zipfile
import io
from subprocess import Popen, PIPE

from _utils import clean, id_name, language_list, language_name, plugin_reader, plugin_writer

import requests

def get_download_url(url):
    _url = url.split("/")
    author = _url[3]
    plugin_name = _url[4]
    response = requests.get(f"https://api.github.com/repos/{author}/{plugin_name}/releases/latest")
    return response.json()["assets"][0]["browser_download_url"]

def download_release(url):
    r = requests.get(url)
    r.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(r.content))

def read_plugin(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_latest_plugin(manifest):
    for _plugin in manifest[::-1]:
        if _plugin["Language"] == "python" and "Tested" not in _plugin.keys():
            if "github.com" not in _plugin["UrlSourceCode"]:
                print("Non-Github based website!")
                sys.exit(0)
            break
    else:
        print("No Untested plugin found!")
        sys.exit(1)
    return _plugin

if __name__ == "__main__":
    manifest = plugin_reader()
    plugin = get_latest_plugin(manifest)
    latest_release = get_download_url(plugin["UrlSourceCode"])
    z = download_release(latest_release)
    zip_dir = Path.cwd().joinpath("plugin")
    try:
        os.mkdir(zip_dir)
    except FileExistsError:
        pass
    z.extractall(zip_dir)
    if zip_dir.joinpath(z.namelist()[0]).is_dir():
        plugin_path = zip_dir.joinpath(z.namelist()[0])
    else:
        plugin_path = zip_dir
    execute_file = read_plugin(Path(plugin_path, "plugin.json"))["ExecuteFileName"]
    p = Popen(["python3", "-S", Path(Path(plugin_path, execute_file)), '{\"method\": \"query\", \"parameters\": [\"\"]}'], text=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    exit_code = p.wait()
    if stdout != "":
        print(stdout)
    if exit_code == 0:
        plugin_infos = plugin_reader()
        for _idx, _plugin in enumerate(plugin_infos):
            if plugin['Name'] == _plugin['Name']:
                plugin_infos[_idx]['Tested'] = True
                plugin_writer(plugin_infos)
                break
    else:
        print(f'Test failed!\nPlugin returned a non-zero exit code!\n{"#" * 9} Trace {"#" * 9}')
        if stderr != "":
            print(stderr)
            sys.exit(exit_code)







