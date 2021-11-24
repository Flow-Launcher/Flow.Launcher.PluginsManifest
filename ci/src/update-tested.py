import sys
import json
import os
import zipfile
import io

from _utils import clean, id_name, language_list, language_name, plugin_reader, plugin_writer

if __name__ == "__main__":
    plugin_infos = plugin_reader()

    for idx, plugin in enumerate(plugin_infos):
        if plugin["Language"] == "python" and "Tested" not in plugin.keys():
            plugin_infos[idx]["Tested"] = True

    plugin_writer(plugin_infos)







