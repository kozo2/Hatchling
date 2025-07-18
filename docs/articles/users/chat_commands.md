# Chat Commands

This article is about:
- Available commands during Hatchling chat sessions
- Hatch environment and package management commands
- Configuration and debugging commands

You will learn about:
- How to use basic chat commands for session management
- How to manage Hatch environments and packages
- How to configure logging and tool settings

The following commands are available during chat:

## Basic Commands

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `help` | Display help for available commands | None | `help` |
| `clear` | Clear the chat history | None | `clear` |
| `enable_tools` | Enable MCP tools | None | `enable_tools` |
| `disable_tools` | Disable MCP tools | None | `disable_tools` |
| `show_logs` | Display session logs | `[n]` - Optional number of log entries to show | `show_logs` or `show_logs 10` |
| `set_log_level` | Change log level | `<level>` - Log level (debug, info, warning, error, critical) | `set_log_level debug` |
| `set_max_tool_call_iterations` | Set maximum tool call iterations | `<n>` - Maximum iterations | `set_max_tool_call_iterations 10` |
| `set_max_working_time` | Set maximum working time in seconds | `<seconds>` - Maximum time | `set_max_working_time 60` |
| `version` | Display the current version of Hatchling | None | `version` |
| `exit` or `quit` | End the chat session | None | `exit` |

## Hatch Environment Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `hatch:env:list` | List all available Hatch environments | None | `hatch:env:list` |
| `hatch:env:create` | Create a new Hatch environment | `<name>` - Environment name <br>`--description <description>` - Environment description<br>`--python-version <version>` - Python version<br>`--no-python` - Skip Python env<br>`--no-hatch-mcp-server` - Skip MCP server<br>`--hatch_mcp_server_tag <tag>` - MCP server tag/branch | `hatch:env:create my-env --description "For biology tools"` |
| `hatch:env:remove` | Remove a Hatch environment | `<name>` - Environment name | `hatch:env:remove my-env` |
| `hatch:env:current` | Show the current Hatch environment | None | `hatch:env:current` |
| `hatch:env:use` | Set the current Hatch environment | `<name>` - Environment name | `hatch:env:use my-env` |

### Python Environment Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `hatch:env:python:init` | Initialize Python environment for a Hatch environment | `--hatch_env <env>` - Hatch environment name<br>`--python-version <version>` - Python version<br>`--force` - Force recreation<br>`--no-hatch-mcp-server` - Skip MCP server<br>`--hatch_mcp_server_tag <tag>` - MCP server tag/branch | `hatch:env:python:init --hatch_env my-env --python-version 3.10` |
| `hatch:env:python:info` | Show Python environment information | `--hatch_env <env>` - Hatch environment name<br>`--detailed` - Show detailed diagnostics | `hatch:env:python:info --hatch_env my-env --detailed` |
| `hatch:env:python:remove` | Remove Python environment | `--hatch_env <env>` - Hatch environment name<br>`--force` - Force removal | `hatch:env:python:remove --hatch_env my-env --force` |
| `hatch:env:python:shell` | Launch Python shell in environment | `--hatch_env <env>` - Hatch environment name<br>`--cmd <command>` - Command to execute | `hatch:env:python:shell --hatch_env my-env --cmd "python --version"` |
| `hatch:env:python:add-hatch-mcp` | Add hatch_mcp_server wrapper to the environment | `--hatch_env <env>` - Hatch environment name<br>`--tag <tag>` - MCP server tag/branch | `hatch:env:python:add-hatch-mcp --hatch_env my-env --tag v1.2.3` |

## Hatch Package Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `hatch:pkg:add` | Add a package to an environment | `<package_path_or_name>` - Path or name of package<br>`--env <env_name>` - Environment name<br>`--version <version>` - Package version<br>`--force-download`<br>`--refresh-registry`<br>`--auto-approve` | `hatch:pkg:add ./my-package --env my-env` |
| `hatch:pkg:remove` | Remove a package from an environment | `<package_name>` - Name of package to remove<br>`--env <env_name>` - Environment name | `hatch:pkg:remove my-package --env my-env` |
| `hatch:pkg:list` | List packages in an environment | `--env <env_name>` - Environment name | `hatch:pkg:list --env my-env` |
| `hatch:pkg:create` | Create a new package template | `<name>` - Package name<br>`--dir <dir>` - Target directory<br>`--description <description>` - Package description | `hatch:pkg:create my-package --description "My MCP package"` |
| `hatch:pkg:validate` | Validate a package | `<package_dir>` - Path to package directory | `hatch:pkg:validate ./my-package` |

## Settings Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `settings:list` | List all available settings | `[filter]` - Optional filter pattern<br>`--format <format>` - Output format (table, json, yaml) | `settings:list` or `settings:list llm --format json` |
| `settings:get` | Get the value of a specific setting | `<category:name>` - Setting in format category:name | `settings:get llm:model` |
| `settings:set` | Set the value of a specific setting | `<category:name> <value>` - Setting and new value<br>`--force-protected` - Force import of protected settings<br>`--force-confirm` - Force application of settings without asking for user consent | `settings:set llm:model mistral-small` |
| `settings:reset` | Reset a setting to its default value | `<category:name>` - Setting to reset<br>`--force-protected` - Force import of protected settings<br>`--force-confirmed` - Force application of settings without asking for user consent | `settings:reset llm:api_url` |
| `settings:export` | Export settings to a file | `<file>` - Output file path<br>`--format <format>` - Format (toml, json, yaml)<br>`--all` - Include read-only settings | `settings:export config.toml --format json --all` |
| `settings:import` | Import settings from a file | `<file>` - Input file path<br>`--force-protected` - Force import of protected settings<br>`--force-confirm` - Force application of settings without asking for user consent | `settings:import config.toml --force-protected` |
| `settings:save` | Save current settings to the configured file | `--format <format>` - Format (toml, json, yaml) | `settings:save --format toml` |

## Language Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `settings:language:list` | List available interface languages | None | `settings:language:list` |
| `settings:language:set` | Set the interface language | `<language_code>` - Language code to set | `settings:language:set fr` |