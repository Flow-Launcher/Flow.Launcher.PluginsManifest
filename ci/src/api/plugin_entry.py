from typing import TypedDict, TextIO
import zipfile

import requests

from .languages import Languages

PLUGIN_MANIFEST_FILENAME = "plugin.json"


class PluginEntry(TypedDict):
    ID: str
    Name: str
    Description: str
    Author: str
    Version: str
    Language: Languages
    Website: str
    UrlDownload: str
    UrlSourceCode: str
    IcoPath: str
