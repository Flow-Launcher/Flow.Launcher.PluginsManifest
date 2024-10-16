import glob
import json

if __name__ == "__main__":
    plugins = sorted(glob.glob("plugins/*.json"))

    manifests = []

    for plugin in plugins:
        with open(plugin, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            manifests.append(manifest)

    with open("plugins.json", "w", encoding="utf-8") as f:
        json.dump(manifests, f, indent=4, ensure_ascii=False)
