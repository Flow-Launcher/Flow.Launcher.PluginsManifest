import requests

def update_hook(webhook_url: str, info: dict) -> None:
    embed = {
        "content": None,
        "embeds": [
            {
            "title": "Plugin Updated",
            "description": f"{info['Name']} plugin has been updated to v{info['Version']}!",
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