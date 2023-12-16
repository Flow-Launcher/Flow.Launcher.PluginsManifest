# -*-coding: utf-8 -*-
import json
from pathlib import Path
from typing import Dict, List, TypeVar
import re

# path
utils_path = Path(__file__).resolve()

src_dir = utils_path.parent
ci_dir = src_dir.parent
base_dir = ci_dir.parent
plugin_file = base_dir / "plugins.json"
etag_file = base_dir / "etags.json"

# constants
id_name = "ID"
language_name = "Language"
language_list = ("csharp", "executable", "fsharp", "python", "javascript", "typescript")
etag = "ETag"
version = "Version"
url_sourcecode = "UrlSourceCode"
url_download = "UrlDownload"
url_release = "https://api.github.com/repos/{repo}/releases/latest"
icon_path = "IcoPath"
author = "Author"
description = "Description"
plugin_name = "Name"
github_url = "https://github.com"
release_date = "LatestReleaseDate"
date_added = "DateAdded"

# typing
PluginType = Dict[str, str]
P = TypeVar("P", bound=PluginType)
PluginsType = List[PluginType]
Ps = TypeVar("Ps", bound=PluginsType)

ETagsType = Dict[str, str]


def plugin_reader() -> P:
    with open(plugin_file, "r", encoding="utf-8") as f:
        return json.load(f)


def etag_reader() -> ETagsType:
    with open(etag_file, "r", encoding="utf-8") as f:
        return json.load(f)


def plugin_writer(content: P):
    with open(plugin_file, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)
        
def etags_writer(content: ETagsType):
    with open(etag_file, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)


def clean(string: str, flag="-") -> str:
    return string.lower().replace(flag, "").strip()

def version_tuple(version: str) -> tuple:
    version = clean(version, "v")
    return tuple(version.split("."))

def check_url(url: str) -> bool:
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None
