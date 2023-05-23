import json
from typing import Any, List, Union
from github import Github
from github.Repository import Repository

# from .source import Source
from api.plugin_entry import PLUGIN_MANIFEST_FILENAME, PluginEntry
from api.manifest import MasterManifest, add_plugin

BASE_URL = "https://github.com"


gh = Github()


def _url_to_repo(url: str) -> str:
    """Convert URL to repo user/name"""
    return "/".join(url.split("/")[3:5])


def _find_plugin_manifest(repo: Repository) -> bytes:
    """Find plugin manifest in repo"""
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)  # type: ignore
        if file_content.type == "dir":
            contents.extend(repo.get_contents(  # type: ignore
                file_content.path))  # type: ignore
        elif file_content.name == PLUGIN_MANIFEST_FILENAME:
            return file_content.decoded_content
    raise FileNotFoundError(f"Plugin manifest not found in {repo.full_name}")


def _latest_release_download(repo: Repository):
    """Find latest release in repo"""
    return repo.get_latest_release().assets[0].browser_download_url


def from_url(url: str) -> PluginEntry:
    """Get plugin manifest from url"""
    repo = gh.get_repo(_url_to_repo(url))
    manifest = json.loads(_find_plugin_manifest(repo))
    return {
        "ID": manifest["ID"],
        "Name": manifest["Name"],
        "Description": manifest["Description"],
        "Author": manifest["Author"],
        "Version": manifest["Version"],
        "Language": manifest["Language"],
        "Website": manifest["Website"],
        "UrlDownload": _latest_release_download(repo),
        "UrlSourceCode": url,
        "IcoPath": manifest["IcoPath"]
    }


def update(plugin_entry: PluginEntry) -> PluginEntry:
    """Update plugin from source"""
    old_version = plugin_entry["Version"]
    new_version = from_url(plugin_entry["UrlSourceCode"])["Version"]
    if old_version == new_version:
        return plugin_entry
    else:
        return from_url(plugin_entry["UrlSourceCode"])
