import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add ci/src to path so _utils can be resolved
CI_SRC = Path(__file__).resolve().parent.parent / "ci" / "src"
sys.path.insert(0, str(CI_SRC))

import download_plugins as dp  # noqa: E402


def _make_plugin(pid: str, name: str = "", version: str = "1.0") -> dict:
    return {
        dp.id_name: pid,
        dp.plugin_name: name or f"Plugin-{pid}",
        dp.version: version,
        dp.url_download: f"https://github.com/author/repo/releases/download/v1.0.0/{pid}.zip",
    }


def test_env_int_returns_default_when_env_not_set(monkeypatch):
    monkeypatch.delenv("MY_VAR", raising=False)
    assert dp.env_int("MY_VAR", 42) == 42


def test_env_int_returns_default_when_env_empty(monkeypatch):
    monkeypatch.setenv("MY_VAR", "")
    assert dp.env_int("MY_VAR", 42) == 42


def test_env_int_parses_env_value(monkeypatch):
    monkeypatch.setenv("MY_VAR", "8")
    assert dp.env_int("MY_VAR", 42) == 8


def test_env_int_default_is_zero(monkeypatch):
    monkeypatch.setenv("MY_VAR", "0")
    assert dp.env_int("MY_VAR", 1) == 0


def test_manifest_filename_returns_correct_filename():
    plugin = {"Name": "My Plugin", "ID": "abc-123"}
    assert dp.manifest_filename(plugin) == "My Plugin-abc-123.json"


def test_select_new_plugins_returns_only_new_plugins():
    all_plugins = [
        {"ID": "1", "Name": "Existing"},
        {"ID": "2", "Name": "New One"},
        {"ID": "3", "Name": "Another New"},
    ]
    with (
        patch.object(dp, "get_new_plugin_submission_ids", return_value=["2", "3"]),
        patch.object(dp, "plugin_reader", return_value=all_plugins),
    ):
        plugins, meta = dp.select_new_plugins()
        assert len(plugins) == 2
        assert plugins[0]["ID"] == "2"
        assert plugins[1]["ID"] == "3"
        assert meta["mode"] == "new"
        assert meta["new_submissions"] == 2


def test_select_new_plugins_returns_empty_when_no_new_submissions():
    with (
        patch.object(dp, "get_new_plugin_submission_ids", return_value=[]),
        patch.object(dp, "plugin_reader", return_value=[]),
    ):
        plugins, meta = dp.select_new_plugins()
        assert plugins == []
        assert meta["new_submissions"] == 0


def test_select_new_plugins_skips_ids_not_in_reader():
    all_plugins = [{"ID": "1", "Name": "Only"}]
    with (
        patch.object(dp, "get_new_plugin_submission_ids", return_value=["1", "nonexistent"]),
        patch.object(dp, "plugin_reader", return_value=all_plugins),
    ):
        plugins, _ = dp.select_new_plugins()
        assert len(plugins) == 1
        assert plugins[0]["ID"] == "1"


def test_get_changed_plugin_manifest_paths_fetches_base_then_diffs(monkeypatch):
    # Fetch the base branch and diff successfully.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    diff_output = "plugins/Foo-1.json\nplugins/Bar-2.json\n"
    fetch_ok = MagicMock(returncode=0)
    diff_ok = MagicMock(returncode=0, stdout=diff_output)

    with patch.object(dp.subprocess, "run", side_effect=[fetch_ok, diff_ok]) as mock_run:
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Foo-1.json", "plugins/Bar-2.json"]
    fetch_cmd = mock_run.call_args_list[0][0][0]
    assert fetch_cmd[:2] == ["git", "fetch"]
    assert "origin" in fetch_cmd
    assert "main" in fetch_cmd
    diff_cmd = mock_run.call_args_list[1][0][0]
    assert diff_cmd[0:4] == ["git", "diff", "--diff-filter=AM", "--name-only"]
    assert any("origin/main" in arg for arg in diff_cmd)
    assert any("HEAD" in arg for arg in diff_cmd)
    assert "plugins/*.json" in diff_cmd


def test_get_changed_plugin_manifest_paths_uses_base_ref_env(monkeypatch):
    # Use the configured base branch, not a hard-coded branch.
    monkeypatch.setenv("GITHUB_BASE_REF", "release/2.0")
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)

    fetch_ok = MagicMock(returncode=0)
    diff_ok = MagicMock(returncode=0, stdout="")

    with patch.object(dp.subprocess, "run", side_effect=[fetch_ok, diff_ok]) as mock_run:
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == []
    fetch_cmd = mock_run.call_args_list[0][0][0]
    assert "release/2.0" in fetch_cmd
    diff_cmd = mock_run.call_args_list[1][0][0]
    assert any("origin/release/2.0" in arg for arg in diff_cmd)
    assert any("HEAD" in arg for arg in diff_cmd)


def test_get_changed_plugin_manifest_paths_skips_blank_lines(monkeypatch):
    # Ignore blank lines in Git output.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    diff_output = "plugins/Foo-1.json\n\n"
    fetch_ok = MagicMock(returncode=0)
    diff_ok = MagicMock(returncode=0, stdout=diff_output)

    with patch.object(dp.subprocess, "run", side_effect=[fetch_ok, diff_ok]):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Foo-1.json"]


def test_get_changed_plugin_manifest_paths_uses_base_sha_when_local(monkeypatch):
    # Use a locally available base SHA without fetching.
    monkeypatch.setenv("GITHUB_BASE_SHA", "abc1234def5678")
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)

    with (
        patch.object(dp, "_commit_exists", return_value=True),
        patch.object(dp, "_run_git_diff", return_value=["plugins/Plugin-id.json"]) as mock_diff,
    ):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Plugin-id.json"]
    mock_diff.assert_called_once_with("abc1234def5678")


def test_get_changed_plugin_manifest_paths_fetches_sha_when_not_local(monkeypatch):
    # Fetch a base SHA that is missing locally.
    monkeypatch.setenv("GITHUB_BASE_SHA", "deadbeef1234")
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)

    fetch_ok = MagicMock(returncode=0)
    with (
        patch.object(dp, "_commit_exists", return_value=False),
        patch.object(dp.subprocess, "run", return_value=fetch_ok),
        patch.object(dp, "_run_git_diff", return_value=["plugins/New-id.json"]) as mock_diff,
    ):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/New-id.json"]
    mock_diff.assert_called_once_with("deadbeef1234")


def test_get_changed_plugin_manifest_paths_falls_back_to_ref_when_sha_fetch_fails(monkeypatch):
    # Fall back to the base branch if the SHA fetch fails.
    monkeypatch.setenv("GITHUB_BASE_SHA", "deadbeef1234")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    sha_fetch_fail = MagicMock(returncode=1)
    ref_fetch_ok = MagicMock(returncode=0)

    with (
        patch.object(dp, "_commit_exists", return_value=False),
        patch.object(dp.subprocess, "run", side_effect=[sha_fetch_fail, ref_fetch_ok]),
        patch.object(dp, "_run_git_diff", return_value=["plugins/Plugin-id.json"]) as mock_diff,
    ):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Plugin-id.json"]
    mock_diff.assert_called_once_with("origin/main", use_merge_base=True)


def test_get_changed_plugin_manifest_paths_raises_when_ref_diff_fails(monkeypatch):
    # Fail when the fetched base cannot be compared with HEAD, even after unshallowing.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    ref_fetch_ok = MagicMock(returncode=0)
    unshallow_ok = MagicMock(returncode=0)
    with (
        patch.object(dp.subprocess, "run", side_effect=[ref_fetch_ok, unshallow_ok]),
        patch.object(dp, "_run_git_diff", return_value=None) as mock_diff,
        pytest.raises(RuntimeError, match="configured base SHA or ref"),
    ):
        dp._get_changed_plugin_manifest_paths()

    assert mock_diff.call_count == 2
    assert all(call.args == ("origin/main",) for call in mock_diff.call_args_list)
    assert all(call.kwargs == {"use_merge_base": True} for call in mock_diff.call_args_list)


def test_get_changed_plugin_manifest_paths_unshallows_before_retrying_ref_diff(monkeypatch):
    # Recover the merge-base when a depth-1 base fetch is insufficient.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    ref_fetch_ok = MagicMock(returncode=0)
    unshallow_ok = MagicMock(returncode=0)
    with (
        patch.object(dp.subprocess, "run", side_effect=[ref_fetch_ok, unshallow_ok]),
        patch.object(dp, "_run_git_diff", side_effect=[None, ["plugins/Foo-1.json"]]) as mock_diff,
    ):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Foo-1.json"]
    assert mock_diff.call_count == 2
    assert all(call.args == ("origin/main",) for call in mock_diff.call_args_list)
    assert all(call.kwargs == {"use_merge_base": True} for call in mock_diff.call_args_list)


def test_get_changed_plugin_manifest_paths_unshallows_when_ref_fetch_fails(monkeypatch):
    # Use the configured ref after unshallowing when its shallow fetch fails.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    ref_fetch_fail = MagicMock(returncode=1)
    unshallow_ok = MagicMock(returncode=0)
    with (
        patch.object(dp.subprocess, "run", side_effect=[ref_fetch_fail, unshallow_ok]),
        patch.object(dp, "_run_git_diff", return_value=["plugins/Foo-1.json"]) as mock_diff,
    ):
        paths = dp._get_changed_plugin_manifest_paths()

    assert paths == ["plugins/Foo-1.json"]
    mock_diff.assert_called_once_with("origin/main", use_merge_base=True)


def test_get_changed_plugin_manifest_paths_raises_when_all_strategies_fail(monkeypatch):
    # Fail changed mode instead of scanning every plugin.
    monkeypatch.setenv("GITHUB_BASE_SHA", "deadbeef1234")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    commit_check_fail = MagicMock(returncode=1, stderr="network error")
    sha_fetch_fail = MagicMock(returncode=1, stderr="network error")
    ref_fetch_fail = MagicMock(returncode=1, stderr="network error")
    unshallow_fail = MagicMock(returncode=1, stderr="network error")

    with (
        patch.object(
            dp.subprocess,
            "run",
            side_effect=[commit_check_fail, sha_fetch_fail, ref_fetch_fail, unshallow_fail],
        ),
        pytest.raises(RuntimeError, match="configured base SHA or ref"),
    ):
        dp._get_changed_plugin_manifest_paths()


def test_get_changed_plugin_manifest_paths_raises_without_configured_base(monkeypatch):
    # Do not silently assume a branch when no base was configured.
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)

    with pytest.raises(RuntimeError, match="configured base SHA or ref"):
        dp._get_changed_plugin_manifest_paths()


def test_select_changed_plugins_returns_matching_manifests():
    # Match changed paths to manifests, including existing plugins.
    changed_paths = ["plugins/Foo-1.json", "plugins/Baz-3.json"]
    all_plugins = [
        {"ID": "1", "Name": "Foo"},
        {"ID": "2", "Name": "Bar"},
        {"ID": "3", "Name": "Baz"},
    ]

    # simulate
    with (
        patch.object(dp, "_get_changed_plugin_manifest_paths", return_value=changed_paths),
        patch.object(dp, "plugin_reader", return_value=all_plugins),
    ):
        plugins, meta = dp.select_changed_plugins()

    # check
    assert [p["ID"] for p in plugins] == ["1", "3"]
    assert meta["mode"] == "changed"
    assert meta["changed_plugins"] == 2


def test_select_changed_plugins_returns_empty_when_no_matches():
    # Ignore changed paths that do not match a manifest.
    changed_paths = ["plugins/Missing-9.json"]
    all_plugins = [{"ID": "1", "Name": "Foo"}]

    # simulate
    with (
        patch.object(dp, "_get_changed_plugin_manifest_paths", return_value=changed_paths),
        patch.object(dp, "plugin_reader", return_value=all_plugins),
    ):
        plugins, meta = dp.select_changed_plugins()

    # check
    assert plugins == []
    assert meta["changed_plugins"] == 0


def test_select_changed_plugins_exits_when_diff_unavailable():
    # Propagate a failure when the diff base is unavailable.
    with (
        patch.object(dp, "_get_changed_plugin_manifest_paths", side_effect=RuntimeError("diff unavailable")),
        pytest.raises(RuntimeError, match="diff unavailable"),
    ):
        dp.select_changed_plugins()


def test_main_mode_changed(monkeypatch):
    # Route changed mode through selection and downloading.
    monkeypatch.setenv("MODE", "changed")
    monkeypatch.setattr(sys, "argv", ["download_plugins.py"])
    with (
        patch.object(dp, "download_all") as mock_download_all,
        patch.object(dp, "select_changed_plugins") as mock_select,
    ):
        mock_select.return_value = (
            [_make_plugin("changed1")],
            {"mode": "changed", "changed_plugins": 1},
        )
        dp.main()

    # check
    mock_select.assert_called_once_with()
    mock_download_all.assert_called_once_with([_make_plugin("changed1")], Path("plugin_downloads"), cache_meta_path=None)


def test_download_plugin_successfully(tmp_path, monkeypatch):
    monkeypatch.setenv("DOWNLOAD_TIMEOUT_SEC", "30")
    mock_response = MagicMock(spec=requests.Response)
    mock_response.iter_content.return_value = [b"chunk1", b"", b"chunk2"]
    mock_response.__enter__.return_value = mock_response

    with patch.object(dp, "requests") as mock_requests:
        mock_requests.get.return_value = mock_response
        dest = tmp_path / "plugin.zip"
        plugin = {dp.url_download: "https://github.com/author/repo/releases/download/v1.0.0/plugin.zip"}
        dp.download_plugin(plugin, dest)
        mock_requests.get.assert_called_once_with(
            "https://github.com/author/repo/releases/download/v1.0.0/plugin.zip",
            timeout=30,
            stream=True,
        )
    assert dest.read_bytes() == b"chunk1chunk2"


def test_download_plugin_raises_on_http_error(tmp_path):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.side_effect = requests.HTTPError("404")
    mock_response.__enter__.return_value = mock_response

    with patch.object(dp, "requests") as mock_requests:
        mock_requests.get.return_value = mock_response
        with pytest.raises(requests.HTTPError):
            dp.download_plugin(
                {dp.url_download: "https://github.com/author/repo/releases/download/v1.0.0/bad.zip"},
                tmp_path / "bad.zip",
            )


def test_download_plugin_rejects_non_github_url(tmp_path):
    with patch.object(dp, "requests") as mock_requests:
        with pytest.raises(ValueError, match="must be a GitHub release .zip URL"):
            dp.download_plugin(
                {dp.url_download: "https://example.com/plugin.zip"},
                tmp_path / "plugin.zip",
            )
        mock_requests.get.assert_not_called()


def test_download_plugin_rejects_non_zip_url(tmp_path):
    with patch.object(dp, "requests") as mock_requests:
        with pytest.raises(ValueError, match="must be a GitHub release .zip URL"):
            dp.download_plugin(
                {dp.url_download: "https://github.com/author/repo/releases/download/v1.0.0/plugin.tar.gz"},
                tmp_path / "plugin.tar.gz",
            )
        mock_requests.get.assert_not_called()


def test_sha256_file_computes_correct_hash(tmp_path):
    content = b"hello world"
    expected = hashlib.sha256(content).hexdigest()
    f = tmp_path / "data.bin"
    f.write_bytes(content)
    assert dp.sha256_file(f) == expected


def test_sha256_file_handles_empty_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    assert dp.sha256_file(f) == hashlib.sha256(b"").hexdigest()


def test_load_cache_meta_loads_existing_file(tmp_path):
    data = {"plugin.zip": {"version": "1.0"}}
    f = tmp_path / "cache.json"
    f.write_text(json.dumps(data))
    assert dp._load_cache_meta(f) == data


def test_load_cache_meta_returns_empty_dict_when_file_missing(tmp_path):
    assert dp._load_cache_meta(tmp_path / "nonexistent.json") == {}


def test_save_cache_meta_saves_to_file(tmp_path):
    data = {"plugin.zip": {"version": "1.0"}}
    f = tmp_path / "cache.json"
    dp._save_cache_meta(f, data)
    assert json.loads(f.read_text()) == data


def test_save_cache_meta_creates_parent_directories(tmp_path):
    data = {"p.zip": {"version": "2.0"}}
    f = tmp_path / "sub" / "nested" / "cache.json"
    dp._save_cache_meta(f, data)
    assert f.exists()
    assert json.loads(f.read_text()) == data


def test_expected_zip_filenames_returns_correct_filenames():
    plugins = [
        {dp.plugin_name: "Plugin A", dp.id_name: "id1"},
        {dp.plugin_name: "Plugin B", dp.id_name: "id2"},
    ]
    result = dp._expected_zip_filenames(plugins)
    assert result == {"Plugin A-id1.zip", "Plugin B-id2.zip"}


def test_expected_zip_filenames_returns_empty_set_for_empty_list():
    assert dp._expected_zip_filenames([]) == set()


def test_prune_orphans_removes_orphan_zips(tmp_path):
    (tmp_path / "keep.zip").write_text("keep")
    (tmp_path / "orphan.zip").write_text("orphan")
    (tmp_path / "other.txt").write_text("text")
    cache = {"orphan.zip": {"version": "1"}, "keep.zip": {"version": "2"}}
    dp._prune_orphans(tmp_path, {"keep.zip"}, cache)
    assert (tmp_path / "keep.zip").exists()
    assert not (tmp_path / "orphan.zip").exists()
    assert (tmp_path / "other.txt").exists()
    assert "orphan.zip" not in cache
    assert "keep.zip" in cache


def test_prune_orphans_does_nothing_when_no_orphans(tmp_path):
    (tmp_path / "a.zip").write_text("a")
    cache = {"a.zip": {"version": "1"}}
    dp._prune_orphans(tmp_path, {"a.zip"}, cache)
    assert (tmp_path / "a.zip").exists()
    assert cache == {"a.zip": {"version": "1"}}


def test_download_all_plugins_fresh(tmp_path):
    plugins = [_make_plugin("1"), _make_plugin("2")]
    with (
        patch.object(dp, "download_plugin") as mock_dl,
        patch.object(dp, "sha256_file", return_value="abc"),
    ):
        result = dp.download_all(plugins, tmp_path)
    assert len(result) == 2
    for pid, (dest, err, status) in result.items():
        assert err is None
        assert status == "fresh"
    assert mock_dl.call_count == 2


def test_download_all_skips_up_to_date_cached_plugins(tmp_path):
    plugin = _make_plugin("1", version="2.0")
    dest = tmp_path / "Plugin-1-1.zip"
    dest.write_text("existing")
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"Plugin-1-1.zip": {"version": "2.0"}}))
    with patch.object(dp, "download_plugin") as mock_dl:
        result = dp.download_all([plugin], tmp_path, cache_meta_path=cache_path)
    assert result["1"][1] is None
    assert "up-to-date (v2.0)" in result["1"][2]
    mock_dl.assert_not_called()


def test_download_all_updates_outdated_cached_plugins(tmp_path):
    plugin = _make_plugin("1", version="2.0")
    dest = tmp_path / "Plugin-1-1.zip"
    dest.write_text("old")
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"Plugin-1-1.zip": {"version": "1.0"}}))
    with patch.object(dp, "download_plugin") as mock_dl:
        result = dp.download_all([plugin], tmp_path, cache_meta_path=cache_path)
    assert result["1"][1] is None
    assert "updated (v1.0 -> v2.0)" in result["1"][2]
    mock_dl.assert_called_once()


def test_download_all_handles_download_failures(tmp_path):
    plugin = _make_plugin("fail")
    with patch.object(dp, "download_plugin", side_effect=ValueError("bad")):
        result = dp.download_all([plugin], tmp_path)
    pid, (dest, err, status) = next(iter(result.items()))
    assert err is not None
    assert "ValueError: bad" in err
    assert status is None


def test_download_all_missing_urldownload_in_task(tmp_path):
    plugin = {dp.id_name: "1", dp.plugin_name: "P1", dp.version: "1.0"}
    result = dp.download_all([plugin], tmp_path)
    _, (dest, err, status) = next(iter(result.items()))
    assert err is not None
    assert "missing UrlDownload" in err
    assert status is None


def test_download_all_http_error_with_response(tmp_path):
    plugin = _make_plugin("1")
    resp = MagicMock()
    resp.status_code = 404
    http_err = requests.HTTPError("Not Found")
    http_err.response = resp
    with patch.object(dp, "download_plugin", side_effect=http_err):
        result = dp.download_all([plugin], tmp_path)
    _, (dest, err, status) = next(iter(result.items()))
    assert err is not None
    assert "HTTP 404" in err
    assert status is None


def test_download_all_prunes_orphans(tmp_path):
    (tmp_path / "orphan.zip").write_text("orphan")
    plugin = _make_plugin("1")
    with (
        patch.object(dp, "download_plugin"),
        patch.object(dp, "sha256_file", return_value="abc"),
    ):
        dp.download_all([plugin], tmp_path)
    assert not (tmp_path / "orphan.zip").exists()


def test_download_all_persists_cache_meta(tmp_path):
    plugin = _make_plugin("1", version="3.0")
    cache_path = tmp_path / "cache.json"
    with (
        patch.object(dp, "download_plugin"),
        patch.object(dp, "sha256_file", return_value="abc"),
    ):
        dp.download_all([plugin], tmp_path / "out", cache_meta_path=cache_path)
    assert cache_path.exists()
    meta = json.loads(cache_path.read_text())
    assert "Plugin-1-1.zip" in meta
    assert meta["Plugin-1-1.zip"]["version"] == "3.0"


def test_download_all_mixed_success_and_failure(tmp_path):
    plugins = [_make_plugin("1"), _make_plugin("2")]
    side_effects = [None, ValueError("fail")]
    with (
        patch.object(dp, "download_plugin", side_effect=side_effects),
        patch.object(dp, "sha256_file", return_value="abc"),
    ):
        result = dp.download_all(plugins, tmp_path)
    assert result["1"][1] is None
    assert result["2"][1] is not None


def test_main_mode_all(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["download_plugins.py"])
    with (
        patch.object(dp, "download_all") as mock_download_all,
        patch.object(dp, "plugin_reader", return_value=[_make_plugin("1")]),
    ):
        dp.main()
    mock_download_all.assert_called_once_with([_make_plugin("1")], Path("plugin_downloads"), cache_meta_path=None)


def test_main_mode_new(monkeypatch):
    monkeypatch.setenv("MODE", "new")
    monkeypatch.setattr(sys, "argv", ["download_plugins.py"])
    with (
        patch.object(dp, "download_all") as mock_download_all,
        patch.object(dp, "select_new_plugins") as mock_select,
    ):
        mock_select.return_value = (
            [_make_plugin("new1")],
            {"mode": "new", "new_submissions": 1},
        )
        dp.main()
    mock_download_all.assert_called_once_with([_make_plugin("new1")], Path("plugin_downloads"), cache_meta_path=None)


def test_main_cli_arg_overrides_env_var(monkeypatch):
    monkeypatch.setenv("MODE", "all")
    monkeypatch.setattr(sys, "argv", ["download_plugins.py", "--mode", "new"])
    with (
        patch.object(dp, "download_all") as mock_download_all,
        patch.object(dp, "select_new_plugins") as mock_select,
    ):
        mock_select.return_value = (
            [_make_plugin("cli-new")],
            {"mode": "new", "new_submissions": 1},
        )
        dp.main()
    mock_download_all.assert_called_once_with([_make_plugin("cli-new")], Path("plugin_downloads"), cache_meta_path=None)


def test_main_exits_when_no_plugins_and_all_mode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["download_plugins.py"])
    with (
        patch.object(dp, "plugin_reader", return_value=[]),
        pytest.raises(SystemExit) as exc,
    ):
        dp.main()
    assert exc.value.code == 0
