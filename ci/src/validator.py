# -*-coding: utf-8 -*-
import json
import uuid

from _utils import (check_url, clean, get_new_plugin_submission_ids, get_plugin_file_paths, get_plugin_filenames,
                    icon_path, id_name, language_list, language_name, plugin_reader, github_download_url_regex,
                    url_download, necessary_fields, optional_fields, _raise_on_duplicate_keys, plugin_name)

USE_EFFECTIVE_PLUGIN_DIR = True

plugin_infos = plugin_reader(use_effective_plugin_dir=USE_EFFECTIVE_PLUGIN_DIR)
plugin_filenames = get_plugin_filenames(use_effective_plugin_dir=USE_EFFECTIVE_PLUGIN_DIR)
plugin_file_paths = get_plugin_file_paths(use_effective_plugin_dir=USE_EFFECTIVE_PLUGIN_DIR)


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
    incorrect_ext_files = [file_path for file_path in plugin_file_paths if not file_path.endswith(".json")]

    assert len(incorrect_ext_files) == 0, f"Expected the following file to be of .json extension: {incorrect_ext_files}"


def test_file_name_construct():
    for info in plugin_infos:
        assert (
                f"{info[plugin_name]}-{info[id_name]}.json" in plugin_filenames
        ), f"Plugin {info[plugin_name]} with ID {info[id_name]} does not have the correct filename. Make sure it's name + ID, i.e. {info[plugin_name]}-{info[id_name]}.json"


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
        assert github_download_url_regex.fullmatch(info[
                                                       url_download]), f"The plugin {info[plugin_name]} with ID {info[id_name]} does not have a valid download url: {info[url_download]}"


def test_necessary_fields():
    for info in plugin_infos:
        missing_fields = [field for field in necessary_fields if field not in info]
        assert not missing_fields, f"Plugin {info[plugin_name]} with ID {info[id_name]} is missing fields: {missing_fields}"


def test_optional_fields():
    allowed_fields = set(necessary_fields) | set(optional_fields)
    for info in plugin_infos:
        unknown_fields = [field for field in info if field not in allowed_fields]
        assert not unknown_fields, f"Plugin {info[plugin_name]} with ID {info[id_name]} has unknown fields: {unknown_fields}"


def test_no_duplicate_fields():
    for file_path in plugin_file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                json.load(f, object_pairs_hook=_raise_on_duplicate_keys)
            except ValueError as e:
                assert False, f"Plugin file {file_path} has {e}"
