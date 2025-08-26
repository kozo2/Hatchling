# Automated Versioning with Semantic Release

Hatchling uses [semantic-release](https://semantic-release.gitbook.io/) for fully automated versioning and releases based on [Conventional Commits](https://www.conventionalcommits.org/).

## How It Works

1. **Commit Analysis**: Analyzes commit messages to determine release type
2. **Version Calculation**: Automatically calculates next version
3. **Changelog Generation**: Creates release notes from commits
4. **GitHub Release**: Publishes release with generated notes
5. **Version Update**: Updates pyproject.toml with new version

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```txt
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Examples

```bash
feat: add new LLM provider support
fix: resolve memory leak in streaming
docs: update API documentation
refactor: simplify provider registry
test: add integration tests for OpenAI
chore: update dependencies

# Breaking changes (avoid until ready for v1.0.0)
feat!: change configuration format
```

### Version Impact

- `feat:` → Minor version (0.4.0 → 0.5.0)
- `fix:` → Patch version (0.4.0 → 0.4.1)
- `feat!:` or `BREAKING CHANGE:` → Major version (0.4.0 → 1.0.0)
- `docs:`, `test:`, `chore:` → No release

## Using Commitizen

For guided commit messages:

```bash
npm run commit
# or
npx cz
```

## Branches

- **main**: Production releases (0.4.0, 0.5.0, etc.)
- **dev**: Pre-releases (0.5.0-dev.1, 0.5.0-dev.2, etc.)

## Manual Testing

Test semantic-release configuration:

```bash
npx semantic-release --dry-run
```

## GitHub Actions Workflows

### 1. Semantic Release Workflow (`semantic-release.yml`)

**Triggered by**: Pushes to `main` and `dev` branches

**Actions**:

- Runs tests to ensure code quality
- Analyzes commits since last release
- Calculates next version based on commit types
- Generates changelog from commit messages
- Creates GitHub release with generated notes
- Updates pyproject.toml with new version
- Commits version changes back to repository

### 2. Commit Lint Workflow (`commitlint.yml`)

**Triggered by**: Pull requests to `main` and `dev` branches

**Actions**:

- Validates commit messages follow Conventional Commits format
- Ensures proper commit types and formatting
- Provides feedback on commit message issues

## Configuration Files

### .releaserc.json

Contains semantic-release configuration:

- Branch configuration for main and dev
- Plugin configuration for commit analysis
- Changelog and release note generation
- GitHub integration settings

### .commitlintrc.json

Contains commit message linting rules:

- Enforces Conventional Commits format
- Validates commit types and structure
- Ensures consistent commit message style

### package.json

Contains Node.js dependencies for semantic-release:

- semantic-release and plugins
- commitizen for guided commits
- commitlint for validation

## Best Practices

1. **Use Conventional Commits** for all commit messages
2. **Use commitizen** (`npm run commit`) for guided commits
3. **Test changes** before merging to main or dev
4. **Avoid breaking changes** until ready for v1.0.0
5. **Use descriptive commit messages** that explain the change
6. **Squash merge** PRs to maintain clean commit history

## Troubleshooting

### Commit Message Issues

If commits don't follow the conventional format:

```bash
# Use commitizen for guided commits
npm run commit

# Or manually format commits
git commit -m "feat: add new feature description"
```

### Testing Configuration

Validate semantic-release setup:

```bash
# Test configuration without making changes
npx semantic-release --dry-run

# Validate commit messages
echo "feat: test commit" | npx commitlint
```

### Release Issues

If releases fail:

1. Check commit message format
2. Ensure branch is configured in .releaserc.json
3. Verify GitHub token permissions
4. Check workflow logs in GitHub Actions

### Manual Release

In emergency situations, create manual release:

```bash
# Create and push a tag manually
git tag v0.4.1
git push origin v0.4.1

# Then create GitHub release manually
```

## Testing

Run the test suite to ensure everything works:

```bash
python run_tests.py --regression --feature
```

This validates that the new versioning system doesn't break existing functionality.
