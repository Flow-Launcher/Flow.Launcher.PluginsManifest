import requests

def update_hook(webhook_url: str, info: dict, latest_ver: str) -> None:
    embed = {
        "content": None,
        "embeds": [
            {
            "title": "Plugin Updated",
            "description": f"{info['Name']} plugin has been updated to v{latest_ver}!",
            "url": info['Website'],
            "color": None,
            "fields": [
                {
                "name": "Author",
                "value": info['Author'],
                "inline": True
                },
                {
                "name": "Language",
                "value": info['Language'],
                "inline": True
                },
                {
                "name": "Download",
                "value": info['UrlDownload']
                }
            ],
            "thumbnail": {
                "url": info['IcoPath']
            }
            }
        ]
        }
    requests.post(webhook_url, json=embed)