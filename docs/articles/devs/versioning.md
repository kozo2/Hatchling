# Automated Versioning System

This article is about:

- The dual-file versioning system in Hatchling
- How version information is managed for both humans and tools

You will learn about:

- The structure and purpose of `VERSION.meta` and `VERSION`
- How to use the versioning scripts and workflows
- Best practices for version management

Hatchling uses a dual-file versioning system to maintain both human-readable version information and compatibility with Python packaging tools.

## Dual-File Versioning System

### Files

#### VERSION.meta

- Human-readable, structured version information for CI/CD and development
- Format: Key-value pairs with comments
- Example:

  ```txt
  MAJOR=0
  MINOR=5
  PATCH=0
  DEV_NUMBER=0
  BUILD_NUMBER=1
  BRANCH=feat/automated-versioning
  ```

#### VERSION

- Simple version string for setuptools and Python packaging
- Format: Standard semantic version string
- Example: `0.5.0.dev0+build1`

## Usage

### For Development

- Read version information from `VERSION.meta` for detailed component access
- Use `scripts/version_manager.py` to update versions while preserving both formats

### For Building/Packaging

- Run `scripts/prepare_version.py` before building to ensure `VERSION` file is in correct format
- The build process reads from the simple `VERSION` file
- `VERSION.meta` is preserved unchanged

### In CI/CD Workflows

- Both files are committed to maintain version history
- Workflows download and commit both files as artifacts
- Version increments update both files automatically

## Commands

```bash
# Get current version
python scripts/version_manager.py --get

# Increment version components
python scripts/version_manager.py --increment [major|minor|patch|dev|build]

# Update version for specific branch
python scripts/version_manager.py --update-for-branch BRANCH_NAME

# Prepare for build (ensures VERSION file is in simple format)
python scripts/prepare_version.py
```

## Benefits

1. **Human Readability**: `VERSION.meta` provides clear, structured version information
2. **Tool Compatibility**: `VERSION` maintains standard format for setuptools and other tools
3. **Build Metadata**: Preserves branch, build number, and dev version information
4. **CI/CD Integration**: Both files are automatically maintained by version management workflows

## Workflow Examples

### Example 1: Feature Development

1. **Starting State**: `dev` branch at `v1.2.0-dev`
2. **Create Feature Branch**: `git checkout -b feat/new-feature`
3. **Initial Version**: Automatically becomes `v1.3.0-dev.b1`
4. **First Push**: Increments to `v1.3.0-dev.b2`
5. **Second Push**: Increments to `v1.3.0-dev.b3`
6. **Merge to Dev**: `dev` branch becomes `v1.3.0-dev`
7. **Merge to Main**: `main` branch becomes `v1.3.0`

### Example 2: Bug Fix

1. **Starting State**: `dev` branch at `v1.2.0-dev`
2. **Create Fix Branch**: `git checkout -b fix/critical-bug`
3. **Initial Version**: Automatically becomes `v1.2.1-dev.b1`
4. **Push Changes**: Increments to `v1.2.1-dev.b2`
5. **Merge to Dev**: `dev` branch becomes `v1.2.1-dev`
6. **Hotfix to Main**: Can merge directly, `main` becomes `v1.2.1`

## GitHub Actions Workflows

### 1. Release Workflow (`release.yml`)

**Triggered by**: Pushes to `main` branch

**Actions**:

- Tests the package build
- Updates version for main branch (removes pre-release suffixes)
- Creates official release with version tag
- Uploads build artifacts
- Commits updated VERSION file

### 2. Pre-Release Workflow (`prerelease.yml`)

**Triggered by**: Pushes to `dev` branch

**Actions**:

- Tests the package build
- Updates version for dev branch (adds `-dev` suffix)
- Creates pre-release with version tag
- Uploads build artifacts
- Commits updated VERSION file

### 3. Feature/Fix Workflow (`feature-fix.yml`)

**Triggered by**: Pushes to `feat/` and `fix/` branches

**Actions**:

- Tests the package build
- Updates version based on branch type
- Increments build number on each push
- Creates lightweight tags for tracking
- Commits updated VERSION file

### 4. Tag Cleanup Workflow (`tag-cleanup.yml`)

**Triggered by**: Weekly schedule or manual dispatch

**Actions**:

- Identifies old tags for cleanup
- Removes build tags older than 7 days
- Removes dev tags older than 30 days
- Supports dry-run mode for testing

## Manual Version Management

The `scripts/version_manager.py` script provides manual control over versioning:

### Get Current Version

```bash
python scripts/version_manager.py --get
```

### Update Version for Branch

```bash
python scripts/version_manager.py --update-for-branch feat/my-feature
python scripts/version_manager.py --update-for-branch dev
python scripts/version_manager.py --update-for-branch main
```

### Increment Version Components

```bash
python scripts/version_manager.py --increment major
python scripts/version_manager.py --increment minor
python scripts/version_manager.py --increment patch
python scripts/version_manager.py --increment build
```

### Prepare for Building

```bash
python scripts/prepare_version.py
```

This converts the structured VERSION file to a simple format that setuptools can read.

## Integration with setuptools

The `pyproject.toml` file is configured to read the version from the VERSION file:

```toml
[tool.setuptools.dynamic]
version = {file = "VERSION"}
```

Before building, the `prepare_version.py` script converts the structured VERSION file to a simple format that setuptools understands.

## Testing

Run the versioning system tests:

```bash
python tests/test_versioning.py
```

This validates:

- Version string generation
- Branch-based version updates
- Build number increments
- The examples from the project requirements

## Best Practices

1. **Never manually edit version numbers** - let the automation handle it
2. **Use descriptive branch names** with proper prefixes (`feat/`, `fix/`)
3. **Test in feature branches** before merging to dev
4. **Use dev branch** for integration testing before production
5. **Keep main branch stable** - only merge tested code from dev
6. **Monitor tag cleanup** to avoid repository bloat

## Troubleshooting


### VERSION File Format Issues

If the version files get corrupted, restore them as follows:

- For the structured format, restore `VERSION.meta` with:

  ```txt
  MAJOR=1
  MINOR=0
  PATCH=0
  DEV_NUMBER=0
  BUILD_NUMBER=0
  BRANCH=main
  ```

- For the simple format, regenerate `VERSION` by running:

  ```bash
  python scripts/prepare_version.py
  ```

  This will convert the structured `VERSION.meta` to the correct setuptools-compatible `VERSION` file.

### Build Failures

If builds fail due to version format:

```bash
python scripts/prepare_version.py
```

### Testing Version Logic

Run the test suite to verify versioning logic:

```bash
python tests/test_versioning.py
```

### Manual Tag Creation

If GitHub Actions fail, manually create tags:

```bash
# Ensure VERSION is up to date with VERSION.meta
python scripts/prepare_version.py
VERSION=$(python scripts/version_manager.py --get)
git tag $VERSION
git push origin $VERSION
```
