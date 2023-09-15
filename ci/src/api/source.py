from typing import Callable, Tuple
from api.plugin_entry import PluginEntry
from api.sources import github

FromUrl = Callable[[str], PluginEntry]
Update = Callable[[PluginEntry], PluginEntry]
SourceInterface = Tuple[FromUrl, Update]

sources = {
    github.BASE_URL: (github.from_url, github.update)
}


def source_factory(url: str) -> SourceInterface:
    """Get source from url"""
    for source_url, source in sources.items():
        if source_url in url:
            return source
    raise ValueError(f"Invalid source URL: {url}")
