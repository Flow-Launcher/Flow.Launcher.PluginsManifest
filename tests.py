# -*-coding: utf-8 -*-
import json

# constants
plugin_info_file = 'plugins.json'
id_name = 'ID'

# read `plugin_info_file`
with open(plugin_info_file) as f:
    plugin_infos = json.loads(f.read())


def clean_uuid(old_id: str) -> str:
    return old_id.lower().replace('-', '')


def test_uuid_unique():
    uuids = [plugin_info[id_name] for plugin_info in plugin_infos]
    uuids = [clean_uuid(uuid) for uuid in uuids]

    assert len(uuids) == len(set(uuids))
