from pytest_schema import Optional
from pytest_schema.helpers import exact_schema

# import api
from api.languages import Languages
from tests import load_manifest

import pytest

plugin_manifest_schema = {
    "ID": str,
    "Name": str,
    "Description": str,
    "Author": str,
    "Version": str,
    "Language": str,
    "Website": str,
    "UrlDownload": str,
    "UrlSourceCode": str,
    "IcoPath": str,
    "DateAdded": str,
    "LatestReleaseDate": str,
    Optional("Tested"): bool,
}


@ pytest.mark.parametrize("plugin", load_manifest())
def test_manifest_schema(plugin):
    assert exact_schema(plugin_manifest_schema) == plugin


@ pytest.mark.parametrize("plugin", load_manifest())
def test_id_clash(plugin):
    ids = [plugin["ID"] for plugin in load_manifest()]
    assert ids.count(
        plugin["ID"]) == 1, f"ID {plugin['ID']} is not unique in {plugin}"


@ pytest.mark.parametrize("plugin", load_manifest())
def test_languages(plugin):
    assert plugin["Language"] in Languages.__members__, f"Language {plugin['Language']} is not supported in {plugin}"
