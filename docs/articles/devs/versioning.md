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

### Benefits

1. **Human Readability**: `VERSION.meta` provides clear, structured version information
2. **Tool Compatibility**: `VERSION` maintains standard format for setuptools and other tools
3. **Build Metadata**: Preserves branch, build number, and dev version information
4. **CI/CD Integration**: Both files are automatically maintained by version management workflows

## Usage

### Branch-based Versioning Logic

- **Feature branches (`feat/`)**:
  - If created from `main`, minor version is incremented, and both `DEV_NUMBER` and `BUILD_NUMBER` are reset to 0.
  - If updating an existing feature branch, only the `BUILD_NUMBER` is incremented.
- **Fix branches (`fix/`)**:
  - If created from any branch, patch version is incremented and `BUILD_NUMBER` is reset to 0.
  - If updating the same fix branch, only the `BUILD_NUMBER` is incremented.
  - If switching between fix branches, patch version is incremented.
- **Main branch (`main`)**:
  - `DEV_NUMBER` and `BUILD_NUMBER` are cleared for clean releases.
- **Dev/other branches**:
  - If coming from `main`, the minor version is incremented and `DEV_NUMBER` is reset to 0.
  - Otherwise, `DEV_NUMBER` is incremented and `BUILD_NUMBER` is reset.

### Workflow Examples

#### Example 1: Feature Development

1. **Starting State**: `main` branch at `v1.2.0`
2. **Create Feature Branch**: `git checkout -b feat/new-feature`
   - Minor version is incremented: `v1.3.0.dev0+build0`
3. **First Push**: Increments to `v1.3.0.dev0+build1`
4. **Second Push**: Increments to `v1.3.0.dev0+build2`
5. **Merge to Dev**: `dev` branch becomes `v1.3.0.devN`
6. **Merge to Main**: `main` branch becomes `v1.3.0`

#### Example 2: Bug Fix

1. **Starting State**: `main` branch at `v1.2.0`
2. **Create Fix Branch**: `git checkout -b fix/critical-bug`
   - Patch version is incremented: `v1.2.1.dev0+build0`
3. **First Push**: Increments to `v1.2.1.dev0+build1`
4. **Switch to another fix branch**: Patch version is incremented for the new branch.
5. **Merge to Dev**: `dev` branch becomes `v1.2.1.devN`
6. **Hotfix to Main**: `main` branch becomes `v1.2.1`

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
