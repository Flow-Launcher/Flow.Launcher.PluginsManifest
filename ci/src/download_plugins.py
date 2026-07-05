"""Download Flow Launcher plugin ZIPs from their GitHub release URLs.

This script reads plugin manifest JSON files from the ``plugins/``
directory and downloads each plugin's ``UrlDownload`` ZIP into an output
directory.  It supports a ``--mode new`` option to download only newly
submitted plugins, and a local metadata cache to avoid re-downloading
unchanged versions.

Usage examples::

    # Download all plugins
    python ci/src/download_plugins.py

    # Download only newly submitted plugins
    python ci/src/download_plugins.py --mode new

    # Use a cache metadata file to skip unchanged downloads
    python ci/src/download_plugins.py --cache-meta cache.json

Environment variables:
    MODE                 Fallback for ``--mode``.
    OUTPUT_DIR           Fallback for ``--output-dir`` (default: plugin_downloads).
    DOWNLOAD_WORKERS     Max concurrent downloads (default: 8).
    DOWNLOAD_TIMEOUT_SEC HTTP request timeout in seconds (default: 120).
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import requests
from _utils import (get_new_plugin_submission_ids, id_name, plugin_name, plugin_reader, sha256_file, url_download,
                    version)

DOWNLOAD_WORKERS = 8


def env_int(name: str, default: int) -> int:
    """Read an integer from an environment variable.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is unset or empty.

    Returns:
        The integer value of the environment variable, or the default.
    """
    val = os.getenv(name, "")
    if not val:
        return default
    return int(val)


def manifest_filename(plugin: dict[str, str]) -> str:
    """Build the manifest filename for a plugin.

    Args:
        plugin: A plugin dictionary containing ``Name`` and ``ID`` keys.

    Returns:
        A string in the format ``{Name}-{ID}.json``.
    """
    return f"{plugin[plugin_name]}-{plugin[id_name]}.json"


def select_new_plugins() -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Select plugins whose IDs are absent from plugins.json.

    Returns:
        Tuple of ``(new_plugins, metadata_dict)``.
    """
    ids = get_new_plugin_submission_ids()
    by_id = {plugin[id_name]: plugin for plugin in plugin_reader()}
    plugins = [by_id[plugin_id] for plugin_id in ids if plugin_id in by_id]
    meta: dict[str, Any] = {"mode": "new", "new_submissions": len(plugins)}
    if not plugins:
        print("No new plugin submissions to download")
    else:
        print(f"Downloading {len(plugins)} new plugin submission(s)")
    return plugins, meta


def download_plugin(plugin: dict[str, str], dest: Path) -> None:
    """Download a plugin ZIP to destination path.

    Args:
        plugin: Plugin dictionary containing ``UrlDownload``.
        dest: Local path where the ZIP is saved.

    Raises:
        requests.HTTPError: On non-2xx HTTP responses.
    """
    url = plugin[url_download]

    timeout = env_int("DOWNLOAD_TIMEOUT_SEC", 120)
    with requests.get(url, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as zip_file:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if chunk:
                    zip_file.write(chunk)


def _load_cache_meta(path: Path) -> dict[str, Any]:
    """Load cache metadata from a JSON file.

    Args:
        path: Path to the cache metadata file.

    Returns:
        Deserialised dictionary, or an empty dict if the file does not exist.
    """
    if path.is_file():
        with open(path, "r") as cache_file:
            return json.load(cache_file)
    return {}


def _save_cache_meta(path: Path, meta: dict[str, Any]) -> None:
    """Persist cache metadata to a JSON file.

    Args:
        path: Destination path.
        meta: Metadata dictionary to serialise.
    """
    first_time = not path.is_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as cache_file:
        json.dump(meta, cache_file, indent=2)
    if first_time:
        print(f"Plugin download cache metadata created at {path}")


def _expected_zip_filenames(plugins: list[dict[str, str]]) -> set[str]:
    """Compute the set of expected ZIP filenames for the given plugins.

    Args:
        plugins: List of plugin dictionaries.

    Returns:
        Set of ``{Name}-{ID}.zip`` strings.
    """
    return {manifest_filename(plugin).replace(".json", "") + ".zip" for plugin in plugins}


def _prune_orphans(output_dir: Path, expected_filenames: set[str], cache_meta: dict[str, Any]) -> None:
    """Remove ZIP files in *output_dir* not in *expected_filenames*.
    Also removes the corresponding entries from *cache_meta*.

    This ensures we do not upload orphaned files as cache

    Args:
        output_dir: Directory containing downloaded ZIP files.
        expected_filenames: Set of filenames that should be kept.
        cache_meta: In-memory cache metadata dict (mutated in-place).
    """
    pruned = []
    for zip_path in list(output_dir.glob("*.zip")):
        if zip_path.name not in expected_filenames:
            zip_path.unlink()
            cache_meta.pop(zip_path.name, None)
            pruned.append(zip_path.name)
    if pruned:
        print(f"Pruned {len(pruned)} orphaned plugin ZIP(s):")
        for name in sorted(pruned):
            print(f"  removed {name}")


def download_all(
    plugins: list[dict[str, str]],
    output_dir: Path,
    cache_meta_path: Optional[Path] = None,
) -> dict[str, tuple[Path, Optional[str]]]:
    """Download all plugin ZIPs in parallel.

    Skips plugins whose cached version matches the manifest version.
    Prunes orphan ZIPs and updates the cache metadata.

    Args:
        plugins: List of plugin dictionaries to download.
        output_dir: Directory to write ZIP files into.
        cache_meta_path: Optional path to a JSON cache metadata file.

    Returns:
        Dict mapping plugin ID to ``(dest_path, error_or_None)``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_meta = _load_cache_meta(cache_meta_path) if cache_meta_path else {}
    workers = env_int("DOWNLOAD_WORKERS", DOWNLOAD_WORKERS)
    out: dict[str, tuple[Path, Optional[str]]] = {}

    def task(plugin: dict[str, str]) -> tuple[str, Path, Optional[str], Optional[str]]:
        pid = plugin[id_name]
        dest = output_dir / f"{manifest_filename(plugin).replace('.json', '')}.zip"
        filename = dest.name
        cached = cache_meta.get(filename)
        if cached and cached.get("version") == plugin.get(version) and dest.exists():
            return pid, dest, None, f"up-to-date (v{cached['version']})"
        try:
            if not plugin.get(url_download):
                raise ValueError("missing UrlDownload")
            download_plugin(plugin, dest)
            cache_meta[filename] = {"version": plugin.get(version, "")}
            status = f"updated (v{cached['version']} -> v{plugin.get(version, '')})" if cached else "fresh"
            return pid, dest, None, status
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, requests.HTTPError) and exc.response is not None:
                err = f"HTTP {exc.response.status_code} {plugin.get(url_download, '')} {exc}"
            return pid, dest, err, None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(task, plugin): plugin for plugin in plugins}
        for future in as_completed(futures):
            pid, dest, err, status = future.result()
            out[pid] = (dest, err, status)

    expected_filenames = _expected_zip_filenames(plugins)
    _prune_orphans(output_dir, expected_filenames, cache_meta)

    if cache_meta_path:
        _save_cache_meta(cache_meta_path, cache_meta)

    total = len(plugins)
    ok = sum(1 for result in out.values() if result[1] is None)
    failed = total - ok
    print(f"\nProcessed {ok}/{total} plugins" + (f" ({failed} failed)" if failed else ""))
    for pid, (dest, err, status) in out.items():
        if err:
            print(f"  FAIL {dest.name}: {err}")
        elif status and status.startswith("up-to-date"):
            print(f"  From cache -> {dest.name}: {status}")
        elif status and status.startswith("updated"):
            print(f"  Downloaded & cached -> {dest.name}: {status}")
        else:
            sha = sha256_file(dest)
            print(f"  Downloaded {dest.name} sha256={sha[:12]}...")
    return out


def main() -> None:
    """Parse CLI arguments and orchestrate the download workflow."""
    parser = argparse.ArgumentParser(description="Download Flow Launcher plugin zips")
    parser.add_argument(
        "--mode",
        default=None,
        choices=["new"],
        help="Selection mode (default: download all plugins, falls back to MODE env var)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: plugin_downloads, falls back to OUTPUT_DIR env var)",
    )
    parser.add_argument(
        "--cache-meta",
        default=None,
        help="Path to cache metadata JSON; skips download if cached version matches manifest",
    )
    args = parser.parse_args()

    mode = args.mode
    if mode is None:
        mode = os.getenv("MODE")
    if mode is None:
        mode = "all"

    output_dir = Path(args.output_dir or os.getenv("OUTPUT_DIR", "plugin_downloads"))

    if mode == "new":
        plugins, meta = select_new_plugins()
    else:
        plugins = plugin_reader()
        print(f"Downloading all {len(plugins)} plugins")

    if not plugins:
        print("No plugins to download")
        sys.exit(0)

    cache_meta_path = Path(args.cache_meta) if args.cache_meta else None
    download_all(plugins, output_dir, cache_meta_path=cache_meta_path)


if __name__ == "__main__":
    main()
