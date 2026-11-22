import json
import sys
from pathlib import Path

import pytest

CI_SRC = Path(__file__).resolve().parent.parent / "ci" / "src"
sys.path.insert(0, str(CI_SRC))

import validator as validator_module  # noqa: E402
import _utils as utils_module  # noqa: E402


def test_get_validation_paths_returns_full_mode_when_unset(tmp_path):
    assert validator_module._get_validation_paths(None, tmp_path) is None
    assert validator_module._get_validation_paths("", tmp_path) is None


def test_get_validation_paths_parses_changed_paths(tmp_path):
    plugin_path = tmp_path / "plugins" / "Example-id.json"
    readme_path = tmp_path / "README.md"
    misplaced_plugin_path = (
        tmp_path / "other" / "Misplaced-123e4567-e89b-42d3-a456-426614174000.json"
    )
    plugin_path.parent.mkdir()
    misplaced_plugin_path.parent.mkdir()
    plugin_path.write_text("{}", encoding="utf-8")
    readme_path.write_text("readme", encoding="utf-8")
    misplaced_plugin_path.write_text("{}", encoding="utf-8")

    paths = validator_module._get_validation_paths(
        json.dumps(
            [
                "plugins/Example-id.json",
                "README.md",
                "other/Misplaced-123e4567-e89b-42d3-a456-426614174000.json",
            ]
        ),
        tmp_path,
    )

    assert paths == [
        plugin_path.resolve(),
        readme_path.resolve(),
        misplaced_plugin_path.resolve(),
    ]


def test_get_validation_paths_rejects_paths_outside_repository(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        validator_module._get_validation_paths(
            json.dumps(["../outside.json"]), tmp_path
        )


def test_get_plugin_file_paths_selects_changed_files_under_plugins(
    tmp_path, monkeypatch
):
    plugin_root = tmp_path / "plugins"
    plugin_path = plugin_root / "Example-id.json"
    invalid_extension_path = plugin_root / "Example-id.txt"
    nested_plugin_path = plugin_root / "nested" / "Nested-id.json"
    nested_invalid_extension_path = plugin_root / "nested" / "Nested-id.txt"
    readme_path = tmp_path / "README.md"
    plugin_root.mkdir()
    nested_plugin_path.parent.mkdir()
    plugin_path.write_text("{}", encoding="utf-8")
    invalid_extension_path.write_text("not a manifest", encoding="utf-8")
    nested_plugin_path.write_text("{}", encoding="utf-8")
    nested_invalid_extension_path.write_text("not a manifest", encoding="utf-8")
    readme_path.write_text("readme", encoding="utf-8")
    monkeypatch.setattr(validator_module, "plugin_dir", str(plugin_root))

    paths = validator_module._get_plugin_file_paths(
        [
            plugin_path.resolve(),
            invalid_extension_path.resolve(),
            nested_plugin_path.resolve(),
            nested_invalid_extension_path.resolve(),
            readme_path.resolve(),
        ]
    )

    assert paths == [
        plugin_path.resolve(),
        invalid_extension_path.resolve(),
        nested_plugin_path.resolve(),
        nested_invalid_extension_path.resolve(),
    ]
    assert validator_module._read_plugin_infos(paths) == [{}, {}]


def test_changed_duplicate_ids_only_fail_when_changed_plugin_has_collision():
    catalogue_ids = ["unchanged-duplicate", "unchanged-duplicate", "unique"]

    assert validator_module._get_changed_duplicate_ids(["unique"], catalogue_ids) == set()
    assert validator_module._get_changed_duplicate_ids(
        ["unchanged-duplicate"], catalogue_ids
    ) == {"unchangedduplicate"}


def test_misplaced_plugin_detection_allows_only_direct_official_manifests(tmp_path):
    plugin_root = tmp_path / "plugins"
    direct_manifest = plugin_root / "Plugin-123e4567-e89b-42d3-a456-426614174000.json"
    nested_manifest = plugin_root / "nested" / direct_manifest.name
    outside_manifest = tmp_path / "other" / direct_manifest.name

    assert not validator_module._is_misplaced_plugin_file(direct_manifest, plugin_root)
    assert validator_module._is_misplaced_plugin_file(nested_manifest, plugin_root)
    assert validator_module._is_misplaced_plugin_file(outside_manifest, plugin_root)


def test_new_submission_id_helper_accepts_scoped_candidate_ids(monkeypatch):
    monkeypatch.setattr(
        utils_module,
        "get_file_plugins_json_info",
        lambda _key: [{"ID": "existing-id"}],
    )
    monkeypatch.setattr(
        utils_module,
        "plugin_reader",
        lambda: pytest.fail("scoped lookup should not read every plugin manifest"),
    )

    assert utils_module.get_new_plugin_submission_ids(
        ["existing-id", "new-id"]
    ) == ["new-id"]


def test_new_submission_id_helper_defaults_to_all_plugin_files(monkeypatch):
    monkeypatch.setattr(
        utils_module,
        "get_file_plugins_json_info",
        lambda _key: [{"ID": "existing-id"}],
    )
    monkeypatch.setattr(
        utils_module,
        "plugin_reader",
        lambda: [{"ID": "existing-id"}, {"ID": "new-id"}],
    )

    assert utils_module.get_new_plugin_submission_ids() == ["new-id"]
