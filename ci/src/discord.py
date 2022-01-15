import requests

from _utils import *

def update_hook(webhook_url: str, info: dict, latest_ver: str, release_url: str) -> None:
    embed = {
        "content": None,
        "embeds": [
            {
            "title": info[plugin_name],
            "description": f"Updated to v{latest_ver}!",
            "url": release_url,
            "color": None,
            "fields": [
                {
                "name": "Description",
                "value": info[description]
                },
                {
                "name": "Language",
                "value": info[language_name]
                }
            ],
            "author": {
                "name": info[author]
            },
            "thumbnail": {
                "url": info[icon_path]
            }
            }
        ]
        }
    if 'github.com' in info[url_sourcecode].lower():
        github_username = info[url_sourcecode].split('/')[3]
        embed['embeds'][0]['author']['name'] = github_username
        embed['embeds'][0]['author']['url'] = f"{github_url}/{github_username}"
        embed['embeds'][0]["author"]["icon_url"] = f"{github_url}/{github_username}.png?size=40"
    requests.post(webhook_url, json=embed)