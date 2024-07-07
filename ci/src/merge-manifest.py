import glob
import json

if __name__ == "__main__":
    plugins = glob.glob("plugins/*.json")

    manifests = []

    for plugin in plugins:
        with open(plugin, "r") as f:
            manifest = json.load(f)
            manifests.append(manifest)

    with open("plugins.json", "w") as f:
        json.dump(manifests, f, indent=4)
