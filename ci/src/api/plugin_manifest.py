from typing import TypedDict

from api.languages import Languages
from api.plugin_entry import PluginEntry


class PluginManifest(TypedDict):
    ID: str
    ActionKeyword: str
    Name: str
    Description: str
    Author: str
    Version: str
    Language: Languages
    Website: str
    IcoPath: str
    ExecuteFileName: str


def convert_to_plugin_entry(plugin_manifest: PluginManifest) -> PluginEntry:
    """Convert a plugin manifest to a plugin entry."""
    return {
        "ID": plugin_manifest["ID"],
        "Name": plugin_manifest["Name"],
        "Description": plugin_manifest["Description"],
        "Author": plugin_manifest["Author"],
        "Version": plugin_manifest["Version"],
        "Language": plugin_manifest["Language"],
        "Website": plugin_manifest["Website"],
        "UrlDownload": "",
        "UrlSourceCode": "",
        "IcoPath": plugin_manifest["IcoPath"]
    }
