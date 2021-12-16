import sys
import json
import os
from pathlib import Path
import zipfile
import io
from subprocess import Popen, PIPE

from _utils import clean, id_name, language_list, language_name, plugin_reader, plugin_writer

import requests
import yaml

USER_PATH = Path(os.environ["APPDATA"], "FlowLauncher")
APP_PATH = Path(os.environ["LOCALAPPDATA"], "FlowLauncher")
USER_DIRS = ["Settings", "Logs", "PythonEmbeddable", "Themes", "Plugins"]
APP_DIRS = ["Images"]

def _mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

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

def run_plugin(plugin_path, execute_path):
    os.chdir(plugin_path)
    default_settings = init_settings(plugin_name, plugin_path)
    args = json.dumps(
        {"method": "query", "parameters": [""], "Settings": default_settings}
    )
    p = Popen(["python", "-S", Path(Path(plugin_path, execute_path)), args], text=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    exit_code = p.wait()
    if stdout != "":
        print(f'{"#" * 9} Output {"#" * 9}\n{stdout}')
    if exit_code == 0:
        print("Test passed!")
    else:
        print(f'Test failed!\nPlugin returned a non-zero exit code!\n{"#" * 9} Trace {"#" * 9}')
        if stderr != "":
            print(stderr)
        sys.exit(exit_code)

def setup_flow_environment():
    _mkdir(USER_PATH)
    _mkdir(APP_PATH)
    for _dir in USER_DIRS:
        _mkdir(Path(USER_PATH, _dir))
    for _dir in APP_DIRS:
        _mkdir(Path(APP_PATH, _dir))
    os.makedirs(Path(USER_PATH, "Settings", "Plugins"), exist_ok=True)
    os.makedirs(Path(APP_PATH, "app-1.9.0"), exist_ok=True)
    with open(USER_PATH.joinpath("Settings", "Settings.json"), "w") as f:
        json.dump({
            "PluginSettings": {"Plugins": {}},
        }, f, indent=4)
    
def init_settings(plugin_name, plugin_path):
    default_values = {}
    path = Path(plugin_path, "SettingsTemplate.yaml")
    if path.exists():
        with open("SettingsTemplate.yaml", "r") as f:
            settings = yaml.safe_load(f)
        for key in settings.keys():
            for ui_element in settings[key]:
                if "defaultValue" in ui_element['attributes'].keys():
                    default_values[ui_element['attributes']['name']] = ui_element['attributes']['defaultValue']
        settings_path = Path(USER_PATH, "Settings", "Plugins", plugin_name)
        _mkdir(settings_path)
        with open(settings_path.joinpath("Settings.json"), "w") as f:
            f.write(json.dumps(default_values, indent=4))             
    return json.dumps(default_values)

def create_plugin_settings(id, name, version, action_keyword):
    with open(USER_PATH.joinpath("Settings", "Settings.json"), "r") as f:
        settings = json.load(f)
    settings['PluginSettings']['Plugins'][id] = {
        "ID": id,
        "Name": name,
        "Version": version,
        "ActionKeywords": [
            action_keyword
        ]
    }
    with open(USER_PATH.joinpath("Settings", "Settings.json"), "w") as f:
        json.dump(settings, f, indent=4)


if __name__ == "__main__":
    # Load plugins manifest
    manifest = plugin_reader()

    # Set up the Flow environment
    print("Setting up Flow Launcher environment...")
    setup_flow_environment()

    # Get latest untested plugin
    plugin = get_latest_plugin(manifest)
    print(f"Found untested plugin: {plugin['Name']}")

    # Download latest release
    latest_release = get_download_url(plugin["UrlSourceCode"])
    print("Downloading latest release...")
    z = download_release(latest_release)
    zip_dir = USER_PATH.joinpath("Plugins", plugin['Name'])
    try:
        _mkdir(zip_dir)
    except FileExistsError:
        pass
    print("Extracting...")
    z.extractall(zip_dir)
    for path in Path(zip_dir).glob("**/plugin.json"):
        execute_file = read_plugin(path)["ExecuteFileName"]
        id = read_plugin(path)["ID"]
        plugin_path = Path(path).parent
    print("Adding plugin to Flow Launcher's settings file...")
    create_plugin_settings(id, plugin['Name'], plugin['Version'], read_plugin(path)['ActionKeyword'])
    print("Running plugin...")
    run_plugin(plugin_path, execute_file)







