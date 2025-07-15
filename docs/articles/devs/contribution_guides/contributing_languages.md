# Contributing New Languages

> [!Warning]
> **ALPHA FEATURE WARNING**: Multi-language support is currently in alpha stage. The setup process is heavy and requires manual testing. There are no automated tests for translations - you must run commands manually to verify text displays correctly in Hatchling.

This article is about:

- Steps to contribute a new language translation
- Translation file format and validation requirements
- Testing procedures for new translations

You will learn about:

- How to create and structure translation files
- Testing methodology for new languages
- Submission requirements for pull requests

## Prerequisites

Before contributing a new language:

- Familiarize yourself with TOML format
- Understand placeholder syntax preservation
- Have access to a Hatchling development environment
- Be prepared for manual testing of all translated strings

## Step-by-Step Guide

### 1. Copy the Template

Start with the English template as your base:

```bash
cd hatchling/config/languages/
cp en.toml {language_code}.toml
```

Example: `cp en.toml es.toml` for Spanish.

### 2. Update Meta Section

Modify the language metadata:

```toml
[meta]
language_code = "es"  # Use ISO 639-1 code
language_name = "Español"  # Native language name
version = "1.0.0"  # Keep version as 1.0.0
```

### 3. Translate Content Sections

Translate all user-facing strings while preserving:

#### Placeholder Syntax

Keep all `{variable_name}` placeholders exactly as shown:

```toml
# English
description = "URL for the {service} API endpoint"
# Spanish  
description = "URL para el punto final de la API de {service}"
```

#### Technical Terms

Do not translate technical identifiers:

```toml
# Keep these unchanged
[settings.llm]  # Don't translate section names
category_name = "llm"  # Don't translate keys
```

#### Key Structure

Preserve all TOML section and key names:

```toml
[commands.base]  # Section names stay in English
help_name = "ayuda"  # Only translate values
help_description = "Mostrar ayuda para comandos disponibles"
```

### 4. Translation Guidelines

#### Do Translate

- Setting display names and descriptions
- Command descriptions and help text
- Error and informational messages
- Common UI terms

#### Don't Translate

- TOML section names (`[settings.llm]`)
- Configuration keys (`category_name`, `api_url`)
- Technical parameters
- File extensions
- URLs and API endpoints

### 5. Cultural Considerations

- Use appropriate formal/informal tone for your language
- Consider regional variations if significant
- Maintain consistency in terminology throughout
- Adapt examples to be culturally relevant when appropriate

### 6. Testing Your Translation

⚠️ **Manual Testing Required**: There are currently no automated tests for translations.

#### Basic Testing Process

1. Place your translation file in `hatchling/config/languages/`
2. Start Hatchling development environment
3. Test language listing:

   ```bash
   settings:language:list
   ```

4. Set your language:

   ```bash
   settings:language:set {your_language_code}
   ```

5. Verify UI elements display in your language

#### Comprehensive Testing Checklist

Test these command categories to ensure all translations work:

**Settings Commands:**

- [ ] `settings:list` - Check category and setting names
- [ ] `settings:get llm:model` - Verify setting descriptions
- [ ] `settings:set ui:language_code {code}` - Test language switching

**Hatch Commands:**

- [ ] `hatch:env:list` - Check command descriptions
- [ ] `help` - Verify help text translations

**Error Messages:**

- [ ] Try invalid commands to test error message translations
- [ ] Test validation errors with invalid setting values

#### Validation Requirements

Ensure your translation file:

- [ ] Is valid TOML format (use TOML validator)
- [ ] Contains all required sections from English template
- [ ] Preserves all placeholder syntax exactly
- [ ] Maintains consistent terminology
- [ ] Displays correctly in Hatchling interface

### 7. Submission Requirements

When submitting a pull request:

#### Required Information

- Brief description of the language and region (if applicable)
- Confirmation that manual testing was completed
- Notes about any translation choices or cultural adaptations
- Screenshots showing key UI elements in the new language

#### Pull Request Template

```markdown
## New Language: {Language Name}

**Language Code:** {code}
**Region/Variant:** {if applicable}

### Testing Completed
- [ ] Language switching works correctly
- [ ] Settings commands display translated text
- [ ] Help text appears in target language
- [ ] Error messages are translated

### Translation Notes
{Any cultural adaptations or translation choices}

### Screenshots
{Screenshots showing translated interface}
```

## Common Issues

### TOML Syntax Errors

- Use TOML validators to check syntax, for example <https://www.toml-lint.com/>
- Ensure proper quote escaping
- Verify section headers are correct

### Missing Translations

- Compare your file with `en.toml` to ensure completeness
- Check that all required sections are present
- Verify no keys were accidentally omitted

### Placeholder Problems

- Double-check all `{variable}` placeholders are preserved
- Ensure no extra spaces or characters were added
- Verify placeholder names match exactly

## Support

If you encounter still encounter issues with your translation not being displayed consider submitting an issue at <https://github.com/CrackingShells/Hatchling/issues> following the template:

```markdown

### New Translation Setup [language-name]

**New language:**  
(e.g. `es`)

**File:**
- [ ] Translation file added to this issue

**Describe the Problem:**  
(Briefly describe what is not working—e.g. language not appearing, errors, missing translations, etc.)

**Steps to Reproduce:**  
1.  
2.  
3.  

**What did you expect to happen?**  
(Describe the expected behavior.)

**What actually happened?**  
(Describe the actual behavior.)

**Screenshots or Error Messages:**  
(Attach screenshots or paste error messages if available.)

**TOML Validation:**  
- [ ] I validated my file with a TOML validator

**Additional Notes:**  
(Any other relevant information.)

```

## Current Supported Languages

- English (`en`) - Default/template language
- French (`fr`) - Français

Thank you for contributing to Hatchling's internationalization! 🌍
