# -*-coding: utf-8 -*-
from _utils import clean, id_name, language_list, language_name, plugin_reader, check_url, icon_path

plugin_infos = plugin_reader()


def test_uuid_unique():
    uuids = [info[id_name] for info in plugin_infos]
    uuids = [clean(uuid) for uuid in uuids]

    msg = f"The '{id_name}' is not unique."
    assert len(uuids) == len(set(uuids)), msg


def test_language_in_list():
    languages = [info[language_name] for info in plugin_infos]
    languages = [clean(language) for language in languages]

    msg = f"The '{language_name}' is not in the list of {language_list}"
    assert set(language_list) >= set(languages), msg

def test_valid_icon_url():
    for plugin in plugin_infos:
        msg = f"The URL in {icon_path} is not a valid URL."
        assert check_url(plugin[icon_path]), msg
