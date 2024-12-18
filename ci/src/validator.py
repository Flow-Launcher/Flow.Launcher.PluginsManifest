# -*-coding: utf-8 -*-
import uuid

from _utils import (check_url, clean, get_file_plugins_json_info, get_plugin_file_paths, get_plugin_filenames,
                    icon_path, id_name, language_list, language_name, plugin_reader)

plugin_infos = plugin_reader()


def test_uuid_unique():
    uuids = [clean(info[id_name]) for info in plugin_infos]
    duplicates = set([id for id in uuids if uuids.count(id) > 1])

    msg = f"{id_name} not unique: {duplicates}"
    assert len(duplicates) == 0, msg


def test_language_in_list():
    languages = [info[language_name] for info in plugin_infos]
    languages = [clean(language) for language in languages]

    msg = f"The '{language_name}' is not in the list of {language_list}"
    assert set(language_list) >= set(languages), msg

def test_valid_icon_url():
    for plugin in plugin_infos:
        msg = f"The URL in {icon_path} is not a valid URL."
        assert check_url(plugin[icon_path]), msg

def test_file_type_json():
    incorrect_ext_files = [file_path for file_path in get_plugin_file_paths() if not file_path.endswith(".json")]

    assert len(incorrect_ext_files) == 0, f"Expected the following file to be of .json extension: {incorrect_ext_files}"

def test_file_name_construct():
    filenames = get_plugin_filenames()
    for info in plugin_infos:
        assert (
            f"{info['Name']}-{info['ID']}.json" in filenames
        ), f"Plugin {info['Name']} with ID {info['ID']} does not have the correct filename. Make sure it's name + ID, i.e. {info['Name']}-{info['ID']}.json"

def test_submitted_plugin_id_is_valid_uuid():
    plugins_json_ids = [item["ID"] for item in get_file_plugins_json_info("ID")]
    existing_plugin_file_ids = [info["ID"] for info in plugin_infos]

    for id in existing_plugin_file_ids:
        # plugins.json would not contain new submission's ID.
        if id in plugins_json_ids:
            continue

        try:
            uuid.UUID(id, version=4)
            outcome = True
        except ValueError:
            outcome = False

        assert outcome is True, f"The submission plugin ID {id} is not a valid v4 UUID"
