# Settings

This article is about:

- Configuration settings available in Hatchling
- Settings categories and their purposes
- Managing settings through the chat interface

## Overview

Hatchling provides a comprehensive settings system to configure various aspects of the application including language model settings, file paths, tool behavior, and user interface preferences.

## Settings Categories

The lists of settings was moved to [settings reference](./settings_reference.md)

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

The protected settings can be found in the [full list](./settings_reference.md)

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

## Persistent Settings

Hatchling automatically saves and loads user settings to persist your preferences across sessions.

### How It Works

- **On Startup**: Settings are, by default, loaded from `<path_to_hatchling_cache>/settings/hatchling_settings.toml`
- **On Exit**: Current settings are automatically saved to preserve changes
- **What's Saved**: Only modifiable settings (excludes read-only settings like computed paths)

### Configuration Directories

The cache and settings directories can be configured at install time via environment variables:

| Environment Variable | Purpose | Default |
|---------------------|---------|---------|
| `HATCHLING_CACHE_DIR` | Main cache directory | `~/.hatch` |
| `HATCHLING_SETTINGS_DIR` | Settings storage directory | `$HATCHLING_CACHE_DIR/settings` |

**Note**: These directories become read-only after first use to ensure consistency. In Docker environments, they are typically set via volume mounts.

### Import/Export vs Persistent Settings

- **Persistent settings**: Automatic save/load for session continuity
- **Import/Export**: Manual operations for backup, sharing, or profile management
- **Read-only exclusion**: By default, both persistent and export operations exclude read-only settings

Use `settings:export filename --all` to include read-only settings when creating complete configuration backups.

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
| Export all settings | `settings:export filename --all` |
| Import settings | `settings:import filename` |

## Language Support

Hatchling supports multiple interface languages. See [Language Support](language_support.md) for details on changing the interface language and available translations.
