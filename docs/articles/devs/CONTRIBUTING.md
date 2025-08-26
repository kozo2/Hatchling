# Contributing to Hatchling

Thank you for your interest in contributing to Hatchling! This guide will help you get started with our development workflow and contribution standards.

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New features (triggers minor version bump)
- **fix**: Bug fixes (triggers patch version bump)
- **docs**: Documentation changes
- **refactor**: Code refactoring without functional changes
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **ci**: Changes to CI/CD configuration
- **perf**: Performance improvements
- **style**: Code style changes (formatting, etc.)

### Examples

```bash
# Good commit messages
feat: add support for Claude 3.5 Sonnet model
fix: resolve memory leak in streaming responses
docs: update API documentation for new providers
refactor: simplify provider registry initialization
test: add integration tests for OpenAI provider
chore: update dependencies to latest versions

# Breaking changes (use sparingly until v1.0.0)
feat!: change configuration file format
fix!: remove deprecated API methods

# With scope
feat(providers): add Anthropic Claude support
fix(mcp): resolve tool execution timeout
docs(api): update provider configuration guide
```

### Using Commitizen

For guided commit messages, use commitizen:

```bash
# Install dependencies first
npm install

# Use commitizen for guided commits
npm run commit
# or
npx cz
```

This will prompt you through creating a properly formatted commit message.

## Development Workflow

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/Hatchling.git
cd Hatchling
```

### 2. Set Up Development Environment

```bash
# Install Python dependencies
pip install -e .

# Install Node.js dependencies for semantic-release
npm install
```

### 3. Create Feature Branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 4. Make Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation as needed
- Follow PEP 8 style guidelines

### 5. Test Your Changes

```bash
# Run the test suite
python run_tests.py --regression --feature

# Run specific test categories
python run_tests.py --integration  # Requires API keys/services
python run_tests.py --file test_specific_file.py
```

### 6. Commit Changes

```bash
# Use commitizen for guided commits
npm run commit

# Or commit manually with conventional format
git commit -m "feat: add your feature description"
```

### 7. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### Title Format

Use conventional commit format for PR titles:

- `feat: add new LLM provider support`
- `fix: resolve streaming timeout issue`
- `docs: update installation guide`

### Description

Include in your PR description:

- **What**: Brief description of changes
- **Why**: Reason for the changes
- **How**: Implementation approach (if complex)
- **Testing**: How you tested the changes
- **Breaking Changes**: Any breaking changes (if applicable)

### Checklist

- [ ] Code follows existing style and patterns
- [ ] Tests added for new functionality
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventional format
- [ ] All tests pass
- [ ] No breaking changes (unless intentional and documented)

## Code Style

### Python

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Documentation

- Update relevant documentation for changes
- Use clear, concise language
- Include code examples where helpful
- Keep README.md up to date

## Testing

### Test Categories

- **Regression**: Ensure existing functionality works
- **Feature**: Test new functionality
- **Integration**: Test with external services (requires setup)

### Running Tests

```bash
# All tests
python run_tests.py --all

# Specific categories
python run_tests.py --regression
python run_tests.py --feature
python run_tests.py --integration

# Skip slow tests
python run_tests.py --skip slow

# Only run specific tags
python run_tests.py --only feature,regression
```

### Writing Tests

- Add tests for new features
- Test edge cases and error conditions
- Use descriptive test names
- Follow existing test patterns

## Release Process

Releases are fully automated using semantic-release with GitHub App integration:

1. **Commits are analyzed** for conventional commit format
2. **Version is calculated** based on commit types
3. **Changelog is generated** from commit messages
4. **Version files are updated** (pyproject.toml, CHANGELOG.md)
5. **Changes are committed** back to repository using GitHub App
6. **GitHub release is created** with release notes and tags

### Version Impact

- `feat:` commits → Minor version (0.4.0 → 0.5.0)
- `fix:` commits → Patch version (0.4.0 → 0.4.1)
- `feat!:` or `BREAKING CHANGE:` → Major version (0.4.0 → 1.0.0)
- Other types → No release

## Getting Help

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Documentation**: Check docs/articles/ for detailed guides
- **Code**: Look at existing code for patterns and examples

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub's community guidelines

Thank you for contributing to Hatchling! 🚀
