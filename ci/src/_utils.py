# -*-coding: utf-8 -*-
import json
from pathlib import Path
from typing import Dict, List, TypeVar

# path
utils_path = Path(__file__).resolve()

src_dir = utils_path.parent
ci_dir = src_dir.parent
base_dir = ci_dir.parent
plugin_file = base_dir / "plugins.json"

# constants
id_name = "ID"
language_name = "Language"
language_list = ("csharp", "executable", "fsharp", "python")
etag = "ETag"
version = "Version"
url_sourcecode = "UrlSourceCode"
url_download = "UrlDownload"
url_release = "https://api.github.com/repos/{repo}/releases/latest"

# typing
PluginType = Dict[str, str]
P = TypeVar("P", bound=PluginType)
PluginsType = List[PluginType]
Ps = TypeVar("Ps", bound=PluginsType)


def plugin_reader() -> P:
    with open(plugin_file, "r", encoding="utf-8") as f:
        return json.load(f)


def plugin_writer(content: P):
    with open(plugin_file, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)


def clean(string: str, flag="-") -> str:
    return string.lower().replace(flag, "").strip()
