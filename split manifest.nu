let plugins = open "plugins.json"

for plugin in $plugins {
    let name = $plugin.Name
    let id = $plugin.ID

    $plugin | to json -i 4 | save $"plugins\\($name)-($id).json" -f
}
