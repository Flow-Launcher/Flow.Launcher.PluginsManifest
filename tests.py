# -*-coding: utf-8 -*-
import json

# constants
plugin_info_file = 'plugins.json'
id_name = 'ID'
language_name = 'Language'
language_list = ('csharp', 'executable', 'fsharp', 'python')


# read `plugin_info_file`
with open(plugin_info_file) as f:
    plugin_infos = json.loads(f.read())


def clean(old: str) -> str:
    return old.lower().replace('-', '').strip()


def test_uuid_unique():
    uuids = [plugin_info[id_name] for plugin_info in plugin_infos]
    uuids = [clean(uuid) for uuid in uuids]

    assert len(uuids) == len(set(uuids))


def test_language_in_list():
    languages = [plugin_info[language_name] for plugin_info in plugin_infos]
    languages = [clean(language) for language in languages]

    assert set(language_list) >= set(languages)
