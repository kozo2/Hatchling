# Hatchling Versioning System Documentation

This document provides detailed information about the automated versioning system implemented in Hatchling.

## Overview

Hatchling uses an automated semantic versioning system that:
- Tracks version components in a structured `VERSION` file
- Automatically increments versions based on branch types
- Creates releases and pre-releases through GitHub Actions
- Maintains compatibility with Python setuptools

## Version File Structure

The `VERSION` file at the project root stores version information in a structured format:

```
MAJOR=1
MINOR=0
PATCH=3
PRERELEASE=dev
BUILD=b1
BRANCH=feat/example
```

### Components

- **MAJOR**: Major version number (breaking changes)
- **MINOR**: Minor version number (new features)
- **PATCH**: Patch version number (bug fixes)
- **PRERELEASE**: Pre-release identifier (`dev` for development versions)
- **BUILD**: Build number for feature/fix branches (`b1`, `b2`, etc.)
- **BRANCH**: Current branch name for tracking

## Version Patterns

### Main Branch (`main`)
- Format: `vMAJOR.MINOR.PATCH`
- Example: `v1.2.3`
- Used for: Production releases

### Development Branch (`dev`)
- Format: `vMAJOR.MINOR.PATCH-dev`
- Example: `v1.2.3-dev`
- Used for: Pre-releases and testing

### Feature Branches (`feat/`)
- Format: `vMAJOR.MINOR.PATCH-dev.bN`
- Example: `v1.3.0-dev.b1`
- Increments: Minor version + build number on each push

### Fix Branches (`fix/`)
- Format: `vMAJOR.MINOR.PATCH-dev.bN`
- Example: `v1.2.1-dev.b1`
- Increments: Patch version + build number on each push

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
If the VERSION file gets corrupted, restore it with proper format:
```
MAJOR=1
MINOR=0
PATCH=0
PRERELEASE=
BUILD=
BRANCH=main
```

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
VERSION=$(python scripts/version_manager.py --get)
git tag $VERSION
git push origin $VERSION
```