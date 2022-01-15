# -*-coding: utf-8 -*-
from http.client import responses
from typing import List
from unicodedata import name
from sys import argv

import requests
from tqdm import tqdm

from _utils import *
from discord import update_hook

def batch_github_plugin_info(info: P, tags: ETagsType, webhook_url: str=None) -> P:
    if "github.com" not in info[url_download]:
        return info

    url_parts: List[str] = info[url_sourcecode].split("/")
    if len(url_parts) < 5:
        return info

    repo = "/".join(url_parts[3:5])
    tag: str = tags.get(info[id_name], info.get(etag, ""))
    res = requests.get(
        url_release.format(repo=repo),
        headers={"If-None-Match": tag},
    )
    
    if res.status_code in (403, 304):
        return info

    latest_rel = res.json()
    assets = latest_rel.get("assets")
    if assets:
        info[url_download] = assets[0]["browser_download_url"]
        send_notification(info, clean(latest_rel["tag_name"], "v"), latest_rel, webhook_url)
        info[version] = clean(latest_rel["tag_name"], "v")
        
    tags[info[id_name]] = res.headers.get(etag, "")

    return info


def batch_plugin_infos(plugin_infos: Ps, tags: ETagsType, webhook_url: str=None) -> Ps:
    return [batch_github_plugin_info(info, tags, webhook_url) for info in tqdm(plugin_infos)]


def send_notification(info: P, latest_ver, release, webhook_url: str=None) -> None:
    if version_tuple(info[version]) != version_tuple(latest_ver):
        tqdm.write(f"Update detected: {info[plugin_name]} {latest_ver}")
        try:
            update_hook(webhook_url, info, latest_ver, release)
        except Exception as e:
            tqdm.write(e)

if __name__ == "__main__":
    webhook_url = None
    if len(argv) > 1:
        webhook_url = argv[1]
    plugin_infos = plugin_reader()
    etags = etag_reader()
    plugin_infos_new = batch_plugin_infos(plugin_infos, etags, webhook_url)
    plugin_writer(plugin_infos_new)
    etags_writer(etags)
