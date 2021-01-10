import json
from typing import Callable, Optional

# constants
plugin_info_file = 'plugin.json'
id_name = 'ID'

# read `plugin_info_file`
with open(plugin_info_file) as f:
    plugin_infos = json.loads(f.read())


def clean_uuid(old_id: str) -> str:
    new_id = old_id.lower().replace('-', '')

    return new_id


def test_uuid_unique(self):
    uuids = [plugin_info[id_name] for plugin_info in plugin_infos]
    uuids = [clean_uuid(uuid) for uuid in uuids]

    assert len(self.uuids) == len(set(self.uuids))
