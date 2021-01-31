Welcome to Flow Launcher's plugins repository
=============================================

This repository contains the information for community-made plugins used in [Flow](https://github.com/Flow-Launcher/Flow.Launcher) and how to make submissions.

### How to submit your plugin

Add your plugin by updating the plugins.json file with the following details via a pull request:

```
  "ID": "This is a unique GUID for your plugin and needs to be the same as the ID in your plugin.json",  
  "Name": "Plugin name",
  "Description": "Short description of your plugin",
  "Author": "Author of the plugin",
  "Version": "Version of your plugin and needs to be the same as the Version in your plugin.json",
  "Language": "The programming language the plugin is written in",
  "Website": "Your plugin's website",
  "UrlDownload":"The url to download the plugin",
  "UrlSourceCode": "Url to the source code of the plugin"
```

All the information above except for `UrlDownload` and `UrlSourceCode` should already exist in your own plugin's **plugin.json** file, simply copy them across is fine.

Once your submission is approved by the Flow Launcher Team it will be available immediately in Flow.

As usual, we will not accept plugin submissions that could potentially harm the computer or contains malicious code.

### Have a plugin enhancement request or issue?

This repository does not track enhancement requests or issues for the plugins, it is up to the plugin developers to maintain their own plugin. 

If you would like to contribute, submit a request or issue, please visit the plugin's repository via the 'UrlSourceCode' link or go to the plugin using `pm install`, `shift enter`/`right click` on the plugin from Flow and select 'Suggest an enhancement or submit an issue'.

### Usage

From [flow](https://github.com/Flow-Launcher/Flow.Launcher/releases/latest), query `pm install` and you should see a list of the plugins available to install:
<p align="center"><img src="https://user-images.githubusercontent.com/26427004/103451827-c08fba80-4d1c-11eb-945b-02546d31baad.png" width="800"></p>

Also use `pm update` to update or `pm uninstall` to uninstall plugins, and go to context menu on each plugin to see more options such as visit the plugin website or submit a suggestion or bug report to the developer.
