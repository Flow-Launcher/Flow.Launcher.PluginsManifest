# Welcome to Flow Launcher's plugins repository

This repository contains the information for community-made plugins used in [Flow](https://github.com/Flow-Launcher/Flow.Launcher) and how to make new submissions.

[![AutoUpdate](https://github.com/Flow-Launcher/Flow.Launcher.PluginsManifest/actions/workflows/updater.yaml/badge.svg?branch=plugin_api_v2)](https://github.com/Flow-Launcher/Flow.Launcher.PluginsManifest/actions/workflows/updater.yaml)

## List of Flow plugins

Looking for a list of currently available plugins in Flow? Visit [here](https://flow-launcher.github.io/docs/#/plugins)

## How to submit your plugin

Add your plugin by updating the plugins.json file with the following details via a pull request:

```json
{
  "ID": "This is a unique GUID for your plugin and needs to be the same as the ID in your plugin.json",  
  "Name": "Plugin name",
  "Description": "Short description of your plugin",
  "Author": "Author of the plugin",
  "Version": "Version of your plugin and needs to be the same as the Version in your plugin.json",
  "Language": "The programming language the plugin is written in",
  "Website": "Your plugin's website",
  "UrlDownload":"The url to download the plugin",
  "UrlSourceCode": "Url to the source code of the plugin",
  "IcoPath": "Url to the icon of the plugin"
}
```

All the information above except for `UrlDownload`, `UrlSourceCode` and `IcoPath` should already exist in your own plugin's **plugin.json** file, simply copying them across is fine. For `IcoPath`, you will need to provide the direct URL to your plugin's icon image (usually via your repo). It is recommended to use a CDN provider for international access. [jsdelivr.com](https://www.jsdelivr.com/) for example, provides a simple API and supports github repositories. see other listed plugins in [plugins.json](https://github.com/Flow-Launcher/Flow.Launcher.PluginsManifest/blob/plugin_api_v2/plugins.json) for examples.

Once your submission is approved by the Flow Launcher Team it will be available immediately in Flow.

Our *CI* will automatically check for new updates from plugins every three hours and update to the newer version if they are stored in the Github Release.
Therefore, if you are using Github to release and update your plugin, there will be no need to manually create a pull request for every update.
If this is the first time you are publishing your plugin to Flow, then you will need to create a pull request for it to be reviewed.

As usual, we will not accept plugin submissions that could potentially harm the computer or contains malicious code.

## Plugin Store

Once your plugin submission has been merged, it will soon be available in [flow's](https://github.com/Flow-Launcher/Flow.Launcher/releases/latest) Plugin Store. Users will be able to install your plugin via the store or type `pm install <your-plugin-name>`:
<p align="center"><img src="https://user-images.githubusercontent.com/6903107/207155616-d559f0d2-ee95-4072-a7bc-3ffcc2faec27.png" width="800"></p>

## Have a plugin enhancement request or issue?

This repository does not track enhancement requests or issues for plugins, it is up to the plugin developers to maintain their own plugin.

If you would like to contribute, submit a request or issue, please visit the plugin's repository via the 'UrlSourceCode' link or from `pm install`, `shift enter`/`right click` on the plugin to go to the context menu and select 'Suggest an enhancement or submit an issue'.
