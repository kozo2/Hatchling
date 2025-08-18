# GitHub-Specific Solutions Report: Automated Workflows with Branch Protection

## Executive Summary

This report provides comprehensive guidance on implementing automated versioning workflows while maintaining GitHub branch protection rules. It covers GitHub Apps, service accounts, organization-level configurations, and specific GitHub features that enable secure automation.

## GitHub Branch Protection Overview

### Core Protection Features

- **Pull Request Requirements**: Enforce code review before merging
- **Status Check Requirements**: Require CI/CD checks to pass
- **Conversation Resolution**: Ensure all comments are addressed
- **Signed Commits**: Require cryptographic verification
- **Linear History**: Prevent merge commits
- **Merge Queue**: Automated merge management
- **Deployment Requirements**: Require successful deployments
- **Branch Locking**: Make branches read-only
- **Push Restrictions**: Limit who can push directly

### Bypass Mechanisms

1. **Administrator Override**: Repository admins can bypass by default
2. **Custom Roles**: Organization-level roles with bypass permissions
3. **GitHub Apps**: Applications added to bypass list
4. **Service Accounts**: Dedicated automation accounts

## GitHub Apps: The Preferred Solution

### Why GitHub Apps Are Recommended

**Security Benefits**:

- Fine-grained permissions (repository-specific)
- No personal access token exposure
- Automatic token rotation
- Audit trail for all actions
- Organization-level management

**Operational Benefits**:

- Can be added to branch protection bypass lists
- Works across multiple repositories
- Centralized credential management
- No dependency on individual user accounts

### GitHub App Setup Process

#### Step 1: Create GitHub App

1. **Navigate to GitHub Settings**:
   - Organization: `Settings` → `Developer settings` → `GitHub Apps`
   - Personal: `Settings` → `Developer settings` → `GitHub Apps`

2. **Basic Information**:

   ```
   App Name: [Organization]-Versioning-Bot
   Homepage URL: https://github.com/[org]/[repo]
   Description: Automated versioning and release management
   ```

3. **Webhook Configuration**:

   ```
   Webhook URL: [Optional - leave blank for simple automation]
   Webhook Secret: [Optional]
   SSL Verification: Enabled
   ```

#### Step 2: Configure Permissions

**Repository Permissions**:

```
Contents: Read & Write (required for commits/tags)
Metadata: Read (required for basic repository access)
Pull Requests: Write (if using PR-based workflow)
Actions: Read (if triggering workflows)
Checks: Write (if updating status checks)
```

**Organization Permissions**:

```
Members: Read (if checking organization membership)
```

**Account Permissions**:

```
Email addresses: Read (if needed for commit attribution)
```

#### Step 3: Generate Private Key

1. Scroll to "Private keys" section
2. Click "Generate a private key"
3. Download and securely store the `.pem` file
4. Note the App ID from the app settings

#### Step 4: Install App

1. Go to "Install App" tab
2. Select target organization/repositories
3. Choose "All repositories" or "Selected repositories"
4. Complete installation

### GitHub App Authentication in Workflows

#### Using tibdex/github-app-token Action

```yaml
name: Automated Versioning
on:
  push:
    branches: [main, dev]

jobs:
  version-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate GitHub App Token
        id: generate-token
        uses: tibdex/github-app-token@v2
        with:
          app_id: ${{ secrets.APP_ID }}
          private_key: ${{ secrets.APP_PRIVATE_KEY }}

      - name: Configure Git
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "Versioning Bot"

      - name: Update Version and Commit
        run: |
          # Your versioning logic here
          python scripts/version_manager.py --update-for-branch ${{ github.ref_name }}
          git add VERSION VERSION.meta
          git commit -m "chore: update version files [skip ci]"
          git push
        env:
          GITHUB_TOKEN: ${{ steps.generate-token.outputs.token }}
```

#### Storing Secrets

1. **Repository Secrets**:
   - `Settings` → `Secrets and variables` → `Actions`
   - Add `APP_ID` (GitHub App ID)
   - Add `APP_PRIVATE_KEY` (contents of .pem file)

2. **Organization Secrets** (for multiple repositories):
   - Organization `Settings` → `Secrets and variables` → `Actions`
   - Set repository access permissions

### Adding GitHub App to Branch Protection Bypass

#### Repository Level

1. Navigate to repository `Settings` → `Branches`
2. Edit existing branch protection rule or create new one
3. Scroll to "Restrict pushes that create files"
4. In "Bypass restrictions" section:
   - Check "Apps" checkbox
   - Select your GitHub App from dropdown
5. Save changes

#### Organization Level (Enterprise)

For GitHub Enterprise Cloud organizations:

1. Organization `Settings` → `Repository defaults`
2. Configure default branch protection rules
3. Add GitHub App to bypass list
4. Apply to new repositories automatically

## Alternative Authentication Methods

### 1. Fine-Grained Personal Access Tokens (Beta)

**Setup**:

```
Token Name: Versioning Automation
Expiration: 1 year (maximum)
Resource Owner: [Organization]
Repository Access: Selected repositories
Permissions:
  - Contents: Write
  - Metadata: Read
  - Pull Requests: Write (if needed)
```

**Usage**:

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.FINE_GRAINED_PAT }}
```

**Limitations**:

- Still in beta
- Requires manual token rotation
- Tied to user account
- Limited organization support

### 2. Deploy Keys (Read-Only Alternative)

**Use Case**: For read-only operations or when combined with other auth methods

**Setup**:

1. Generate SSH key pair: `ssh-keygen -t ed25519 -C "deploy-key"`
2. Add public key to repository `Settings` → `Deploy keys`
3. Store private key as repository secret

**Limitations**:

- Read-only by default
- Repository-specific
- Cannot bypass branch protection

### 3. Service Account with PAT (Legacy)

**Setup**:

1. Create dedicated GitHub user account
2. Add to organization with appropriate permissions
3. Generate classic PAT with required scopes
4. Add to branch protection bypass list

**Disadvantages**:

- Requires paid seat in organization
- Manual token rotation
- Security risk if token is compromised
- Tied to user account lifecycle

## Branch Protection Configuration Best Practices

### Recommended Settings for Automated Versioning

```yaml
# Example branch protection configuration
Branch Protection Rule: main
Settings:
  ✅ Require pull request reviews: false (for direct automation)
  ✅ Require status checks: true
    - Required checks: ["test", "build", "lint"]
    - Require up-to-date branches: true
  ❌ Require conversation resolution: false
  ✅ Require signed commits: true (recommended)
  ❌ Require linear history: false (allows merge commits)
  ❌ Require merge queue: false (unless high-traffic)
  ❌ Lock branch: false
  ❌ Do not allow bypassing: false (allow bypass for automation)
  ✅ Restrict pushes: true
    - Bypass restrictions: [Your GitHub App]
  ❌ Allow force pushes: false
  ❌ Allow deletions: false
```

### Development Branch Configuration

```yaml
Branch Protection Rule: dev
Settings:
  ❌ Require pull request reviews: false
  ✅ Require status checks: true
    - Required checks: ["test", "build"]
    - Require up-to-date branches: false
  ❌ Require conversation resolution: false
  ❌ Require signed commits: false
  ❌ Require linear history: false
  ❌ Lock branch: false
  ❌ Do not allow bypassing: false
  ✅ Restrict pushes: true
    - Bypass restrictions: [Your GitHub App, Developers Team]
  ❌ Allow force pushes: false
  ❌ Allow deletions: false
```

## Advanced GitHub Features

### 1. Repository Rulesets (New Alternative)

**Benefits over Branch Protection**:

- More flexible targeting
- Better inheritance model
- Improved API support
- Organization-level management

**Configuration**:

```yaml
# .github/rulesets/main-protection.yml
name: Main Branch Protection
target: branch
enforcement: active
conditions:
  ref_name:
    include: ["refs/heads/main"]
rules:
  - type: required_status_checks
    parameters:
      required_status_checks:
        - context: "test"
        - context: "build"
  - type: restrict_pushes
    parameters:
      restrict_pushes: true
bypass_actors:
  - actor_id: [GitHub App ID]
    actor_type: Integration
    bypass_mode: always
```

### 2. Merge Queues

**Use Case**: High-traffic repositories with frequent merges

**Benefits**:

- Automatic conflict resolution
- Parallel testing
- Reduced developer wait time
- Maintains branch protection

**Configuration**:

```yaml
# In branch protection settings
Require merge queue: true
Merge method: merge (or squash/rebase)
Build concurrency: 5
Merge timeout: 60 minutes
```

### 3. Required Deployments

**Use Case**: Ensure staging deployment before production merge

**Configuration**:

```yaml
Required deployments before merging:
  - staging
  - integration-tests
```

## Security Considerations

### 1. Principle of Least Privilege

**GitHub App Permissions**:

- Only grant minimum required permissions
- Use repository-specific installations when possible
- Regular permission audits

**Branch Protection**:

- Limit bypass actors to essential automation only
- Use separate apps for different functions
- Monitor bypass usage

### 2. Audit and Monitoring

**GitHub Audit Log**:

- Monitor app token usage
- Track bypass events
- Review permission changes

**Workflow Monitoring**:

```yaml
- name: Audit Workflow Run
  run: |
    echo "Workflow: ${{ github.workflow }}"
    echo "Actor: ${{ github.actor }}"
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
```

### 3. Secret Management

**Best Practices**:

- Use GitHub App tokens over PATs
- Rotate secrets regularly
- Use organization-level secrets for shared resources
- Implement secret scanning

**Secret Rotation**:

```yaml
# Automated secret rotation workflow
name: Rotate GitHub App Key
on:
  schedule:
    - cron: '0 0 1 */3 *'  # Quarterly
jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - name: Generate New Key
        # Implementation depends on your key management system
```

## Troubleshooting Common Issues

### 1. "GH006: Protected branch update failed"

**Cause**: GitHub App not in bypass list or insufficient permissions

**Solution**:

1. Verify app is added to branch protection bypass
2. Check app has "Contents: Write" permission
3. Ensure app is installed on repository

### 2. "Resource not accessible by integration"

**Cause**: Missing permissions or incorrect token scope

**Solution**:

1. Review GitHub App permissions
2. Verify token generation in workflow
3. Check repository installation

### 3. Workflow Infinite Loops

**Cause**: Workflow triggering itself

**Solution**:

```yaml
# Use [skip ci] in commit messages
git commit -m "chore: update version [skip ci]"

# Or use conditional triggers
on:
  push:
    branches: [main]
    paths-ignore:
      - 'VERSION'
      - 'VERSION.meta'
```

## Recommendations for Hatchling

### Immediate Implementation

1. **Create GitHub App**:
   - Name: "Hatchling-Versioning-Bot"
   - Permissions: Contents (Write), Metadata (Read)
   - Install on Hatchling repository

2. **Update Branch Protection**:
   - Add GitHub App to bypass list for main branch
   - Maintain status check requirements
   - Remove complex workflow chains

3. **Simplify Workflows**:
   - Use direct commits instead of PR-based flow
   - Implement proper [skip ci] usage
   - Add fail-safe mechanisms

### Long-term Strategy

1. **Organization-wide Deployment**:
   - Install app across all repositories
   - Standardize branch protection rules
   - Implement centralized secret management

2. **Advanced Features**:
   - Evaluate repository rulesets
   - Consider merge queues for high-traffic repos
   - Implement comprehensive audit logging

## Conclusion

GitHub Apps provide the most secure and scalable solution for automated versioning in protected repositories. The combination of fine-grained permissions, bypass capabilities, and centralized management makes them superior to alternative authentication methods.

**Key Success Factors**:

1. Proper GitHub App configuration with minimal permissions
2. Correct branch protection bypass setup
3. Simplified workflow architecture
4. Comprehensive monitoring and auditing

**Grade**: GitHub's native solutions are mature and well-supported (A)
**Recommendation**: Implement GitHub App-based authentication immediately
