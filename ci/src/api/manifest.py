import json
from typing import List

import requests
from api.plugin_entry import PluginEntry

MASTER_MANIFEST_FILE = "plugins.json"
CURRENT_MANIFEST_URL = "https://raw.githubusercontent.com/Flow-Launcher/Flow.Launcher.PluginsManifest/plugin_api_v2/plugins.json"

MasterManifest = List[PluginEntry]


def load_from_file(path: str) -> MasterManifest:
    """Load plugin manifest from file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_from_url(url: str) -> MasterManifest:
    """Load plugin manifest from url"""
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def get_added(manifest: MasterManifest) -> List[PluginEntry]:
    """Get plugins added to manifest"""
    current_manifest = load_from_url(CURRENT_MANIFEST_URL)
    # remove all duplicates by ID
    manifest_ids = [p["ID"] for p in manifest]
    current_manifest_ids = [p["ID"] for p in current_manifest]
    new_ids = set(manifest_ids) - set(current_manifest_ids)
    return [p for p in manifest if p["ID"] in new_ids]


def save_manifest(manifest: MasterManifest) -> None:
    """Save manifest to file"""
    with open(MASTER_MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4)


def add_plugin(manifest: MasterManifest, plugin: PluginEntry) -> MasterManifest:
    """Add plugin to manifest"""
    manifest.append(plugin)
    return manifest


def update_plugin(manifest: MasterManifest, id: str, plugin: PluginEntry) -> MasterManifest:
    """Update plugin in manifest by ID"""
    for i, p in enumerate(manifest):
        if p["ID"] == id:
            manifest[i] = plugin
            return manifest
    raise ValueError(f"Plugin with ID {id} not found")


def download_plugin(plugin: PluginEntry) -> None:
    """Download plugin from url"""
    r = requests.get(plugin["UrlDownload"])
    r.raise_for_status()
    with open(plugin["UrlDownload"], "wb") as f:
        f.write(r.content)
