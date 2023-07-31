import sys
from time import time
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

def _mkdir(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.mkdir(path)

def print_section(title: str, text: str, char: str = "#", repeat_times: int = 20) -> None:
    """Print a section with a title and text."""
    _title_line = f'{char * repeat_times} {title} {char * repeat_times}'
    print(_title_line, text, sep="\n")

def get_github_release(url: str) -> str:
    """Get latest release from GitHub."""
    _url = url.split("/")
    author = _url[3]
    plugin_name = _url[4]
    response = requests.get(f"https://api.github.com/repos/{author}/{plugin_name}/releases/latest")
    download_url = response.json()["assets"][0]["browser_download_url"]
    print(f'Downloading plugin {plugin_name} from {download_url}')
    return download_url

def install(plugin: dict) -> str:
    """Download and install plugin."""
    if "UrlDownload" in plugin.keys():
        print(f"Downloading plugin {plugin['Name']} from {plugin['UrlDownload']}")
        file = _download(plugin["UrlDownload"])
    else:
        file = _download(get_github_release(plugin["UrlSourceCode"]))
    extract_dir = USER_PATH.joinpath("Plugins", plugin['Name'])
    _mkdir(extract_dir)
    print("Extracting...")
    file.extractall(extract_dir)
    return extract_dir

def _download(url: str) -> zipfile.ZipFile:
    """Download plugin from url."""
    r = requests.get(url)
    r.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(r.content))

def read_plugin(file_path: str) -> dict:
    """Read plugin's manifest."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_latest_plugin(manifest: dict) -> dict:
    """Get latest plugin from manifest."""
    untested_plugins = []
    for _plugin in manifest[::-1]:
        if _plugin["Language"] == "python" and "Tested" not in _plugin.keys():
            untested_plugins.append(_plugin)
            break
        if _plugin["Language"] != "python" and "Tested" not in _plugin.keys():
            print_section("Non-Python plugin detected, test not required.", f'Detected Plugin: {_plugin["Name"]}\nPassing test...')
            sys.exit(0)
    if len(untested_plugins) == 0:
        print_section("Test failed!", "The new plugin should not have the \"Tested\" key.")
        sys.exit(1)
    return untested_plugins[0]

def get_all_python_plugins(manifest: dict):
    return [plugin for plugin in manifest if plugin["Language"].lower() == "python"]

def run_plugin(plugin_name: str, plugin_path: str, execute_path: str) -> None:
    """Run plugin and check output."""
    os.chdir(plugin_path)
    default_settings = init_settings(plugin_name, plugin_path)
    args = json.dumps(
        {"method": "query", "parameters": [""], "Settings": default_settings}
    )
    full_args = ["python", "-S", Path(plugin_path, execute_path), args]
    # Older Flox used environmental variable to locate Images directory
    os.environ["PYTHONPATH"] = str(USER_PATH.joinpath("PythonEmbeddable"))
    print_section("Input", full_args)
    p = Popen(full_args, text=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    exit_code = p.wait()
    if stdout != "":
        print_section("Output", stdout)
        valid_json, json_msg = test_valid_json(stdout)
    if exit_code == 0 and valid_json:
        print_section("Test passed!", "", repeat_times=20)
    else:
        print(f'Test failed!\nPlugin returned a non-zero exit code!')
        if stderr != "":
            print_section('Trace', stderr)
        if json_msg:
            print(json_msg)
        sys.exit(max(exit_code, 1))


def setup_flow_environment() -> None:
    """Setup Flow Launcher local & roaming directory."""
    _mkdir(USER_PATH)
    _mkdir(APP_PATH)
    for _dir in USER_DIRS:
        _mkdir(Path(USER_PATH, _dir))
    for _dir in APP_DIRS:
        _mkdir(Path(APP_PATH, _dir))
    os.makedirs(Path(USER_PATH, "Settings", "Plugins"), exist_ok=True)
    os.makedirs(Path(APP_PATH, "app-1.0.0"), exist_ok=True)
    with open(USER_PATH.joinpath("Settings", "Settings.json"), "w") as f:
        json.dump({
            "PluginSettings": {"Plugins": {}},
        }, f, indent=4)

def init_settings(plugin_name: str, plugin_path: str) -> dict:
    """Read plugins template file and initialize settings."""
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

def create_plugin_settings(id, name, version, action_keyword) -> None:
    """Add settings for the plugin to Flow Launcher's settings file."""
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

def test_valid_json(data: dict) -> None:
    """Test if the data is valid JSON."""
    e = None
    try:
        json.loads(data)
    except Exception as e:
        return False, e
    else:
        return True, e

if __name__ == "__main__":
    #Pass 'all' as an arg to test for all Python plugins

    start = time()

    py_plugins = []

    # Load plugins manifest
    manifest = plugin_reader()

    if len(sys.argv) > 1 and str(sys.argv[1]) == "all":
        py_plugins = get_all_python_plugins(manifest)

    else:
        # Get and test latest untested plugin for PR submission
        py_plugins.append(get_latest_plugin(manifest))
        print(f"Found untested plugin: {py_plugins[0]['Name']} (Version: {py_plugins[0]['Version']})")

    # Set up the Flow environment
    print("Setting up Flow Launcher environment...")
    setup_flow_environment()

    for plugin in py_plugins:
        # Download latest release
        extract_dir = install(plugin)

        # Locate Plugins manifest file (plugins.json)
        for path in Path(extract_dir).glob("**/plugin.json"):
            execute_file = read_plugin(path)["ExecuteFileName"]
            plugin_id = read_plugin(path)["ID"]
            plugin_path = Path(path).parent
            plugin_json_path = path

        # Add plugin to Flow Launcher's settings file
        print(f"Adding plugin {plugin['Name']} to Flow Launcher's settings file...")
        create_plugin_settings(plugin_id, plugin['Name'], plugin['Version'], read_plugin(plugin_json_path)['ActionKeyword'])

        # Run plugin
        print(f"Running plugin test for {plugin['Name']} ...")
        run_plugin(plugin['Name'], plugin_path, execute_file)
        print(f"Test for {plugin['Name']} finished in {time() - start:.2f} seconds.\n")







