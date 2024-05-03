# -*-coding: utf-8 -*-
from _utils import clean, id_name, language_list, language_name, plugin_reader, check_url, icon_path
import cerberus

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


def test_json_schema():
    schema = {
        "plugins":
        {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "ID": {
                        "type": "string",
                        "regex": "^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$",
                        "required": True
                    },
                    "Name": {
                        "type": "string",
                        "empty": False,
                        "required": True
                    },
                    "Description": {
                        "type": "string",
                        "empty": False,
                        "required": True
                    },
                    "Author": {
                        "type": "string",
                        "empty": False,
                        "required": True
                    },
                    "Version": {
                        "type": "string",
                        "empty": False,
                        "required": True
                    },
                    "Language": {
                        "type": "string",
                        "allowed": [
                            "csharp", "executable", "fsharp", "python", "javascript", "typescript"
                        ],
                        "required": True
                    },
                    "Website": {
                        "type": "string",
                        "regex": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                        "required": True
                    },
                    "UrlDownload": {
                        "type": "string",
                        "regex": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.zip",
                        "required": True
                    },
                    "UrlSourceCode": {
                        "type": "string",
                        "regex": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                        "required": True
                    },
                    "IcoPath": {
                        "type": "string",
                        "regex": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                        "required": True
                    },
                    "DateAdded": {
                        "type": "string"
                    },
                    "LatestReleaseDate": {
                        "type": "string"
                    },
                    "Tested": {
                        "type": "boolean"
                    }
                },
            }
        }
    }

    v = cerberus.Validator(schema)
    v.validate({"plugins": plugin_infos}, schema)
    print(v.errors)


if __name__ == '__main__':
    test_json_schema()