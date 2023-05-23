"""Add a plugin from a URL to the manifest"""
import json
import sys

from api.source import source_factory
from api.manifest import load_from_file, add_plugin, save_manifest


def main(url: str):
    from_url, update = source_factory(url)
    plugin_entry = from_url(url)
    print(json.dumps(plugin_entry, indent=4))
    manifest = load_from_file("./plugins.json")
    manifest = add_plugin(manifest, plugin_entry)
    save_manifest(manifest)


if __name__ == "__main__":
    main(sys.argv[1])
