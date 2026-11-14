# -*-coding: utf-8 -*-
import json
import os
import uuid
from collections import Counter
from pathlib import Path

from _utils import (
    _raise_on_duplicate_keys,
    base_dir,
    check_url,
    clean,
    get_new_plugin_submission_ids,
    get_plugin_file_paths,
    github_download_url_regex,
    icon_path,
    id_name,
    language_list,
    language_name,
    necessary_fields,
    optional_fields,
    plugin_dir,
    plugin_name,
    url_download,
)
from pytest import fail


def _get_validation_paths(
    serialized_paths: str | None, repository_root: Path
) -> list[Path] | None:
    if not serialized_paths:
        return None

    paths = json.loads(serialized_paths)
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        raise ValueError("Validation file paths must be a JSON array of strings")

    root = repository_root.resolve()
    resolved_paths = []
    for path in paths:
        resolved_path = (root / path).resolve()
        if not resolved_path.is_relative_to(root):
            raise ValueError(f"Validation path is outside the repository: {path}")
        if resolved_path.is_file():
            resolved_paths.append(resolved_path)

    return list(dict.fromkeys(resolved_paths))


def _get_plugin_file_paths(validation_paths: list[Path] | None) -> list[Path]:
    plugin_root = Path(plugin_dir).resolve()
    if validation_paths is None:
        return [Path(path).resolve() for path in get_plugin_file_paths()]

    return [path for path in validation_paths if plugin_root in path.parents]


def _read_plugin_infos(file_paths: list[Path]) -> list[dict[str, str]]:
    manifests = []
    for file_path in file_paths:
        if file_path.suffix.lower() != ".json":
            # Non-JSON entries are reported by test_file_type_json.
            continue
        with open(file_path, "r", encoding="utf-8") as file:
            manifests.append(json.load(file))
    return manifests


def _get_catalogue_plugin_ids() -> list[str]:
    plugin_ids = []
    for file_path in get_plugin_file_paths():
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                plugin = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(plugin, dict) and isinstance(plugin.get(id_name), str):
            plugin_ids.append(clean(plugin[id_name]))
    return plugin_ids


def _get_changed_duplicate_ids(
    changed_ids: list[str], catalogue_ids: list[str]
) -> set[str]:
    id_counts = Counter(clean(plugin_id) for plugin_id in catalogue_ids)
    return {
        clean(plugin_id)
        for plugin_id in changed_ids
        if id_counts[clean(plugin_id)] > 1
    }


def _is_misplaced_plugin_file(file_path: Path, plugin_root: Path) -> bool:
    if file_path.suffix.lower() != ".json" or "-" not in file_path.stem:
        return False

    _, uuid_part = file_path.stem.split("-", 1)
    try:
        uuid.UUID(uuid_part, version=4)
    except ValueError:
        return False

    return file_path.parent != plugin_root


validation_paths = _get_validation_paths(
    os.getenv("PLUGIN_VALIDATION_FILES"), Path(base_dir)
)
plugin_file_paths = _get_plugin_file_paths(validation_paths)
plugin_infos = _read_plugin_infos(plugin_file_paths)
changed_ids = [info[id_name] for info in plugin_infos if info.get(id_name)]


def test_uuid_unique():
    duplicates = _get_changed_duplicate_ids(changed_ids, _get_catalogue_plugin_ids())

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
    incorrect_ext_files = [
        str(file_path) for file_path in plugin_file_paths if file_path.suffix.lower() != ".json"
    ]

    assert len(incorrect_ext_files) == 0, f"Expected the following file to be of .json extension: {incorrect_ext_files}"


def test_file_name_construct():
    filenames = {file_path.name for file_path in plugin_file_paths}
    for info in plugin_infos:
        assert (
            f"{info[plugin_name]}-{info[id_name]}.json" in filenames
        ), f"Plugin {info[plugin_name]} with ID {info[id_name]} does not have the correct filename. Make sure it's name + ID, i.e. {info[plugin_name]}-{info[id_name]}.json"


def test_submitted_plugin_id_is_valid_uuid():
    new_ids = get_new_plugin_submission_ids(changed_ids)
    for id in new_ids:
        try:
            uuid.UUID(id, version=4)
            outcome = True
        except ValueError:
            outcome = False

        assert outcome is True, f"The submission plugin ID {id} is not a valid v4 UUID"


def test_valid_download_url():
    for info in plugin_infos:
        assert github_download_url_regex.fullmatch(info[url_download]), f"The plugin {info[plugin_name]} with ID {info[id_name]} does not have a valid download url: {info[url_download]}"


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
        if file_path.suffix.lower() != ".json":
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                json.load(f, object_pairs_hook=_raise_on_duplicate_keys)
            except ValueError as e:
                assert False, f"Plugin file {file_path} has {e}"


def test_plugins_in_correct_location():
    plugins_path = Path(plugin_dir)
    if validation_paths is None:
        files_to_check = []
        for root, _dirs, files in os.walk(base_dir):
            root_path = Path(root)
            # Skip the official plugins directory and anything inside it
            if root_path == plugins_path or plugins_path in root_path.parents:
                continue
            files_to_check.extend(root_path / file for file in files)
    else:
        files_to_check = validation_paths

    for file_path in files_to_check:
        if not _is_misplaced_plugin_file(file_path, plugins_path):
            continue

        fail(
            f"{str(file_path)} appears to be a plugin file and is not in the ./plugins directory. "
            "Please move it into ./plugins"
        )
