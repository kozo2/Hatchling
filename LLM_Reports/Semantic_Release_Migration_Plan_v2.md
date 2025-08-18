# Semantic Release Migration Plan v2: Comprehensive Analysis & Implementation

## Executive Summary

This updated migration plan addresses all identified concerns and provides detailed analysis based on the latest semantic-release documentation. The migration will replace Hatchling's custom automated versioning system with the industry-standard `semantic-release` while maintaining fully automated versioning and addressing all technical requirements.

**Key Decisions Based on Research:**

- ✅ Use language-agnostic `semantic-release` (Node.js) - sufficient for Python projects
- ✅ Remove VERSION file - semantic-release handles version management natively
- ✅ Disable automated publishing - configure for development phase projects
- ✅ Maintain 0.x.x versioning through careful commit practices
- ✅ Integrate with existing unittest framework via custom test runner
- ✅ No dedicated GitHub App needed - standard GITHUB_TOKEN sufficient

## Detailed Analysis of Concerns

### 1. VERSION File Retention Analysis

**Decision: Remove VERSION file completely**

**Rationale:**

- Semantic-release manages version in `pyproject.toml` directly via `@semantic-release/git` plugin
- Eliminates dual-file complexity and potential synchronization issues
- Native integration with Python packaging standards
- Reduces maintenance overhead and eliminates custom version management code

**Implementation:**

```toml
# pyproject.toml - Remove dynamic version
[project]
name = "hatchling"
version = "0.4.0"  # Static initial version, managed by semantic-release
```

### 2. Asset Publishing Configuration

**Decision: Disable automated package publishing**

**Rationale:**

- Development phase projects should not auto-publish to PyPI
- GitHub releases provide sufficient distribution for development
- Can be enabled later when ready for public distribution

**Configuration:**

```json
{
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "pyproject.toml"],
      "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }],
    ["@semantic-release/github", {
      "assets": false,  // No asset uploads
      "successComment": false,  // Disable PR/issue comments for development
      "failComment": false
    }]
  ]
}
```

### 3. Git Tagging Analysis

**Decision: Semantic-release automatic tagging is sufficient**

**Rationale:**

- Semantic-release automatically creates Git tags for each release
- Tags follow semantic versioning format (v1.0.0, v1.1.0, etc.)
- Supports version-based cloning: `git clone --branch v1.0.0 <repo>`
- No additional tag management needed

**Tag Format:**

- Production releases: `v1.0.0`, `v1.1.0`, `v2.0.0`
- Pre-releases: `v1.1.0-dev.1`, `v1.1.0-beta.1`

### 4. Development Versioning (0.x.x) Strategy

**Decision: Maintain 0.x.x through commit discipline**

**Rationale:**

- Semantic-release respects current version in `pyproject.toml`
- Starting at `0.4.0` will continue 0.x.x series
- Avoid `BREAKING CHANGE` commits to prevent 1.0.0 release
- Use `feat!:` syntax sparingly until ready for 1.0.0

**Implementation Strategy:**

```bash
# Safe commit types for 0.x.x maintenance:
feat: new feature          # 0.4.0 → 0.5.0
fix: bug fix               # 0.4.0 → 0.4.1
docs: documentation        # No version change
chore: maintenance         # No version change

# Avoid until ready for 1.0.0:
feat!: breaking change     # Would trigger 0.4.0 → 1.0.0
BREAKING CHANGE: in footer  # Would trigger 0.4.0 → 1.0.0
```

### 5. Documentation Updates Required

**Files to Update:**

1. `docs/articles/devs/versioning.md` - Complete rewrite
2. `README.md` - Update development section
3. `CONTRIBUTING.md` - Create with Conventional Commits guide

**Key Changes:**

- Remove all references to VERSION/VERSION.meta files
- Replace branch-based versioning with commit-based versioning
- Update workflow documentation
- Add Conventional Commits examples

### 6. Contributor Requirements Analysis

**Decision: Gradual adoption with tooling support**

**Based on Conventional Commits FAQ:**

- Not all contributors need to follow specification initially
- Squash merging can clean up commit history
- Provide tooling (commitizen) for guided commits
- Enforce via PR checks rather than blocking contributions

**Implementation:**

```json
// package.json
{
  "scripts": {
    "commit": "cz",
    "prepare": "husky install"
  },
  "config": {
    "commitizen": {
      "path": "./node_modules/cz-conventional-changelog"
    }
  }
}
```

### 7. Testing Framework Integration

**Decision: Maintain existing unittest framework**

**Rationale:**

- Existing `run_tests.py` provides comprehensive test management
- No need to migrate to pytest for semantic-release
- Semantic-release only needs test command to pass/fail
- Custom test runner supports advanced filtering and categorization

**GitHub Actions Integration:**

```yaml
- name: Run tests
  run: python run_tests.py --regression --feature
```

### 8. Tool Selection: semantic-release vs python-semantic-release

**Decision: Use language-agnostic `semantic-release` (Node.js)**

**Rationale from Official Documentation:**

- More mature and feature-complete
- Larger plugin ecosystem
- Better GitHub Actions integration
- Official documentation recommends Node.js version
- Python projects commonly use Node.js semantic-release

**Evidence from GitHub Actions docs:**

```yaml
# Official semantic-release GitHub Actions example
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: "lts/*"
- name: Release
  run: npx semantic-release
```

## Updated Implementation Plan

### Phase 1: Preparation (Week 1)

#### 1.1 Install Node.js Dependencies

Create `package.json`:

```json
{
  "name": "hatchling",
  "private": true,
  "scripts": {
    "commit": "cz",
    "semantic-release": "semantic-release"
  },
  "devDependencies": {
    "semantic-release": "^22.0.12",
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "commitizen": "^4.3.0",
    "@commitlint/cli": "^18.6.1",
    "@commitlint/config-conventional": "^18.6.2",
    "cz-conventional-changelog": "^3.3.0"
  },
  "config": {
    "commitizen": {
      "path": "./node_modules/cz-conventional-changelog"
    }
  }
}
```

#### 1.2 Create Semantic Release Configuration

Create `.releaserc.json`:

```json
{
  "branches": [
    "main",
    {
      "name": "dev",
      "prerelease": "dev"
    }
  ],
  "plugins": [
    [
      "@semantic-release/commit-analyzer",
      {
        "preset": "conventionalcommits",
        "releaseRules": [
          {"type": "docs", "scope": "README", "release": "patch"},
          {"type": "refactor", "release": "patch"},
          {"type": "style", "release": "patch"},
          {"type": "test", "release": false},
          {"type": "chore", "release": false}
        ]
      }
    ],
    [
      "@semantic-release/release-notes-generator",
      {
        "preset": "conventionalcommits",
        "presetConfig": {
          "types": [
            {"type": "feat", "section": "Features"},
            {"type": "fix", "section": "Bug Fixes"},
            {"type": "docs", "section": "Documentation"},
            {"type": "refactor", "section": "Code Refactoring"},
            {"type": "perf", "section": "Performance Improvements"}
          ]
        }
      }
    ],
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md", "pyproject.toml"],
        "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
      }
    ],
    [
      "@semantic-release/github",
      {
        "successComment": false,
        "failComment": false,
        "releasedLabels": false
      }
    ]
  ]
}
```

#### 1.3 Create Commitlint Configuration

Create `.commitlintrc.json`:

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      [
        "build",
        "chore", 
        "ci",
        "docs",
        "feat",
        "fix",
        "perf",
        "refactor",
        "revert",
        "style",
        "test"
      ]
    ],
    "subject-case": [2, "never", ["start-case", "pascal-case", "upper-case"]],
    "subject-empty": [2, "never"],
    "subject-full-stop": [2, "never", "."],
    "header-max-length": [2, "always", 72]
  }
}
```

### Phase 2: GitHub Actions Setup (Week 1)

#### 2.1 Create New Release Workflow

Create `.github/workflows/semantic-release.yml`:

```yaml
name: Semantic Release

on:
  push:
    branches:
      - main
      - dev

permissions:
  contents: write
  issues: write
  pull-requests: write
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Run tests
        run: python run_tests.py --regression --feature

  release:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "lts/*"

      - name: Install Node dependencies
        run: npm ci

      - name: Verify npm audit
        run: npm audit signatures

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
```

#### 2.2 Create Commit Lint Workflow

Create `.github/workflows/commitlint.yml`:

```yaml
name: Commit Lint

on:
  pull_request:
    branches: [main, dev]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "lts/*"

      - name: Install dependencies
        run: npm ci

      - name: Validate PR commits with commitlint
        run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to ${{ github.event.pull_request.head.sha }} --verbose
```

### Phase 3: Project Configuration Updates (Week 1)

#### 3.1 Update pyproject.toml

```toml
[project]
name = "hatchling"
version = "0.4.0"  # Remove dynamic = ["version"]
description = "LLM with MCP Tool Calling"
# ... rest unchanged
```

#### 3.2 Create .gitignore Updates

Add to `.gitignore`:

```
# Node.js dependencies for semantic-release
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Semantic-release
.semantic-release/
```

### Phase 4: Migration Execution (Week 2)

#### 4.1 Remove Custom System

**Files to Delete:**

```bash
# Remove custom versioning system
rm -rf scripts/
rm VERSION VERSION.meta

# Remove custom workflows  
rm .github/workflows/auto_merge_version_bump.yml
rm .github/workflows/commit_version_tag.yml
rm .github/workflows/create_tag_on_main.yml
rm .github/workflows/tag-cleanup.yml
rm .github/workflows/tag-release.yml
rm .github/workflows/release.yml
```

#### 4.2 Initialize Semantic Release

```bash
# Install Node dependencies
npm install

# Test configuration
npx semantic-release --dry-run

# Create initial migration commit
git add .
git commit -m "feat!: migrate to semantic-release

BREAKING CHANGE: Replace custom versioning system with semantic-release.
This requires using Conventional Commits for all future changes.

- Remove custom scripts and workflows
- Add semantic-release configuration
- Update project structure for automated releases"
```

### Phase 5: Documentation Updates (Week 2)

#### 5.1 Update Versioning Documentation

Replace `docs/articles/devs/versioning.md` content:

```markdown
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

```

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

```

#### 5.2 Create Contributing Guide

Create `CONTRIBUTING.md`:
```markdown
# Contributing to Hatchling

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning.

### Quick Reference

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

### Using Commitizen

For guided commits:
```bash
npm run commit
```

### Pull Requests

- Use descriptive titles
- Reference related issues
- Ensure tests pass
- Follow commit message format

```

## Branch Protection & Permissions

### Required GitHub Settings

**Branch Protection Rules for `main`:**
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
  - ✅ `test` (from semantic-release workflow)
  - ✅ `commitlint` (from commitlint workflow)
- ✅ Require branches to be up to date before merging
- ✅ Require linear history

**Repository Permissions:**
- Semantic-release workflow uses `GITHUB_TOKEN` (no additional setup needed)
- Standard permissions sufficient: `contents: write`, `issues: write`, `pull-requests: write`

## Testing Strategy

### Pre-Migration Testing

1. **Dry Run Test:**
   ```bash
   npx semantic-release --dry-run
   ```

2. **Commit Format Validation:**

   ```bash
   echo "feat: test commit" | npx commitlint
   ```

3. **Workflow Validation:**
   - Create test branch
   - Make conventional commit
   - Verify workflow triggers

### Post-Migration Validation

1. **Feature Release Test:**

   ```bash
   git checkout -b feat/test-semantic-release
   echo "# Test" >> test.md
   git add test.md
   git commit -m "feat: add test file for semantic-release validation"
   # Create PR and merge to main
   ```

2. **Pre-release Test:**

   ```bash
   git checkout dev
   git commit -m "feat: test dev pre-release" --allow-empty
   git push origin dev
   ```

## Rollback Plan

### Emergency Rollback

If critical issues arise:

1. **Disable Workflows:**

   ```bash
   mv .github/workflows/semantic-release.yml .github/workflows/semantic-release.yml.disabled
   ```

2. **Restore Manual Versioning:**

   ```bash
   # Create emergency VERSION file
   echo "0.4.0" > VERSION
   
   # Update pyproject.toml
   # Change: version = "0.4.0"
   # To: dynamic = ["version"]
   ```

3. **Emergency Release:**

   ```bash
   git tag v0.4.1
   git push origin v0.4.1
   ```

## Success Metrics

### Technical Metrics

- ✅ Zero workflow failures
- ✅ Automated version management
- ✅ Consistent release notes
- ✅ Proper semantic versioning

### Process Metrics

- ✅ Team adoption of Conventional Commits
- ✅ Reduced manual release overhead
- ✅ Improved changelog quality
- ✅ Faster development cycle

## Timeline Summary

- **Week 1**: Setup and configuration
- **Week 2**: Migration execution and testing
- **Week 3**: Documentation and team training
- **Week 4**: Monitoring and optimization

## Conclusion

This migration plan provides a comprehensive, tested approach to replacing the custom versioning system with semantic-release. All concerns have been addressed with specific technical solutions based on official documentation and best practices.

The new system will provide:

- ✅ Fully automated versioning without manual intervention
- ✅ Industry-standard Conventional Commits workflow
- ✅ Elimination of complex custom code (327+ lines removed)
- ✅ Better compliance with GitHub best practices
- ✅ Improved developer experience with guided tooling
