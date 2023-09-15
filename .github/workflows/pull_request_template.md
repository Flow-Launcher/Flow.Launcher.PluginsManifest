name: "Plugin Submission"
description: Submit your plugin to FLow Launcher's Store
title: "Plugin Submission: "
labels: ["Plugin Submission"]

body:
  - type: markdown
    attributes:
      value: Please fill out the following.

  - type: checkboxes
    attributes:
      label: Checks
      options:
        - label: >
            I tested my plugin thoroughly and fixed all bugs to the best of my ability.
        - label: >
            I understand that submitting my plugin may require additional user support.

  - type: input
    attributes:
      label: Plugin's Source code URL
      description: Please provide the source URL for your plugin.
      placeholder: "Example: https://github.com/Flow-Launcher/Flow.Launcher.Plugin.Example"
    validations:
      required: true
