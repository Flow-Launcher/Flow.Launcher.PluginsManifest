# -*-coding: utf-8 -*-
import json
import uuid

from _utils import (check_url, clean, get_new_plugin_submission_ids, get_plugin_file_paths, get_plugin_filenames,
                    icon_path, id_name, language_list, language_name, plugin_reader, github_download_url_regex,
                    url_download, permitted_fields, ci_managed_fields, _raise_on_duplicate_keys)

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
    for id in get_new_plugin_submission_ids():
        try:
            uuid.UUID(id, version=4)
            outcome = True
        except ValueError:
            outcome = False

        assert outcome is True, f"The submission plugin ID {id} is not a valid v4 UUID"

def test_valid_download_url():
    for info in plugin_infos:
        assert github_download_url_regex.fullmatch(info[url_download]), f" The plugin {info['Name']}-{info['ID']} does not have a valid download url: {info[url_download]}"


def test_no_unknown_fields():
    new_ids = set(get_new_plugin_submission_ids())
    for info in plugin_infos:
        if info[id_name] not in new_ids:
            continue
        unknown = set(info.keys()) - set(permitted_fields)
        assert len(unknown) == 0, (
            f"Plugin {info['Name']}-{info[id_name]} contains unknown field(s): {unknown}. "
            f"Only these fields are permitted: {permitted_fields}"
        )


def test_no_duplicate_fields():
    for file_path in get_plugin_file_paths():
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                json.load(f, object_pairs_hook=_raise_on_duplicate_keys)
            except ValueError as e:
                assert False, f"Plugin file {file_path} has {e}"