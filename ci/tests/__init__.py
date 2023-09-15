from api.manifest import load_from_file, get_added


def load_manifest():
    return load_from_file("./plugins.json")


def submitted_plugins():
    return get_added(load_manifest())
