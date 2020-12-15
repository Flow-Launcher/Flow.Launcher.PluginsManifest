Welcome to Flow Launcher's plugins repository
=============================================

This repository contains the information for community-made plugins used in [Flow](https://github.com/Flow-Launcher/Flow.Launcher) and how to make submissions.

### How to submit your plugin
Add your plugin by updating the plugins.json file with the following details via a pull request:
```
  "ID": "This is a unique GUID for your plugin",  
  "Name": "Plugin name",
  "Description": "Short description of your plugin",
  "Author": "Author of the plugin",
  "Version": "Version number",
  "Language": "The programming language the plugin is written in",
  "Website": "Your plugin's website",
  "UrlDownload":"The url to download the plugin",
  "UrlSourceCode": "Url to the source code of the plugin"
```
All the information above except for 'UrlDownload' and 'UrlSourceCode' should already exist in your own plugin's plugin.json file, simply copy them across is fine.

Once your submission is approved by the Flow Launcher Team it will be available immediately in Flow.

As usual, we will not accept plugin submissions that could potentially harm the computer or contains malicious code.

### Have a plugin enhancement request or issue?
This repository does track enhancement requests or issues for the plugins, it is up to the plugin developers to maintain their own plugin. If you would like to contribute, submit a request or issue, please visit the plugin's repository via the 'UrlSourceCode' link. 

### Usuage
From [flow](https://github.com/Flow-Launcher/Flow.Launcher/releases/latest), query ```pm``` and you should see a list of the plugins available to install:
![image](https://user-images.githubusercontent.com/26427004/102272853-89c45100-3f75-11eb-9956-2f8b129ce909.png)

