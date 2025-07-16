# Hatchling

![Hatchling Logo](./docs/resources/images/Logo/hatchling_wide_dark_bg_transparent.png)

Hatchling is an interactive CLI-based chat application that integrates local Large Language Models (LLMs) through [Ollama](https://ollama.ai/) with the [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) for tool calling capabilities. It is meant to be the frontend for using all MCP servers in Hatch!

## Project Update Summary

**June 27,2025**:

- Early June we held an internal hackathon centered on using *Hatchling*, developing and using MCP servers for analysis of biological data, building models and running the simulations. This helped identified some practical limits which we started solving.
- This time, we are releasing only the UI part of the update to give:
  - Syntax highlighting in the terminal for *Hatch!* and *Hatchling* commands
  - Prompts history with arrows up and down
  - Commands auto-completion
- After that we worked on the internal of the Hatch ecosystem to facilitate future updates. Deeply necessary but kinda boring, let's be honest!
- The general [roadmap](#roadmap) below is still up to date.

**May 27, 2025**: First release of the Hatch package manager ecosystem! 🎉

- The Hatch package manager is now **fully integrated into Hatchling** with built-in commands
- The package architecture for dynamic loading and switching of MCP servers is now complete
- [Related repositories](#related-repositories) established to support the pipeline.

## Versioning System

Hatchling uses an automated versioning system that handles version increments based on branch merges and GitHub Actions workflows.

### Version Format

The project uses semantic versioning with the following format:
- **Main branch**: `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- **Dev branch**: `vMAJOR.MINOR.PATCH-dev` (e.g., `v1.2.3-dev`)
- **Feature branches**: `vMAJOR.MINOR.PATCH-dev.bN` (e.g., `v1.3.0-dev.b1`)
- **Fix branches**: `vMAJOR.MINOR.PATCH-dev.bN` (e.g., `v1.2.1-dev.b1`)

### Automatic Version Management

#### Branch Types and Version Increments

1. **Feature Branches (`feat/`)**:
   - Increment the **minor** version
   - Example: `v1.2.0-dev` → `feat/new-feature` creates `v1.3.0-dev.b1`
   - Each push increments the build number: `v1.3.0-dev.b1` → `v1.3.0-dev.b2`

2. **Fix Branches (`fix/`)**:
   - Increment the **patch** version
   - Example: `v1.2.0-dev` → `fix/bug-fix` creates `v1.2.1-dev.b1`
   - Each push increments the build number: `v1.2.1-dev.b1` → `v1.2.1-dev.b2`

3. **Dev Branch**:
   - Receives merged versions from feature/fix branches
   - Creates pre-releases with `-dev` suffix
   - Example: After merging `feat/new-feature`, `dev` becomes `v1.3.0-dev`

4. **Main Branch**:
   - Receives stable versions for production releases
   - Creates clean releases without suffixes
   - Example: After merging from `dev`, `main` becomes `v1.3.0`

#### GitHub Actions Workflows

The versioning system is automated through GitHub Actions:

- **Release Workflow** (`.github/workflows/release.yml`): 
  - Triggers on pushes to `main` branch
  - Creates official releases and tags
  - Builds and publishes packages

- **Pre-Release Workflow** (`.github/workflows/prerelease.yml`):
  - Triggers on pushes to `dev` branch
  - Creates pre-releases with `-dev` suffix
  - Useful for testing before production

- **Feature/Fix Workflow** (`.github/workflows/feature-fix.yml`):
  - Triggers on pushes to `feat/` and `fix/` branches
  - Increments build numbers automatically
  - Creates lightweight tags for tracking

- **Tag Cleanup Workflow** (`.github/workflows/tag-cleanup.yml`):
  - Runs weekly to clean up old tags
  - Removes build tags older than 7 days
  - Removes dev tags older than 30 days

### Manual Version Management

You can also manage versions manually using the version management script:

```bash
# Get current version
python scripts/version_manager.py --get

# Update version for a specific branch
python scripts/version_manager.py --update-for-branch feat/my-feature

# Increment version components
python scripts/version_manager.py --increment minor
python scripts/version_manager.py --increment patch
python scripts/version_manager.py --increment build

# Prepare version for building (converts to setuptools format)
python scripts/prepare_version.py
```

### VERSION File Format

The `VERSION` file stores version information in a structured format:

```
MAJOR=1
MINOR=0
PATCH=3
PRERELEASE=dev
BUILD=b1
BRANCH=feat/example
```

This format allows for clear tracking of all version components and branch information.

For detailed information about the versioning system, see [doc/versioning.md](./doc/versioning.md).

## Features


- Interactive CLI-based chat interface
- Integration with Ollama API for local LLM support
- Ollama tool calling to MCP tools
- Tool execution wrapping to babysit LLMs into doing longer tool calling chains to do more work
- Appropriate citation of the source software wrapped in the MCP server whenever the LLM uses them

## Roadmap

- Support for vanilla MCP servers syntax (no wrapping in `HatchMCP`)
- Launching **Hatch! Biology** for hosting MCP servers providing access to well-established software and methods such as BLAST, UniProt (and other database) queries, PubMed articles, and such... All with citations!
- Customize LLMs system prompts, reference past messages, be in control of context history
- GUI for the chat and all management of the MCP servers
- User-defined tool chains

## Installation & Running

1. [Docker setup instructions](./docs/articles/users/tutorials/Installation/docker-setup.md)

2. [Running Hatchling](./docs/articles/users/tutorials/Installation/running_hatchling.md)

3. [In-chat commands](./docs/articles/users/chat_commands.md)


## Extending with your MCP Servers as *Hatch!* Packages

You can extend Hatchling with custom MCP tools by creating Hatch packages:

1. With Hatchling running, use

    ```txt
    hatch:create .local/<name> --description "Your description here"
    ```

    to populate a folder at directory `HATCH_LOCAL_PACKAGE_DIR/<name>`, where `HATCH_LOCAL_PACKAGE_DIR` is the environment variable   [you can set](./docs/articles/users/tutorials/Installation/running_hatchling.md#configuration) in the `.env` file.

2. The `server.py` is the entry point of your MCP server.

3. Add a new tool:

    ```python
    @hatch_mcp.tool()
    def my_custom_tool(param1: str, param2: int) -> str:
        """Description of what your tool does.
        
        Args:
            param1 (str): First parameter description.
            param2 (int): Second parameter description.
            
        Returns:
            str: Description of the return value.
        """
        hatch_mcp.logger.info(f"Custom tool called with {param1} and {param2}")
        return f"Processed {param1} with value {param2}"

    if __name__ == "__main__":
        hatch_mcp.run()
    ```

    Generally, you can define new tools using the `@hatch_mcp.tool()` decorator above a new function you added in the file. This follows the patterns from the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

4. You can add your package to your current *Hatch!* environment with:

   ```bash
   hatch:pkg:add .local/package
   ```

5. Run `enable_tools` command to have access to your *Hatch!* package in *Hatchling*

## Related Repositories

Hatchling is part of the larger Hatch ecosystem which includes:

- **[Hatch](https://github.com/CrackingShells/Hatch)**: The official package manager for the Hatch ecosystem, now fully integrated into Hatchling with built-in commands for MCP server management
  - Provides environment management for MCP server collections
  - Handles package installation from both local and registry sources
  - Template function to jump start new package development
- **[Hatch-Schemas](https://github.com/CrackingShells/Hatch-Schemas)**: Contains the JSON schemas for package metadata and validation
  - Includes schemas for both individual packages and the central registry
  - Provides versioned access to schemas via GitHub releases
  - Offers helper utilities for schema caching and updates
- **[Hatch-Validator](https://github.com/CrackingShells/Hatch-Validator)**: Validates packages against the schemas
  - Performs package validation against schema specifications
  - Resolves and validates package dependencies
  - Automatically fetches and manages schema versions
- **[Hatch-Registry](https://github.com/CrackingShells/Hatch-Registry)**: Package registry for Hatch packages
  - Maintains a centralized repository of available MCP server packages
  - Supports package versioning and dependency information
  - Provides search and discovery functionality
  - Ensures package integrity through metadata verification

These repositories work together to provide a comprehensive framework for creating, managing, and using MCP tools in Hatchling.
