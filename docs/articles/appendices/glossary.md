# Glossary

This article is about:
- Definitions of key terms used throughout Hatchling documentation
- Technical terminology and acronyms
- Concepts specific to the Hatch ecosystem

You will learn about:
- Meaning of technical terms used in Hatchling
- How different components relate to each other
- Standard terminology for the Hatch ecosystem

## Core Terms

**CLI (Command Line Interface)**: Text-based interface for interacting with Hatchling through terminal commands.

**Docker**: Containerization platform used to run Hatchling and Ollama in isolated environments.

**GPU (Graphics Processing Unit)**: Hardware component that can accelerate LLM inference when properly configured.

**Hatch**: The official package manager for the Hatch ecosystem, integrated into Hatchling.

**Hatch Environment**: Isolated workspace containing specific collections of MCP server packages.

**Hatch Package**: A packaged MCP server that can be installed and managed through Hatch.

**Hatchling**: The main CLI application that provides chat interface with LLM and MCP tool integration.

**LLM (Large Language Model)**: AI model used for natural language processing and generation, run locally through Ollama.

**MCP (Model Context Protocol)**: Protocol that enables language models to securely access external tools and data sources.

**MCP Server**: Software component that provides tools and capabilities accessible through the MCP protocol.

**MCP Tool**: Individual function or capability provided by an MCP server.

**Ollama**: Local LLM runtime that provides API access to language models.

## Technical Terms

**Container**: Isolated runtime environment created by Docker for running applications.

**Environment Variable**: Configuration setting that can be modified to change application behavior.

**Tool Calling**: Capability that allows LLMs to invoke external functions and tools during conversations.

**VRAM**: Video memory on GPU cards, important for determining which LLM models can run effectively.

## Hatch Ecosystem

**Hatch Registry**: Centralized repository of available MCP server packages.

**Hatch Schemas**: JSON schemas for package metadata and validation.

**Hatch Validator**: Tool for validating packages against schema specifications.