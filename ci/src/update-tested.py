import sys
import json
import os
import zipfile
import io, asyncio, aiohttp
from datetime import datetime, UTC
from sys import argv
from os import getenv
from _utils import clean, id_name, language_list, version, plugin_reader, plugin_writer, release_date, date_added, etag_reader, PluginType, ETagsType
from updater import batch_github_plugin_info
from discord import release_hook

def update_tested():
    webhook_url = None
    if len(argv) > 1:
        webhook_url = argv[1]
    github_token = getenv("GITHUB_TOKEN")

    plugin_infos = plugin_reader()
    etags = etag_reader()

    for idx, plugin in enumerate(plugin_infos):
        if plugin["Language"] == "python" and "Tested" not in plugin.keys():
            plugin_infos[idx]["Tested"] = True
        # Add date added if field is not present
        if plugin.get(date_added) is None:
            plugin_infos[idx][date_added] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            yield batch_github_plugin_info(plugin, etags, github_token, webhook_url, True)
    
    plugin_writer(plugin_infos)

async def main():
    await asyncio.gather(*update_tested())

if __name__ == '__main__':
    asyncio.run(main())





