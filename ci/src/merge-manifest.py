import sys
from _utils import get_new_plugin_submission_ids, plugin_reader, save_plugins_json_file

def get_all_plugins() -> list[dict[str]]:
    return plugin_reader()

def get_new_plugins() -> list[dict[str]]:
    ids = get_new_plugin_submission_ids()
    plugins_from_plugins_dir = plugin_reader()

    new_plugins = []

    for id in ids:
        for plugin in plugins_from_plugins_dir:
            if plugin["ID"] == id:
                new_plugins.append(plugin)
                break

    return new_plugins


if __name__ == "__main__":

    if len(sys.argv) > 1 and str(sys.argv[1]) == "new-only":
        save_plugins_json_file(get_new_plugins())
    else:
        save_plugins_json_file(get_all_plugins())
