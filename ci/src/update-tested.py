import asyncio
from datetime import datetime, UTC
from sys import argv
from _utils import plugin_reader, plugin_writer, date_added
from discord import release_hook


async def update_tested():
    webhook_url = None
    if len(argv) > 1:
        webhook_url = argv[1]

    plugin_infos = plugin_reader()

    for idx, plugin in enumerate(plugin_infos):
        if plugin["Language"] == "python" and "Tested" not in plugin.keys():
            plugin_infos[idx]["Tested"] = True

        # Add date added if field is not present
        if plugin.get(date_added) is None:
            plugin_infos[idx][date_added] = datetime.now(UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            if webhook_url:
                await release_hook(webhook_url, plugin)

    plugin_writer(plugin_infos)


if __name__ == "__main__":
    asyncio.run(update_tested())
