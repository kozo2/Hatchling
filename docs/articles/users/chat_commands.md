# Chat Commands

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
| `exit` or `quit` | End the chat session | None | `exit` |

## Hatch Environment Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `hatch:env:list` | List all available Hatch environments | None | `hatch:env:list` |
| `hatch:env:create` | Create a new Hatch environment | `<name>` - Environment name <br>`--description <description>` - Environment description | `hatch:env:create my-env --description "For biology tools"` |
| `hatch:env:remove` | Remove a Hatch environment | `<name>` - Environment name | `hatch:env:remove my-env` |
| `hatch:env:current` | Show the current Hatch environment | None | `hatch:env:current` |
| `hatch:env:use` | Set the current Hatch environment | `<name>` - Environment name | `hatch:env:use my-env` |

## Hatch Package Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `hatch:pkg:add` | Add a package to an environment | `<package_path_or_name>` - Path or name of package<br>`--env <env_name>` - Environment name<br>`--version <version>` - Package version | `hatch:pkg:add ./my-package --env my-env` |
| `hatch:pkg:remove` | Remove a package from an environment | `<package_name>` - Name of package to remove<br>`--env <env_name>` - Environment name | `hatch:pkg:remove my-package --env my-env` |
| `hatch:pkg:list` | List packages in an environment | `--env <env_name>` - Environment name | `hatch:pkg:list --env my-env` |
| `hatch:create` | Create a new package template | `<name>` - Package name<br>`--dir <dir>` - Target directory<br>`--description <description>` - Package description | `hatch:create my-package --description "My MCP package"` |
| `hatch:validate` | Validate a package | `<package_dir>` - Path to package directory | `hatch:validate ./my-package` |

## Settings Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `settings:list` | List all available settings | `[filter]` - Optional filter pattern | `settings:list` or `settings:list llm` |
| `settings:get` | Get the value of a specific setting | `<category:name>` - Setting in format category:name | `settings:get llm:model` |
| `settings:set` | Set the value of a specific setting | `<category:name> <value>` - Setting and new value<br>`--force-protected` - Force import of protected settings<br>`--force-confirmed` - Force application of settings without asking for user consent<br> | `settings:set llm:model mistral-small` |
| `settings:reset` | Reset a setting to its default value | `<category:name>` - Setting to reset<br>`--force-protected` - Force import of protected settings<br>`--force-confirmed` - Force application of settings without asking for user consent<br> | `settings:reset llm:api_url` |
| `settings:export` | Export settings to a file | `<file>` - Output file path<br>`[format]` - Format (toml, json, yaml)<br>`--all` - Include read-only settings | `settings:export config.toml` |
| `settings:import` | Import settings from a file | `<file>` - Input file path<br>`--force-protected` - Force import of protected settings<br>`--force-confirmed` - Force application of settings without asking for user consent<br> | `settings:import config.toml --force` |

## Language Management

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `settings:language:list` | List available interface languages | None | `settings:language:list` |
| `settings:language:set` | Set the interface language | `<language_code>` - Language code to set | `settings:language:set fr` |