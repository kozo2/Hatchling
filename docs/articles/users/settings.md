# Settings

This article is about:

- Configuration settings available in Hatchling
- Settings categories and their purposes
- Managing settings through the chat interface

You will learn about:

- How to view, modify, and reset settings
- Available setting categories and options
- Import/export settings for backup and sharing

## Overview

Hatchling provides a comprehensive settings system to configure various aspects of the application including language model settings, file paths, tool behavior, and user interface preferences.

## Settings Categories

### LLM Configuration (`llm`)

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `api_url` | URL for the Ollama API endpoint | `http://localhost:11434/api` | `http://localhost:11434/api` |
| `model` | LLM model to use for chat interactions | `mistral-small3.1` | `mistral-small3.1` |

### Path Configuration (`paths`)

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `envs_dir` | Directory where Hatch environments are stored | Auto-detected | `/home/user/.hatch/envs` |
| `hatchling_source_dir` | Directory where Hatchling source code is located | Auto-detected | `/opt/hatchling/src` |
| `data_dir` | Directory for application data storage | Auto-detected | `/home/user/.hatchling/data` |
| `config_dir` | Directory for configuration files | Auto-detected | `/home/user/.hatchling/config` |

### Tool Calling (`tool_calling`)

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `max_iterations` | Maximum number of tool calling iterations | `10` | `15` |
| `max_working_time` | Maximum working time for tool calls (seconds) | `60` | `120` |

### User Interface (`ui`)

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `language_code` | Language code for user interface localization | `en` | `fr` |

## Managing Settings

### Viewing Settings

List all available settings:

```bash
settings:list <setting>
```

- Not giving any name will return the full list of settings.
- Whatever you give will be matched to the closest setting existing.
  - If an exact match is found, it will stop there
  - if no exact match is found, it will derive a regex pattern from your input and return the list of all settings matching this pattern

Filter settings by category or name:

```bash
settings:list llm
settings:list model
```

Get a specific setting value:

```bash
settings:get llm:model
settings:get ui:language_code
```

### Modifying Settings

Set a setting value:

```bash
settings:set llm:model mistral-large
settings:set ui:language_code fr --force-confirm
```

Using the flag `--force-confirm` will perform the changes immediately.

For **protected settings**, use the `--force-protected` flag:

```bash
settings:set llm:api_url /custom/path --force-protected
```

Reset a setting to its default value:

```bash
settings:reset llm:api_url --force-protected
settings:reset ui:language_code --force-confirm
```

### Import and Export

Export current settings to a file:

```bash
settings:export my-config.toml
settings:export backup.json
settings:export settings.yaml
```

Import settings from a file:

```bash
settings:import my-config.toml
settings:import backup.json --force-confirm --force-protected
```

## Access Levels

Settings have different access levels that control how they can be modified:

- **Normal**: Can be changed freely
- **Protected**: Require `--force` flag to modify (sensitive settings)
- **Read-only**: Cannot be modified (system-computed values)

## Command Reference

For detailed command syntax and examples, see the [Chat Commands documentation](chat_commands.md#settings-management).

### Quick Reference

| Task | Command |
|------|---------|
| List all settings | `settings:list` |
| Get setting value | `settings:get category:name` |
| Set setting value | `settings:set category:name value` |
| Reset to default | `settings:reset category:name` |
| Export settings | `settings:export filename` |
| Import settings | `settings:import filename` |

## Language Support

Hatchling supports multiple interface languages. See [Language Support](language_support.md) for details on changing the interface language and available translations.
