# Documentation Table of Contents

## For Users

### Tutorials

- [Installation Guide](./users/tutorials/Installation/) - Step-by-step setup instructions
  - [Docker Setup](./users/tutorials/Installation/docker-ollama-setup.md) - Docker environment setup
  - [Running Hatchling](./users/tutorials/Installation/running_hatchling.md) - Starting the application

### User Guides

- [Chat Commands](./users/chat_commands.md) - Available commands and usage
- [Settings](users/settings.md) - Configuration settings and management
- [Language Support](users/language_support.md) - Multi-language interface support

## For Developers

### Development Documentation

Documentation for maintainers and contributors working on Hatchling's codebase.

### Versioning

- [Versioning](devs/versioning.md) - Versioning strategy and documentation

### Architecture

- [Settings Architecture](devs/settings_architecture.md) - Settings system design and patterns
- [Event System Architecture](devs/event_system_architecture.md) - Event-driven communication patterns and implementation
- [i18n Support](devs/i18n_support.md) - Internationalization system architecture

### Contributing

- [**General Contribution Guidelines**](devs/how_to_contribute.md) - Standards for branches, versioning, and automation
- [Contributing Languages](devs/contribution_guides/contributing_languages.md) - How to add new language translations
- [Implementing LLM Providers](devs/contribution_guides/implementing_llm_providers.md) - Complete guide for adding new LLM providers

## Appendices

### Reference Materials

- [Glossary](./appendices/glossary.md) - Key terms and definitions

## Resources

### Images and Diagrams

- [Logo Resources](../resources/images/Logo/) - Hatchling branding materials
- [Setup Screenshots](../resources/images/docker-setup/) - Visual guides for Docker setup
- [CLI Screenshots](../resources/images/running-hatchling/) - Application interface examples

### Diagrams

- [Architecture Diagrams](../resources/diagrams/export/) - System architecture documentation
  - [LLM Provider Architecture](../resources/diagrams/export//llm_provider_architecture.svg) - Provider system class diagram
  - [Provider Interaction Sequence](../resources/diagrams/export/provider_interaction_sequence.svg) - Provider workflow sequence diagram
  - [Translation Flow](../resources/diagrams/export/i18n_translation_flow.svg) - How the translation files are leveraged to display runtime documentation in different languages
  - [Settings](../resources/diagrams/export/settings_components_architecture.svg) - How the settings components are related to each other
  - [Tool Chaining Sequence](../resources/diagrams/export/tool_chaining_events_sequence_v2.svg) - How tool chaining plays out

### Diagram Sources

- [PlantUML Sources](../resources/diagrams/puml/) - Editable source files for architecture and workflow diagrams
