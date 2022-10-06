import sys
import json
import os
import zipfile
import io
from datetime import datetime

from _utils import clean, id_name, language_list, language_name, plugin_reader, plugin_writer, release_date, date_added

if __name__ == "__main__":
    plugin_infos = plugin_reader()

    for idx, plugin in enumerate(plugin_infos):
        if plugin["Language"] == "python" and "Tested" not in plugin.keys():
            plugin_infos[idx]["Tested"] = True
        # Add date added if field is not present
        if plugin.get(date_added) is None:
            plugin_infos[idx][date_added] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    plugin_writer(plugin_infos)







