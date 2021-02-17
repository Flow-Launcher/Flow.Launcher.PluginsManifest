import json
import requests

with open("plugins.json") as pluginsFile:
    plugins = json.load(pluginsFile)

for plugin in plugins:
    urlSplit: list = plugin["UrlSourceCode"].split("/")
    if(len(urlSplit) < 5):
        continue
    if("github.com" in urlSplit[2]):
        repo = "/".join(urlSplit[3:5])
        release_url = "https://api.github.com/repos/{0}/releases/latest".format(
            repo)

        release_res = requests.get(release_url,
                                   headers={"If-None-Match": plugin.get("E-tag", "")})

        # Not change
        if(release_res.status_code == 304):
            continue

        if(release_res.status_code == 403):
            break

        latest_release = release_res.json()

        version: str = latest_release['tag_name'].replace("v", "")
        if(version > plugin["Version"] and len(latest_release["assets"]) > 0):
            asset_url = latest_release["assets"][0]["browser_download_url"]
            plugin["Version"] = version
            plugin["UrlDownload"] = asset_url
            plugin["E-tag"] = release_res.headers["ETag"]

with open("plugins.json", "w") as pluginsFile:
    json.dump(plugins, pluginsFile, indent=4)
