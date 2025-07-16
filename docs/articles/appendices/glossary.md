# Glossary

This glossary defines technical terms used throughout the Hatchling documentation. You will learn about the meaning of technical terms used in Hatchling, how different components relate to each other, and standard terminology for the Hatch ecosystem.

## A
**Access Level**: Security classification for settings that determines modification permissions (normal, protected, read-only).
**API**: Application Programming Interface - a set of protocols and tools for building software applications.

## C
**CLI (Command Line Interface)**: Text-based interface for interacting with Hatchling through terminal commands.
**Container**: Isolated runtime environment created by Docker for running applications.

## D
**Docker**: Containerization platform used to run Hatchling and Ollama in isolated environments.
**Dot Notation**: A way of accessing nested dictionary values using dots to separate levels (e.g., `settings.llm.model`).

## E
**Environment Variable**: Configuration setting that can be modified to change application behavior.

## F
**Fallback**: Automatic use of English translations when a translation is missing in the selected language.

## G
**GPU (Graphics Processing Unit)**: Hardware component that can accelerate LLM inference when properly configured.

## H
**Hatch**: The official package manager for the Hatch ecosystem, integrated into Hatchling.
**Hatch Environment**: Isolated workspace containing specific collections of MCP server packages.
**Hatch Ecosystem**: The ecosystem surrounding Hatchling, including tools and protocols for package management and language models.
**Hatch Package**: A packaged MCP server that can be installed and managed through Hatch.
**Hatch Registry**: Centralized repository of available MCP server packages.
**Hatch Schemas**: JSON schemas for package metadata and validation.
**Hatch Validator**: Tool for validating packages against schema specifications.
**Hatchling**: The main CLI application that provides chat interface with LLM and MCP tool integration.

## I
**i18n**: Internationalization - the process of designing software to support multiple languages and regions.
**ISO 639-1**: International standard for language codes (e.g., "en" for English, "fr" for French).

## L
**Language Code**: A two-letter identifier for languages following ISO 639-1 standard.
**LLM (Large Language Model)**: AI model used for natural language processing and generation, run locally through Ollama.

## M
**MCP (Model Context Protocol)**: Protocol that enables language models to securely access external tools and data sources.
**MCP Server**: Software component that provides tools and capabilities accessible through the MCP protocol.
**MCP Tool**: Individual function or capability provided by an MCP server.

## O
**Ollama**: Local LLM runtime that provides API access to language models.

## P
**Placeholder**: Variable markers in translation strings (e.g., `{variable_name}`) that are replaced with actual values.
**Protected Setting**: A setting that requires explicit confirmation (--force flag) to modify due to its sensitive nature.

## R
**Registry Pattern**: A design pattern that provides a centralized location for storing and accessing objects or data.
**Runtime Switching**: The ability to change settings or language without restarting the application.

## S
**Settings Category**: A logical grouping of related settings (e.g., llm, paths, ui).
**Singleton Pattern**: A design pattern that ensures only one instance of a class exists globally.

## T
**TOML**: Tom's Obvious, Minimal Language - a configuration file format used here for translation files and settings.
**Tool Calling**: Capability that allows LLMs to invoke external functions and tools during conversations.
**Translation Key**: A unique identifier used to look up translated text (e.g., `settings.llm.model.name`).

## U
**UI**: User Interface - the means by which users interact with the application.

## V
**VRAM**: Video memory on GPU cards, important for determining which LLM models can run effectively.
