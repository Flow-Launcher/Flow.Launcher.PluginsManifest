# -*-coding: utf-8 -*-
import asyncio
import aiohttp
import re
from typing import List
from os import getenv
from sys import argv
import traceback

from tqdm.asyncio import tqdm

from _utils import *
from discord import update_hook

github_download_url_regex = re.compile(
    r"https://github\.com/(?P<author>[a-zA-Z0-9-]+)/(?P<repo>[a-zA-Z0-9\.\-\_]*)/releases/download/(?P<version>[a-zA-Z\.0-9]+)/(?P<filename>.*)\.zip"
)


async def batch_github_plugin_info(
    info: P, tags: ETagsType, github_token=None, webhook_url: str | None = None
) -> P:
    try:
        headers = {"authorization": f"token {github_token}"}
        if "github.com" not in info[url_download]:
            return info

        url_parts: List[str] = info[url_sourcecode].split("/")
        if len(url_parts) < 5:
            return info

        repo = "/".join(url_parts[3:5])
        tag: str = tags.get(info[id_name], info.get(etag, ""))

        if release_date in info.keys():
            headers["If-None-Match"] = tag

        async with aiohttp.ClientSession() as session:
            res = await session.get(
                url_release.format(repo=repo),
                headers=headers,
            )
            if res.status in (403, 304):
                return info

            latest_rel = await res.json()

            assets = latest_rel.get("assets")

            if info.get(release_date, "") != latest_rel.get("published_at"):
                info[release_date] = latest_rel.get("published_at")

            if assets:
                browser_download_url = None

                if len(assets) > 1:
                    match = github_download_url_regex.match(info[url_download])
                    if not match:
                        raise ValueError(
                            f"Download URL did not match regex: {info[url_download]!r}"
                        )
                    filename = f"{match['filename']}.zip"
                    for asset in assets:
                        if asset["browser_download_url"].endswith(filename):
                            browser_download_url = asset["browser_download_url"]

                info[url_download] = (
                    browser_download_url or assets[0]["browser_download_url"]
                )

                if webhook_url:
                    await send_notification(
                        info,
                        clean(latest_rel["tag_name"], "v"),
                        latest_rel,
                        webhook_url,
                    )
                info[version] = clean(latest_rel["tag_name"], "v")

            tags[info[id_name]] = res.headers.get(etag, "")

            return info
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error when processing plugin {info[plugin_name]}:\n{e} {tb}")
        return info


async def batch_plugin_infos(
    plugin_infos: Ps, tags: ETagsType, github_token, webhook_url: str | None = None
) -> Ps:
    return await tqdm.gather(
        *[
            batch_github_plugin_info(info, tags, github_token, webhook_url)
            for info in tqdm(plugin_infos)
        ]
    )


def remove_unused_etags(plugin_infos: PluginsType, etags: ETagsType) -> ETagsType:
    etags_updated = {}
    plugin_ids = [info.get("ID") for info in plugin_infos]

    for id, tag in etags.items():
        if id not in plugin_ids:
            print(
                f"Plugin with ID {id} has been removed. The associated ETag will be also removed now."
            )
            continue

        etags_updated[id] = tag

    return etags_updated


async def send_notification(
    info: PluginType, latest_ver, release, webhook_url: str | None = None
) -> None:
    if not webhook_url:
        return

    if version_tuple(info[version]) != version_tuple(latest_ver):
        tqdm.write(f"Update detected: {info[plugin_name]} {latest_ver}")
        try:
            await update_hook(webhook_url, info, latest_ver, release)
        except Exception as e:
            tqdm.write(str(e))


async def main():
    webhook_url = None
    if len(argv) > 1:
        webhook_url = argv[1]
    plugin_infos = plugin_reader()
    etags = etag_reader()

    plugin_infos_new = await batch_plugin_infos(
        plugin_infos, etags, getenv("GITHUB_TOKEN"), webhook_url
    )
    plugin_writer(plugin_infos_new)

    etags_new = remove_unused_etags(plugin_infos_new, etags)
    etags_writer(etags_new)


if __name__ == "__main__":
    asyncio.run(main())
