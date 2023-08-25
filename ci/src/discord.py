import aiohttp

from _utils import *

MAX_BODY_LEN = 1024


async def update_hook(webhook_url: str, info: dict, latest_ver: str, release: dict) -> None:
    embed = {
        "content": None,
        "embeds": [
            {
            "title": info[plugin_name],
            "description": f"Updated to v{latest_ver}!",
            "url": release['html_url'],
            "color": None,
            "fields": [
                {
                "name": "Plugin Description",
                "value": info[description]
                },
                {
                "name": "Plugin Language",
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
    release_notes = release.get('body')
    if release_notes and release_notes.strip():
        embed['embeds'][0]['fields'].append({"name": "Release Notes", "value": truncate_release_notes(release['html_url'], release.get('body', ""))})
    
    async with aiohttp.ClientSession() as session:
        session.post(webhook_url, json=embed)
    
def truncate_release_notes(url: str, release_notes: str, length: int = MAX_BODY_LEN) -> str:
    if len(release_notes) <= length:
        return release_notes
    
    TRUNCATION_MESSAGE = f"\n[Show more...]({url})"
    
    # First get the exact length index that we must break at
    # But, this might cut ``, (), [], etc in half
    rough_truncation_index = length - len(TRUNCATION_MESSAGE)

    # So, we will attempt to discard this entire line so it does not mess up any embed rendering with truncated markdown
    last_included_newline = release_notes[:rough_truncation_index].rfind('\n')
    graceful_truncation_index = last_included_newline if last_included_newline != -1 else rough_truncation_index
    
    return release_notes[:graceful_truncation_index] + TRUNCATION_MESSAGE