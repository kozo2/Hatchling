# Translation Files for Hatchling

This directory contains translation files for the Hatchling application's internationalization (i18n) system.

## File Structure

Translation files are in TOML format and follow the naming convention `{language_code}.toml` (e.g., `en.toml`, `fr.toml`, `es.toml`).

## Translation File Format

Each translation file must include the following sections:

### Meta Section
```toml
[meta]
language_code = "en"  # ISO 639-1 language code
language_name = "English"  # Human-readable language name
version = "1.0.0"  # Translation file version
```

### Settings Section
```toml
[settings.categories]
# Category display names
llm = "LLM Configuration"
paths = "Path Configuration"

[settings.{category}]
category_name = "Category Display Name"
category_description = "Description of this category"

[settings.{category}.{setting_name}]
name = "Setting Display Name"
description = "Description of what this setting does"
hint = "Hint about expected values or format"
```

### Commands Section
```toml
[commands.{command_group}]
command_name = "command"
command_description = "What this command does"

[commands.args]
arg_description = "Description of command argument"
```

### Messages Section
```toml
[errors]
error_key = "Error message with {placeholder} support"

[info]
info_key = "Info message with {placeholder} support"

[common]
common_term = "Translation of common term"
```

## Contributing a New Language

1. **Copy the template**: Start with `en.toml` as your template
2. **Update meta section**: Change `language_code` and `language_name` to match your target language
3. **Translate all strings**: Translate all user-facing text while preserving:
   - Placeholder syntax: `{variable_name}`
   - TOML structure and key names
   - Technical terms that shouldn't be translated (e.g., API URLs, file extensions)
4. **Test your translation**: Verify that:
   - The TOML file is valid and parses correctly
   - All placeholders are preserved
   - The translation makes sense in context
5. **Submit a pull request**: Include your translation file in a PR with:
   - Brief description of the language and region (if applicable)
   - Any notes about translation choices or cultural adaptations

## Translation Guidelines

### Do Translate
- User interface text (names, descriptions, messages)
- Error and informational messages
- Help text and command descriptions
- Common terms and status indicators

### Don't Translate
- Configuration keys and identifiers
- Technical parameter names (unless they're display names)
- File extensions and technical formats
- URLs and API endpoints
- Code examples and syntax

### Placeholder Handling
Preserve all placeholder syntax exactly as shown in the English version:
- `{setting}` - setting name
- `{value}` - setting value
- `{file}` - file path
- `{language}` - language name

### Cultural Considerations
- Use appropriate formal/informal tone for your language
- Consider regional variations if significant
- Adapt examples to be culturally relevant when appropriate
- Maintain consistency in terminology throughout

## Supported Languages

Currently supported languages:
- English (`en`) - Default/template language
- French (`fr`) - Français

## Technical Notes

- Translation files are loaded at startup and cached in memory
- Missing keys fall back to English automatically
- Language switching is supported at runtime
- The system supports nested key structures using dot notation
- All translation files must be valid TOML format

## Testing Your Translation

To test your translation:

1. Place your translation file in this directory
2. Start Hatchling and run: `settings:language:list`
3. Set your language: `settings:language:set {your_language_code}`
4. Verify that UI elements display in your language
5. Test various commands to ensure all text is properly translated

## Questions or Issues?

If you have questions about translation or encounter issues:
- Check the English template (`en.toml`) for reference
- Ensure your TOML syntax is valid
- Verify all required sections are present
- Contact the maintainers if you need clarification on specific terms

Thank you for contributing to Hatchling's internationalization! 🌍
