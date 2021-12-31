# -*-coding: utf-8 -*-
from typing import List

import requests
from tqdm import tqdm

from _utils import *

def batch_github_plugin_info(info: P, tags: ETagsType) -> P:
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
        info[version] = clean(latest_rel["tag_name"], "v")

    return info


def batch_plugin_infos(plugin_infos: Ps, tags: ETagsType) -> Ps:
    return [batch_github_plugin_info(info, tags) for info in tqdm(plugin_infos)]


if __name__ == "__main__":
    plugin_infos = plugin_reader()
    etags = etag_reader()
    plugin_infos_new = batch_plugin_infos(plugin_infos, etags)
    plugin_writer(plugin_infos_new)
    etags_writer(etags)
