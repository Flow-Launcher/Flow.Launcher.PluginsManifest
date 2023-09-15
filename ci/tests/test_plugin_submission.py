import pytest
import requests

from tests import submitted_plugins


URL_FIELDS = ["Website", "UrlDownload", "UrlSourceCode", "IcoPath"]


def test_plugins_submitted():
    """Test that plugins have been submitted"""
    try:
        assert len(submitted_plugins()
                   ) > 0, "No new plugins have been submitted!"
    except AssertionError as e:
        pytest.fail(str(e))


@pytest.mark.parametrize("plugin", submitted_plugins())
@pytest.mark.parametrize("url", URL_FIELDS)
def test_valid_url(plugin, url):
    """Test that URLs are valid"""
    r = requests.get(plugin[url], timeout=15)
    r.raise_for_status()


@pytest.mark.skip(reason="Not implemented")
@pytest.mark.parametrize("plugin", submitted_plugins())
def test_run(plugin):
    """Test that plugin can be run"""
    pass
