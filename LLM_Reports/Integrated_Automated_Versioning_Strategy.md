# Integrated Automated Versioning Strategy: Preserving Emergent Versioning While Fixing Architectural Issues

## Executive Summary

This report synthesizes insights from all previous analyses and extensive research into state-of-the-art automated versioning solutions to propose a comprehensive strategy that **preserves the automatic, emergent versioning behavior** of the current Hatchling system while eliminating the critical architectural flaws.

The solution combines industry-standard tools (semantic-release/release-please) with custom branch-pattern automation to maintain the "hands-off" developer experience while achieving enterprise-grade reliability and compliance with GitHub branch protection.

## Core Requirement Analysis

### What Must Be Preserved

The current system's **key value proposition** is automatic version bumping based on git workflow patterns:

- **feat/* branches** → Minor version increment + dev/build numbers
- **fix/* branches** → Patch version increment + dev/build numbers  
- **dev branch** → Development prereleases with dev numbers
- **main branch** → Clean releases (no dev/build suffixes)

**Critical Success Factor**: Developers never need to think about versioning - it emerges naturally from their git workflow patterns.

### What Must Be Fixed

1. **Infinite loop risk** from workflow chains
2. **Complex dependency chains** with multiple failure points
3. **Branch protection conflicts** requiring PR-based workarounds
4. **Non-atomic operations** spanning multiple commits
5. **Poor error handling** and recovery mechanisms

## Research Findings: State-of-the-Art Solutions

### 1. Semantic Release with Branch Configuration

**Key Discovery**: Semantic-release supports sophisticated branch-based workflows through its `branches` configuration:

```javascript
// .releaserc.js
module.exports = {
  branches: [
    'main',
    { name: 'dev', prerelease: 'dev' },
    { name: 'feat/*', prerelease: '${name.replace(/^feat\\//g, "")}-dev' },
    { name: 'fix/*', prerelease: '${name.replace(/^fix\\//g, "")}-fix' }
  ],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    '@semantic-release/changelog',
    '@semantic-release/npm',
    '@semantic-release/github',
    '@semantic-release/git'
  ]
}
```

**Benefits**:

- Automatic version calculation based on conventional commits
- Branch-specific prerelease patterns
- Built-in loop prevention
- GitHub App authentication support
- Atomic operations

### 2. Release Please with Custom Configuration

**Key Discovery**: Release-please can be configured for branch-based automation while maintaining PR-based oversight:

```yaml
# release-please-config.json
{
  "packages": {
    ".": {
      "release-type": "python",
      "include-component-in-tag": false,
      "include-v-in-tag": true
    }
  },
  "branches": ["main", "dev"],
  "changelog-sections": [
    {"type": "feat", "section": "Features"},
    {"type": "fix", "section": "Bug Fixes"},
    {"type": "chore", "section": "Miscellaneous", "hidden": true}
  ]
}
```

### 3. Advanced GitHub Actions Patterns

**Key Discovery**: Modern GitHub Actions patterns for automated versioning include:

1. **Conditional Execution** to prevent loops
2. **GitHub App Authentication** for branch protection bypass
3. **Atomic Commit Strategies** for consistency
4. **Branch Pattern Triggers** for emergent behavior
5. **Fail-Safe Mechanisms** for error recovery

## Proposed Integrated Solutions

### Option 1: Enhanced Semantic Release (Recommended)

**Architecture**: Direct commit with semantic-release + custom branch logic

```yaml
name: Automated Versioning
on:
  push:
    branches: [main, dev, 'feat/*', 'fix/*']
  workflow_dispatch:
    inputs:
      force_release:
        description: 'Force release creation'
        required: false
        default: false

jobs:
  version-and-release:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]') && github.actor != 'github-actions[bot]'"
    
    steps:
      - name: Generate GitHub App Token
        id: generate-token
        uses: tibdex/github-app-token@v2
        with:
          app_id: ${{ secrets.HATCHLING_APP_ID }}
          private_key: ${{ secrets.HATCHLING_APP_PRIVATE_KEY }}

      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ steps.generate-token.outputs.token }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine semantic-release

      - name: Configure Git
        run: |
          git config --local user.email "hatchling-bot@users.noreply.github.com"
          git config --local user.name "Hatchling Bot"

      - name: Determine Version Strategy
        id: strategy
        run: |
          BRANCH="${{ github.ref_name }}"
          if [[ "$BRANCH" == "main" ]]; then
            echo "strategy=release" >> $GITHUB_OUTPUT
            echo "prerelease=false" >> $GITHUB_OUTPUT
          elif [[ "$BRANCH" == "dev" ]]; then
            echo "strategy=prerelease" >> $GITHUB_OUTPUT
            echo "prerelease=dev" >> $GITHUB_OUTPUT
          elif [[ "$BRANCH" =~ ^feat/ ]]; then
            FEATURE_NAME=$(echo "$BRANCH" | sed 's/^feat\///')
            echo "strategy=prerelease" >> $GITHUB_OUTPUT
            echo "prerelease=${FEATURE_NAME}-dev" >> $GITHUB_OUTPUT
          elif [[ "$BRANCH" =~ ^fix/ ]]; then
            FIX_NAME=$(echo "$BRANCH" | sed 's/^fix\///')
            echo "strategy=prerelease" >> $GITHUB_OUTPUT
            echo "prerelease=${FIX_NAME}-fix" >> $GITHUB_OUTPUT
          else
            echo "strategy=skip" >> $GITHUB_OUTPUT
          fi

      - name: Run Tests
        if: steps.strategy.outputs.strategy != 'skip'
        run: python -m pytest tests/ || exit 1

      - name: Semantic Release
        if: steps.strategy.outputs.strategy != 'skip'
        env:
          GITHUB_TOKEN: ${{ steps.generate-token.outputs.token }}
          GH_TOKEN: ${{ steps.generate-token.outputs.token }}
        run: |
          # Configure semantic-release for current branch
          cat > .releaserc.js << EOF
          module.exports = {
            branches: [
              'main',
              { name: 'dev', prerelease: 'dev' },
              { name: 'feat/*', prerelease: '\${name.replace(/^feat\\\\//g, "")}-dev' },
              { name: 'fix/*', prerelease: '\${name.replace(/^fix\\\\//g, "")}-fix' }
            ],
            plugins: [
              '@semantic-release/commit-analyzer',
              '@semantic-release/release-notes-generator',
              '@semantic-release/changelog',
              [
                '@semantic-release/exec',
                {
                  prepareCmd: 'python scripts/version_manager.py --set-version \${nextRelease.version}',
                  publishCmd: 'python -m build && python -m twine check dist/*'
                }
              ],
              [
                '@semantic-release/git',
                {
                  assets: ['VERSION', 'VERSION.meta', 'CHANGELOG.md'],
                  message: 'chore(release): \${nextRelease.version} [skip ci]\\n\\n\${nextRelease.notes}'
                }
              ],
              '@semantic-release/github'
            ]
          }
          EOF
          
          npx semantic-release

      - name: Cleanup Old Tags (main branch only)
        if: github.ref == 'refs/heads/main'
        run: python scripts/tag_cleanup.py --execute
```

**Benefits**:

- **Preserves emergent versioning**: Branch patterns automatically determine version strategy
- **Eliminates infinite loops**: Built-in semantic-release loop prevention + [skip ci]
- **Atomic operations**: Single workflow handles entire version lifecycle
- **GitHub App authentication**: Bypasses branch protection cleanly
- **Industry standard**: Uses proven semantic-release patterns
- **Fail-safe**: Comprehensive error handling and rollback

### Option 2: Hybrid Release Please + Custom Logic

**Architecture**: Release Please for main releases + custom logic for development branches

```yaml
name: Development Branch Versioning
on:
  push:
    branches: [dev, 'feat/*', 'fix/*']

jobs:
  dev-versioning:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    
    steps:
      - name: Generate GitHub App Token
        id: generate-token
        uses: tibdex/github-app-token@v2
        with:
          app_id: ${{ secrets.HATCHLING_APP_ID }}
          private_key: ${{ secrets.HATCHLING_APP_PRIVATE_KEY }}

      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ steps.generate-token.outputs.token }}

      - name: Update Development Version
        run: |
          # Custom logic preserving current branch-based versioning
          python scripts/version_manager.py --update-for-branch ${{ github.ref_name }}
          
          git config --local user.email "hatchling-bot@users.noreply.github.com"
          git config --local user.name "Hatchling Bot"
          git add VERSION VERSION.meta
          git commit -m "chore: update version for ${{ github.ref_name }} [skip ci]" || exit 0
          git push
```

```yaml
name: Main Branch Release Please
on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          token: ${{ secrets.GITHUB_APP_TOKEN }}
          release-type: python
          
      - uses: actions/checkout@v4
        if: ${{ steps.release.outputs.release_created }}
        
      - name: Build and Publish
        if: ${{ steps.release.outputs.release_created }}
        run: |
          python -m pip install --upgrade pip build twine
          python -m build
          python -m twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### Option 3: Custom Conventional Commit Automation

**Architecture**: Custom implementation using conventional commits with branch pattern enhancement

```yaml
name: Branch-Aware Conventional Versioning
on:
  push:
    branches: [main, dev, 'feat/*', 'fix/*']

jobs:
  version:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]') && github.actor != 'github-actions[bot]'"
    
    steps:
      - name: Generate GitHub App Token
        id: generate-token
        uses: tibdex/github-app-token@v2
        with:
          app_id: ${{ secrets.HATCHLING_APP_ID }}
          private_key: ${{ secrets.HATCHLING_APP_PRIVATE_KEY }}

      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ steps.generate-token.outputs.token }}

      - name: Analyze Commits and Determine Version
        id: version
        run: |
          # Enhanced version_manager.py with conventional commit parsing
          python scripts/enhanced_version_manager.py \
            --branch ${{ github.ref_name }} \
            --analyze-commits \
            --output-github-actions
          
      - name: Update Version Files
        if: steps.version.outputs.should_release == 'true'
        run: |
          python scripts/enhanced_version_manager.py \
            --branch ${{ github.ref_name }} \
            --set-version ${{ steps.version.outputs.next_version }}
            
      - name: Build and Test
        if: steps.version.outputs.should_release == 'true'
        run: |
          python -m pip install --upgrade pip build
          python -m build
          python -m pytest tests/

      - name: Commit and Tag
        if: steps.version.outputs.should_release == 'true'
        run: |
          git config --local user.email "hatchling-bot@users.noreply.github.com"
          git config --local user.name "Hatchling Bot"
          
          git add VERSION VERSION.meta
          git commit -m "chore(release): ${{ steps.version.outputs.next_version }} [skip ci]"
          
          if [[ "${{ github.ref_name }}" == "main" ]]; then
            git tag -a "v${{ steps.version.outputs.next_version }}" -m "Release v${{ steps.version.outputs.next_version }}"
            git push origin "v${{ steps.version.outputs.next_version }}"
          fi
          
          git push
```

## Implementation Roadmap

### Phase 1: Immediate Stabilization (Week 1)

1. **DISABLE** `auto_merge_version_bump.yml` to prevent infinite loops
2. **CREATE** GitHub App with proper permissions
3. **IMPLEMENT** Option 1 (Enhanced Semantic Release) in development environment
4. **TEST** thoroughly with all branch patterns

### Phase 2: Migration (Week 2-3)

1. **DEPLOY** new workflow to production
2. **MONITOR** for 1 week with existing workflows disabled
3. **VALIDATE** version generation matches expected patterns
4. **REMOVE** deprecated workflows once stable

### Phase 3: Enhancement (Month 2)

1. **ADD** advanced features (changelog generation, release notes)
2. **IMPLEMENT** comprehensive monitoring and alerting
3. **OPTIMIZE** performance and reliability
4. **DOCUMENT** new workflow for team

## Loop Prevention Strategies

### 1. Multi-Layer Protection

```yaml
# Workflow level
if: "!contains(github.event.head_commit.message, '[skip ci]') && github.actor != 'github-actions[bot]'"

# Commit level
git commit -m "chore(release): ${version} [skip ci]"

# Path-based (if needed)
on:
  push:
    paths-ignore:
      - 'VERSION'
      - 'VERSION.meta'
```

### 2. Workflow State Validation

```yaml
- name: Check for concurrent workflows
  run: |
    RUNNING=$(gh run list --workflow="${{ github.workflow }}" --status=in_progress --json databaseId --jq length)
    if [ "$RUNNING" -gt 1 ]; then
      echo "Another workflow is running, exiting gracefully"
      exit 0
    fi
```

### 3. Branch-Specific Logic

```yaml
- name: Validate branch for release
  run: |
    if [[ "${{ github.ref_name }}" =~ ^(main|dev|feat/|fix/).*$ ]]; then
      echo "Valid branch for versioning"
    else
      echo "Skipping versioning for branch: ${{ github.ref_name }}"
      exit 0
    fi
```

## Error Handling and Recovery

### 1. Atomic Operations with Rollback

```yaml
- name: Version update with rollback
  run: |
    # Create backup
    cp VERSION VERSION.backup
    cp VERSION.meta VERSION.meta.backup
    
    # Attempt update
    if ! python scripts/version_manager.py --update; then
      # Restore on failure
      mv VERSION.backup VERSION
      mv VERSION.meta.backup VERSION.meta
      echo "Version update failed, restored backup"
      exit 1
    fi
    
    # Clean up on success
    rm -f *.backup
```

### 2. Comprehensive Monitoring

```yaml
- name: Report status
  if: always()
  run: |
    if [[ "${{ job.status }}" == "failure" ]]; then
      gh issue create \
        --title "Automated versioning failed on ${{ github.ref_name }}" \
        --body "Workflow run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
    fi
```

## Migration Strategy

### Step 1: GitHub App Setup

1. Create GitHub App with permissions:
   - Contents: Read & Write
   - Metadata: Read
   - Pull Requests: Write (if using Option 2)
2. Install app on repository
3. Add app to branch protection bypass list
4. Store app credentials as repository secrets

### Step 2: Workflow Implementation

1. Implement chosen option in `.github/workflows/`
2. Test in development environment
3. Gradually migrate branch by branch
4. Monitor and adjust as needed

### Step 3: Legacy Cleanup

1. Disable old workflows
2. Remove deprecated files
3. Update documentation
4. Train team on new process

## Enhanced Version Manager Implementation

To support the new workflows, the existing `version_manager.py` needs enhancement to work with conventional commits and semantic-release patterns:

```python
# Enhanced version_manager.py additions
import re
from typing import Dict, List, Tuple

class ConventionalCommitAnalyzer:
    """Analyzes conventional commits to determine version bumps"""

    COMMIT_PATTERN = re.compile(
        r'^(?P<type>\w+)(?:\((?P<scope>[\w\-]+)\))?(?P<breaking>!)?: (?P<description>.+)$'
    )

    VERSION_BUMPS = {
        'feat': 'minor',
        'fix': 'patch',
        'perf': 'patch',
        'revert': 'patch',
        'docs': None,
        'style': None,
        'refactor': None,
        'test': None,
        'build': None,
        'ci': None,
        'chore': None
    }

    def analyze_commits_since_last_release(self, branch: str) -> str:
        """Determine version bump type based on commits since last release"""
        commits = self._get_commits_since_last_release(branch)

        has_breaking = False
        has_feature = False
        has_fix = False

        for commit in commits:
            match = self.COMMIT_PATTERN.match(commit.message.split('\n')[0])
            if not match:
                continue

            commit_type = match.group('type')
            is_breaking = match.group('breaking') == '!' or 'BREAKING CHANGE' in commit.message

            if is_breaking:
                has_breaking = True
            elif commit_type == 'feat':
                has_feature = True
            elif commit_type in ['fix', 'perf']:
                has_fix = True

        if has_breaking:
            return 'major'
        elif has_feature:
            return 'minor'
        elif has_fix:
            return 'patch'
        else:
            return None  # No releasable changes

def enhanced_version_manager_cli():
    """Enhanced CLI for integration with semantic-release"""
    parser = argparse.ArgumentParser(description='Enhanced Version Manager')
    parser.add_argument('--analyze-commits', action='store_true',
                       help='Analyze commits to determine version bump')
    parser.add_argument('--set-version', type=str,
                       help='Set specific version (for semantic-release integration)')
    parser.add_argument('--output-github-actions', action='store_true',
                       help='Output GitHub Actions compatible variables')

    args = parser.parse_args()

    if args.analyze_commits:
        analyzer = ConventionalCommitAnalyzer()
        bump_type = analyzer.analyze_commits_since_last_release(args.branch)

        if args.output_github_actions:
            print(f"should_release={'true' if bump_type else 'false'}")
            if bump_type:
                current_version = get_current_version()
                next_version = calculate_next_version(current_version, bump_type, args.branch)
                print(f"next_version={next_version}")
```

## Real-World Implementation Examples

### Example 1: Feature Branch Workflow

**Developer Action**:

```bash
git checkout -b feat/user-authentication
# ... make changes ...
git commit -m "feat: add user authentication system"
git push origin feat/user-authentication
```

**Automated Result**:

- Workflow triggers on `feat/user-authentication` branch
- Semantic-release analyzes commit: `feat:` → minor version bump
- Version becomes: `1.2.0-user-authentication-dev.1`
- VERSION files updated automatically
- No manual intervention required

### Example 2: Bug Fix Workflow

**Developer Action**:

```bash
git checkout -b fix/login-validation
git commit -m "fix: resolve login validation issue"
git push origin fix/login-validation
```

**Automated Result**:

- Workflow triggers on `fix/login-validation` branch
- Semantic-release analyzes commit: `fix:` → patch version bump
- Version becomes: `1.1.1-login-validation-fix.1`
- Automatic testing and validation
- Clean integration with existing patterns

### Example 3: Main Branch Release

**Developer Action**:

```bash
git checkout main
git merge feat/user-authentication
git push origin main
```

**Automated Result**:

- Workflow triggers on main branch
- Analyzes all commits since last release
- Determines version: `1.2.0` (clean release)
- Creates git tag: `v1.2.0`
- Generates GitHub release with changelog
- Updates VERSION files with clean version

## Advanced Configuration Options

### Semantic Release Configuration

```javascript
// .releaserc.js - Advanced configuration
module.exports = {
  branches: [
    'main',
    { name: 'dev', prerelease: 'dev' },
    { name: 'feat/*', prerelease: '${name.replace(/^feat\\//g, "")}-dev' },
    { name: 'fix/*', prerelease: '${name.replace(/^fix\\//g, "")}-fix' }
  ],
  plugins: [
    [
      '@semantic-release/commit-analyzer',
      {
        preset: 'conventionalcommits',
        releaseRules: [
          { type: 'feat', release: 'minor' },
          { type: 'fix', release: 'patch' },
          { type: 'perf', release: 'patch' },
          { type: 'revert', release: 'patch' },
          { type: 'docs', release: false },
          { type: 'style', release: false },
          { type: 'chore', release: false },
          { type: 'refactor', release: false },
          { type: 'test', release: false },
          { type: 'build', release: false },
          { type: 'ci', release: false }
        ]
      }
    ],
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'conventionalcommits',
        presetConfig: {
          types: [
            { type: 'feat', section: 'Features' },
            { type: 'fix', section: 'Bug Fixes' },
            { type: 'perf', section: 'Performance Improvements' },
            { type: 'revert', section: 'Reverts' },
            { type: 'docs', section: 'Documentation', hidden: true },
            { type: 'style', section: 'Styles', hidden: true },
            { type: 'chore', section: 'Miscellaneous Chores', hidden: true },
            { type: 'refactor', section: 'Code Refactoring', hidden: true },
            { type: 'test', section: 'Tests', hidden: true },
            { type: 'build', section: 'Build System', hidden: true },
            { type: 'ci', section: 'Continuous Integration', hidden: true }
          ]
        }
      }
    ],
    '@semantic-release/changelog',
    [
      '@semantic-release/exec',
      {
        prepareCmd: 'python scripts/enhanced_version_manager.py --set-version ${nextRelease.version}',
        publishCmd: 'python -m build && python -m twine check dist/*'
      }
    ],
    [
      '@semantic-release/git',
      {
        assets: ['VERSION', 'VERSION.meta', 'CHANGELOG.md'],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ],
    [
      '@semantic-release/github',
      {
        successComment: false,
        failComment: false,
        releasedLabels: ['released']
      }
    ]
  ]
}
```

### GitHub App Permissions Checklist

**Required Permissions**:

- ✅ Contents: Read & Write (for commits and tags)
- ✅ Metadata: Read (for repository access)
- ✅ Actions: Read (for workflow status)
- ✅ Pull Requests: Write (if using PR-based option)
- ✅ Issues: Write (for error reporting)

**Branch Protection Configuration**:

- ✅ Add GitHub App to bypass list
- ✅ Require status checks: `Automated Versioning`
- ✅ Require up-to-date branches: true
- ✅ Restrict pushes: true
- ✅ Allow bypass for: [Your GitHub App]

## Monitoring and Observability

### Workflow Monitoring

```yaml
- name: Report Workflow Metrics
  if: always()
  run: |
    echo "::notice title=Workflow Status::Status: ${{ job.status }}"
    echo "::notice title=Branch::${{ github.ref_name }}"
    echo "::notice title=Commit::${{ github.sha }}"

    if [[ "${{ job.status }}" == "success" ]]; then
      echo "::notice title=Version::Successfully processed version update"
    else
      echo "::error title=Failure::Workflow failed - check logs"
    fi
```

### Error Alerting

```yaml
- name: Create Issue on Failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `Automated versioning failed on ${context.ref}`,
        body: `
        ## Workflow Failure Report

        **Branch**: ${context.ref}
        **Commit**: ${context.sha}
        **Run**: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}
        **Actor**: ${context.actor}

        Please investigate and resolve the issue.
        `,
        labels: ['bug', 'automation', 'versioning']
      })
```

## Performance Optimizations

### Caching Strategy

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: Cache semantic-release
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### Conditional Execution

```yaml
- name: Check if version update needed
  id: check
  run: |
    if git log --oneline -1 | grep -q '\[skip ci\]'; then
      echo "skip=true" >> $GITHUB_OUTPUT
    else
      echo "skip=false" >> $GITHUB_OUTPUT
    fi

- name: Run versioning
  if: steps.check.outputs.skip == 'false'
  # ... rest of workflow
```

## Conclusion

The **Enhanced Semantic Release** approach (Option 1) provides the optimal balance of:

- **Preserving emergent versioning behavior** through branch pattern automation
- **Eliminating architectural issues** with proven industry-standard tools
- **Maintaining developer experience** with zero manual intervention required
- **Ensuring enterprise reliability** with comprehensive error handling

This solution transforms the current system from a custom, fragile implementation into a robust, industry-standard automated versioning system while preserving the core value proposition that makes it valuable to developers.

**Recommendation**: Implement Option 1 immediately to resolve critical stability issues while maintaining the automatic, hands-off versioning behavior that developers rely on.

**Next Steps**:

1. Create GitHub App and configure permissions
2. Implement enhanced version manager with conventional commit support
3. Deploy new workflow with comprehensive testing
4. Monitor and iterate based on real-world usage
5. Remove legacy workflows once stable
