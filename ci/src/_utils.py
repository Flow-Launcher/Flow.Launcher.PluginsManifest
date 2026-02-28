# -*-coding: utf-8 -*-
import atexit
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, TypeVar

# If adding a third-party library here, check CI workflows Python files
# that are dependant on this and require pip install.

github_download_url_regex = re.compile(
    r"https://github\.com/(?P<author>[a-zA-Z0-9-]+)/(?P<repo>[a-zA-Z0-9\.\-\_]*)/releases/download/(?P<version>[a-zA-Z\.0-9]+)/(?P<filename>.*)\.zip"
)

# path
utils_path = Path(__file__).resolve()

src_dir = utils_path.parent
ci_dir = src_dir.parent
base_dir = ci_dir.parent
plugin_dir = base_dir / "plugins/"
etag_file = base_dir / "etags.json"

# constants
id_name = "ID"
language_name = "Language"
language_list = (
    "csharp",
    "executable",
    "fsharp",
    "python",
    "javascript",
    "typescript",
    "python_v2",
    "executable_v2",
    "javascript_v2",
    "typescript_v2",
)
etag = "ETag"
version = "Version"
url_sourcecode = "UrlSourceCode"
url_download = "UrlDownload"
url_release = "https://api.github.com/repos/{repo}/releases/latest"
icon_path = "IcoPath"
author = "Author"
description = "Description"
plugin_name = "Name"
github_url = "https://github.com"
tested = "Tested"
release_date = "LatestReleaseDate"
date_added = "DateAdded"
website = "Website"
minimum_app_version = "MinimumAppVersion"

necessary_fields = (
    id_name,
    plugin_name,
    description,
    author,
    version,
    language_name,
    website,
    url_download,
    url_sourcecode,
    icon_path,
)

optional_fields = (
    minimum_app_version,
    tested,
    release_date,
    date_added
)

# typing
PluginType = Dict[str, str]
P = TypeVar("P", bound=PluginType)
PluginsType = List[PluginType]
Ps = TypeVar("Ps", bound=PluginsType)

ETagsType = Dict[str, str]


def _raise_on_duplicate_keys(pairs):
    seen = set()
    duplicates = set()
    result = {}
    for key, value in pairs:
        if key in seen:
            duplicates.add(key)
        else:
            seen.add(key)
            result[key] = value
    if duplicates:
        sorted_duplicates = sorted(duplicates)
        raise ValueError(f"Duplicate keys found: {sorted_duplicates}")
    return result


def _is_pull_request() -> bool:
    return os.environ.get("GITHUB_EVENT_NAME") == "pull_request"


_pr_plugin_dir: str | None = None


def _get_pr_plugin_dir() -> str:
    """Download plugin files from the PR head repository to a temp directory and return its path."""
    global _pr_plugin_dir
    if _pr_plugin_dir is not None:
        return _pr_plugin_dir

    repo = os.environ.get("PR_HEAD_REPO", "")
    branch = os.environ.get("PR_HEAD_BRANCH", "main")

    if not repo:
        _pr_plugin_dir = str(plugin_dir)
        return _pr_plugin_dir

    temp_dir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, temp_dir, ignore_errors=True)

    api_url = f"https://api.github.com/repos/{repo}/contents/plugins?ref={branch}"
    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "flow-launcher-validator"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            contents = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch plugin list from {api_url}: {e}") from e

    for item in contents:
        if item["name"].endswith(".json") and item["type"] == "file":
            file_req = urllib.request.Request(
                item["download_url"],
                headers={"User-Agent": "flow-launcher-validator"},
            )
            try:
                with urllib.request.urlopen(file_req) as r:
                    file_path = os.path.join(temp_dir, item["name"])
                    with open(file_path, "wb") as f:
                        f.write(r.read())
            except urllib.error.URLError as e:
                raise RuntimeError(f"Failed to download plugin file {item['name']}: {e}") from e

    _pr_plugin_dir = temp_dir
    return _pr_plugin_dir


def _effective_plugin_dir() -> Path:
    if _is_pull_request():
        return Path(_get_pr_plugin_dir())
    return plugin_dir


def plugin_reader() -> P:
    plugin_file_paths = get_plugin_file_paths()

    manifests = []

    for plugin_path in plugin_file_paths:
        with open(plugin_path, "r", encoding="utf-8") as f:
            manifests.append(json.load(f))

    return manifests


def save_plugins_json_file(content: list[dict[str]]) -> None:
    with open("plugins.json", "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)


def get_plugin_file_paths() -> list[str]:
    dir_path = _effective_plugin_dir()
    return [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]


def get_plugin_filenames() -> list[str]:
    return os.listdir(_effective_plugin_dir())


def etag_reader() -> ETagsType:
    with open(etag_file, "r", encoding="utf-8") as f:
        return json.load(f)


def plugin_writer(content: P):
    for plugin in content:
        with open(plugin_dir / f"{plugin[plugin_name]}-{plugin[id_name]}.json", "w", encoding="utf-8") as f:
            json.dump(plugin, f, indent=4)


def etags_writer(content: ETagsType):
    with open(etag_file, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)


def clean(string: str, flag="-") -> str:
    return string.lower().replace(flag, "").strip()


def version_tuple(version: str) -> tuple:
    version = clean(version, "v")
    return tuple(version.split("."))


def check_url(url: str) -> bool:
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None


def get_file_plugins_json_info(required_key: str = "") -> list[dict[str, str]]:
    with open("plugins.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if not required_key:
        return data

    return [{required_key: plugin[required_key]} for plugin in data]


def get_new_plugin_submission_ids() -> list[str]:
    plugins_json_ids = [item["ID"] for item in get_file_plugins_json_info("ID")]
    existing_plugin_file_ids = [info["ID"] for info in plugin_reader()]

    new_ids = []

    for id in existing_plugin_file_ids:
        # plugins.json would not contain new submission's ID.
        if id in plugins_json_ids:
            continue

        new_ids.append(id)

    return new_ids
