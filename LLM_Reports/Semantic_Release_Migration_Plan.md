# Semantic Release Migration Plan: Complete Replacement of Custom Versioning System

## Executive Summary

This comprehensive migration plan details the complete replacement of Hatchling's custom automated versioning system with `semantic-release`, a battle-tested industry standard. The migration will eliminate all architectural flaws while maintaining fully automated versioning through Conventional Commits and branch-based workflows.

**Key Benefits:**
- ✅ Eliminates infinite loop risks and complex dependency chains
- ✅ Full GitHub branch protection compliance
- ✅ Atomic operations with proper error handling
- ✅ Industry-standard Conventional Commits workflow
- ✅ Maintains fully automated versioning without manual intervention
- ✅ Supports pre-releases and multiple distribution channels

## Current State Analysis

### What Will Be Removed

The following custom implementation components will be completely removed:

**Scripts to Remove:**
- `scripts/version_manager.py` (327 lines of complex version logic)
- `scripts/prepare_version.py` (version preparation logic)
- `scripts/tag_cleanup.py` (cleanup utilities)

**Workflows to Remove:**
- `.github/workflows/auto_merge_version_bump.yml`
- `.github/workflows/commit_version_tag.yml`
- `.github/workflows/create_tag_on_main.yml`
- `.github/workflows/tag-cleanup.yml`
- `.github/workflows/tag-release.yml`
- `.github/workflows/release.yml` (current release workflow)

**Files to Remove:**
- `VERSION` (simple version file)
- `VERSION.meta` (structured version metadata)

### Current System Issues

1. **Infinite Loop Risk**: Workflows trigger other workflows creating potential loops
2. **Complex Dependencies**: Multi-step chains with numerous failure points
3. **Branch Protection Conflicts**: Requires PR-based workarounds for protected branches
4. **Non-Atomic Operations**: Version updates span multiple commits and workflows
5. **Poor Error Handling**: Limited recovery mechanisms for failed operations
6. **Maintenance Overhead**: 327+ lines of custom version management code

## Semantic Release Overview

### How Semantic Release Works

Semantic Release automates the entire release workflow based on commit message analysis:

1. **Commit Analysis**: Analyzes commit messages using Conventional Commits format
2. **Version Calculation**: Determines next version based on commit types:
   - `fix:` → Patch release (1.0.0 → 1.0.1)
   - `feat:` → Minor release (1.0.0 → 1.1.0)
   - `BREAKING CHANGE:` → Major release (1.0.0 → 2.0.0)
3. **Release Generation**: Creates GitHub releases with auto-generated changelogs
4. **Asset Publishing**: Publishes to npm, PyPI, or other registries
5. **Notification**: Updates issues/PRs and sends notifications

### Key Advantages

- **Battle-Tested**: Used by thousands of projects including major open source libraries
- **Atomic Operations**: All release steps happen in a single workflow run
- **Branch Protection Compliant**: Works seamlessly with protected branches
- **Extensible**: Rich plugin ecosystem for customization
- **Zero Configuration**: Works out-of-the-box with sensible defaults

## Conventional Commits Integration

### Transition from Current Practices

**Current Approach**: Branch naming patterns determine version increments
- `feat/*` branches → Minor version increment
- `fix/*` branches → Patch version increment

**New Approach**: Commit message format determines version increments
- `feat: add new feature` → Minor version increment
- `fix: resolve bug` → Patch version increment
- `feat!: breaking change` → Major version increment

### Conventional Commits Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common Types:**
- `feat`: New feature (minor version)
- `fix`: Bug fix (patch version)
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Breaking Changes:**
- Add `!` after type: `feat!: breaking change`
- Or add footer: `BREAKING CHANGE: description`

### Migration Strategy for Commit Messages

**Phase 1**: Education and tooling setup
- Install commitizen for guided commit messages
- Add commit message linting with commitlint
- Update documentation with examples

**Phase 2**: Gradual adoption
- Encourage conventional commits in new PRs
- Provide commit message templates
- Add PR checks for commit format

**Phase 3**: Enforcement
- Require conventional commits for all new changes
- Use squash merging to clean up commit history

## Step-by-Step Migration Plan

### Phase 1: Preparation and Setup (Week 1)

#### 1.1 Install Dependencies

Add to `pyproject.toml`:
```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
build_command = "python -m build"
dist_path = "dist/"
upload_to_pypi = false
upload_to_release = true
remove_dist = false

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.dev]
match = "dev"
prerelease = "dev"

[tool.semantic_release.changelog]
template_dir = "templates"
changelog_file = "CHANGELOG.md"

[tool.semantic_release.commit_parser_options]
allowed_tags = ["build", "chore", "ci", "docs", "feat", "fix", "perf", "style", "refactor", "test"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf"]
```

#### 1.2 Create Package.json for Node Dependencies

Create `package.json`:
```json
{
  "name": "hatchling",
  "private": true,
  "devDependencies": {
    "semantic-release": "^22.0.0",
    "@semantic-release/changelog": "^6.0.0",
    "@semantic-release/git": "^10.0.0",
    "@semantic-release/github": "^9.0.0",
    "commitizen": "^4.3.0",
    "@commitlint/cli": "^18.0.0",
    "@commitlint/config-conventional": "^18.0.0",
    "cz-conventional-changelog": "^3.3.0"
  },
  "config": {
    "commitizen": {
      "path": "./node_modules/cz-conventional-changelog"
    }
  }
}
```

#### 1.3 Create Semantic Release Configuration

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
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md", "pyproject.toml"],
        "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
      }
    ],
    "@semantic-release/github"
  ]
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
  pull_request:
    branches:
      - main

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

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest

      - name: Run tests
        run: python run_tests.py

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

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          npm ci
          python -m pip install --upgrade pip
          pip install build python-semantic-release

      - name: Verify the integrity of provenance attestations and registry signatures for installed dependencies
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

      - name: Validate current commit (last commit) with commitlint
        if: github.event_name == 'push'
        run: npx commitlint --last --verbose

      - name: Validate PR commits with commitlint
        if: github.event_name == 'pull_request'
        run: npx commitlint --from ${{ github.event.pull_request.head.sha }}~${{ github.event.pull_request.commits }} --to ${{ github.event.pull_request.head.sha }} --verbose
```

### Phase 3: Configuration Files (Week 1)

#### 3.1 Create Commitlint Configuration

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
    ]
  }
}
```

#### 3.2 Update Pyproject.toml

Update version configuration in `pyproject.toml`:
```toml
[project]
name = "hatchling"
version = "0.4.0"  # Remove dynamic = ["version"]
# ... rest of configuration
```

### Phase 4: Migration Execution (Week 2)

#### 4.1 Remove Custom System

1. **Delete custom scripts:**
   ```bash
   rm -rf scripts/
   ```

2. **Delete custom workflows:**
   ```bash
   rm .github/workflows/auto_merge_version_bump.yml
   rm .github/workflows/commit_version_tag.yml
   rm .github/workflows/create_tag_on_main.yml
   rm .github/workflows/tag-cleanup.yml
   rm .github/workflows/tag-release.yml
   rm .github/workflows/release.yml
   ```

3. **Delete version files:**
   ```bash
   rm VERSION VERSION.meta
   ```

#### 4.2 Initialize Semantic Release

1. **Install Node dependencies:**
   ```bash
   npm install
   ```

2. **Set up initial version:**
   ```bash
   # Update pyproject.toml with current version
   # Commit with conventional format
   git add .
   git commit -m "feat!: migrate to semantic-release

   BREAKING CHANGE: Replace custom versioning system with semantic-release.
   This requires using Conventional Commits for all future changes."
   ```

3. **Test the new system:**
   ```bash
   # Dry run to verify configuration
   npx semantic-release --dry-run
   ```

### Phase 5: Validation and Testing (Week 2)

#### 5.1 Test Release Process

1. **Create test feature branch:**
   ```bash
   git checkout -b feat/test-semantic-release
   echo "# Test" >> test.md
   git add test.md
   git commit -m "feat: add test file for semantic-release validation"
   git push origin feat/test-semantic-release
   ```

2. **Create PR and merge to trigger release**

3. **Verify release creation:**
   - Check GitHub releases page
   - Verify changelog generation
   - Confirm version bumping

#### 5.2 Test Pre-release Process

1. **Push to dev branch:**
   ```bash
   git checkout dev
   git commit -m "feat: test dev pre-release" --allow-empty
   git push origin dev
   ```

2. **Verify pre-release creation:**
   - Check for dev pre-release tags
   - Verify pre-release marking in GitHub

### Phase 6: Documentation and Training (Week 3)

#### 6.1 Update Documentation

Create `docs/CONTRIBUTING.md`:
```markdown
# Contributing to Hatchling

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Examples
- `feat: add new LLM provider`
- `fix: resolve memory leak in streaming`
- `docs: update API documentation`
- `feat!: change configuration format`

### Using Commitizen
For guided commit messages, use:
```bash
npm run commit
# or
npx cz
```
```

#### 6.2 Update README

Add to `README.md`:
```markdown
## Development

### Commit Messages
This project uses [Conventional Commits](https://www.conventionalcommits.org/). 
Please format your commit messages accordingly:

- `feat:` for new features
- `fix:` for bug fixes  
- `docs:` for documentation changes
- `test:` for test changes
- `chore:` for maintenance tasks

### Releases
Releases are automatically created when changes are merged to `main` using 
[semantic-release](https://semantic-release.gitbook.io/).
```

## Configuration Examples

### Complete .releaserc.json
```json
{
  "branches": [
    "main",
    {
      "name": "dev", 
      "prerelease": "dev"
    },
    {
      "name": "beta",
      "prerelease": "beta"
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
          {"type": "style", "release": "patch"}
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
            {"type": "chore", "hidden": true},
            {"type": "docs", "section": "Documentation"},
            {"type": "style", "hidden": true},
            {"type": "refactor", "section": "Code Refactoring"},
            {"type": "perf", "section": "Performance Improvements"},
            {"type": "test", "hidden": true}
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
        "successComment": "🎉 This ${issue.pull_request ? 'PR is included' : 'issue has been resolved'} in version ${nextRelease.version} 🎉",
        "labels": ["released"],
        "releasedLabels": ["released<%= nextRelease.type === 'prerelease' ? ` on @${nextRelease.channel}` : '' %>"]
      }
    ]
  ]
}
```

## Migration Timeline

### Week 1: Setup and Configuration
- **Day 1-2**: Install dependencies and create configuration files
- **Day 3-4**: Set up GitHub Actions workflows  
- **Day 5**: Create commit lint and validation workflows

### Week 2: Migration Execution
- **Day 1-2**: Remove custom system components
- **Day 3-4**: Initialize semantic-release and test
- **Day 5**: Validation and troubleshooting

### Week 3: Documentation and Training
- **Day 1-2**: Update all documentation
- **Day 3-4**: Team training on Conventional Commits
- **Day 5**: Final testing and go-live

### Week 4: Monitoring and Optimization
- **Day 1-3**: Monitor release process
- **Day 4-5**: Optimize configuration based on usage

## Validation and Testing

### Pre-Migration Checklist
- [ ] All dependencies installed
- [ ] Configuration files created
- [ ] GitHub Actions workflows tested
- [ ] Team trained on Conventional Commits
- [ ] Documentation updated
- [ ] Backup of current system created

### Post-Migration Validation
- [ ] Successful release created from main branch
- [ ] Pre-release created from dev branch
- [ ] Changelog automatically generated
- [ ] GitHub releases properly formatted
- [ ] Version bumping working correctly
- [ ] No infinite loops or workflow conflicts

### Testing Scenarios
1. **Feature Release**: Merge feat commit to main → Minor version bump
2. **Bug Fix Release**: Merge fix commit to main → Patch version bump  
3. **Breaking Change**: Merge feat! commit to main → Major version bump
4. **Pre-release**: Push to dev branch → Pre-release version
5. **Documentation**: Merge docs commit → No release (configurable)

## Rollback Plan

### Emergency Rollback Procedure

If critical issues arise during migration:

1. **Immediate Actions:**
   ```bash
   # Disable semantic-release workflow
   mv .github/workflows/semantic-release.yml .github/workflows/semantic-release.yml.disabled
   
   # Restore custom workflows from backup
   git checkout HEAD~1 -- .github/workflows/
   git checkout HEAD~1 -- scripts/
   git checkout HEAD~1 -- VERSION VERSION.meta
   ```

2. **Restore Custom System:**
   - Revert pyproject.toml changes
   - Restore version files
   - Re-enable custom workflows
   - Create hotfix release using old system

3. **Communication:**
   - Notify team of rollback
   - Document issues encountered
   - Plan remediation strategy

### Rollback Triggers
- Infinite loop detection in workflows
- Failed releases blocking development
- Critical functionality broken
- Team unable to adapt to new process

## Success Metrics

### Technical Metrics
- Zero workflow infinite loops
- 100% successful releases
- Reduced release time (target: <5 minutes)
- Eliminated manual version management

### Process Metrics  
- Team adoption of Conventional Commits (target: >90%)
- Reduced release-related issues (target: 50% reduction)
- Improved changelog quality
- Faster hotfix deployment

### Maintenance Metrics
- Reduced custom code maintenance (327 lines → 0)
- Simplified workflow debugging
- Improved error handling and recovery
- Better compliance with GitHub best practices

## Conclusion

This migration plan provides a comprehensive roadmap for replacing Hatchling's custom versioning system with semantic-release. The new system will eliminate architectural flaws while maintaining fully automated versioning through industry-standard practices.

**Key Benefits Achieved:**
- ✅ Eliminated infinite loop risks
- ✅ Simplified architecture with proven tools
- ✅ Full GitHub branch protection compliance  
- ✅ Atomic release operations
- ✅ Industry-standard Conventional Commits
- ✅ Comprehensive error handling
- ✅ Zero maintenance overhead for version management

The migration is designed to be executed in phases with comprehensive testing and validation at each step, ensuring a smooth transition with minimal risk to the development process.
