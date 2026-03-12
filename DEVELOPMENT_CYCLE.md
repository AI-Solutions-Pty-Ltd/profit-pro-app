# Development Cycle & Git Workflow

This document outlines the development workflow and branching strategy for the Profit Pro application.

## Branch Strategy

We follow a **Git Flow** inspired workflow with the following branches:

```
main (production) ← staging ← development ← feat/*
```

### Branch Hierarchy

| Branch        | Purpose                                     | Protected | Deploy To               |
| ------------- | ------------------------------------------- | --------- | ----------------------- |
| `main`        | **Source of truth** - Production-ready code | ✅ Yes    | Production              |
| `staging`     | Pre-production testing and QA               | ✅ Yes    | Staging Environment     |
| `development` | Integration branch for features             | ❌ No     | Development Environment |
| `feat/*`      | Individual feature development              | ❌ No     | Local/Dev               |

## Branch Descriptions

### `main` - Production Branch

- **Source of truth** for the entire project
- Contains only production-ready, tested code
- All code must pass through `staging` before merging to `main`
- Tagged with version numbers (e.g., `v1.0.0`, `v1.1.0`)
- **Never commit directly to this branch**
- Requires pull request approval from team lead/senior developer
- Automatically deploys to production environment

### `staging` - Pre-Production Branch

- Mirrors production environment for final testing
- QA and user acceptance testing (UAT) happens here
- Merges from `development` after feature integration
- Bug fixes found in staging are fixed in `development` and merged back
- Requires pull request approval
- Automatically deploys to staging environment

### `development` - Integration Branch

- Main integration branch for all features
- Features are merged here after completion
- Continuous integration tests run on every merge
- Should always be in a deployable state
- Automatically deploys to development environment
- Requires pull request approval

### `feat/*` - Feature Branches

- Created from `development` for each new feature/task
- Naming convention: `feat/feature-name` or `feat/TICKET-123-description`
- Examples:
  - `feat/payment-certificate-export`
  - `feat/ledger-ajax-delete`
  - `feat/BOQ-456-retention-calculation`
- Deleted after successful merge to `development`

## Development Workflow

### 1. Starting a New Feature

```bash
# Ensure you're on the latest development branch
git checkout development
git pull origin development

# Create a new feature branch
git checkout -b feat/your-feature-name

# Start coding!
```

### 2. Working on Your Feature

```bash
# Make changes and commit regularly
git add .
git commit -m "feat: add payment certificate export functionality"

# Push to remote regularly to backup your work
git push origin feat/your-feature-name
```

### 3. Keeping Your Feature Branch Updated

```bash
# Regularly sync with development to avoid conflicts
git checkout development
git pull origin development

git checkout feat/your-feature-name
git rebase development
# Or use merge if you prefer
git merge development
```

### 4. Completing Your Feature

```bash
# Ensure all tests pass
.venv\Scripts\python.exe -m pytest

# Ensure code is formatted and linted
.venv\Scripts\python.exe -m ruff format .
.venv\Scripts\python.exe -m ruff check .

# Push final changes
git push origin feat/your-feature-name

# Create Pull Request to development branch
```

### 5. Code Review & Merge to Development

1. Create a **Pull Request** from `feat/your-feature-name` → `development`
2. Fill out the PR template with:
   - Description of changes
   - Testing performed
   - Screenshots (if UI changes)
   - Related tickets/issues
3. Request review from team members
4. Address review comments
5. Once approved, **squash and merge** into `development`
6. Delete the feature branch

### 6. Promoting to Staging

```bash
# After features are integrated and tested in development
git checkout staging
git pull origin staging

# Merge development into staging
git merge development

# Push to staging
git push origin staging

# This triggers deployment to staging environment
```

### 7. QA & Testing in Staging

- QA team tests features in staging environment
- UAT with stakeholders
- Bug fixes:
  - Create `fix/bug-name` branch from `development`
  - Fix the bug
  - Merge to `development`
  - Merge `development` to `staging` again

### 8. Production Release

```bash
# After successful staging testing
git checkout main
git pull origin main

# Merge staging into main
git merge staging

# Tag the release
git tag -a v1.2.0 -m "Release version 1.2.0"

# Push to production
git push origin main --tags

# This triggers deployment to production environment
```

## Commit Message Convention

We follow **Conventional Commits** for clear, semantic commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements

### Examples

```bash
git commit -m "feat(ledger): add AJAX delete for transactions"
git commit -m "fix(payment-cert): correct running balance calculation"
git commit -m "docs: update README with setup instructions"
git commit -m "refactor(models): extract transaction logic to utility function"
git commit -m "test(retention): add factory for retention transactions"
git commit -m "chore(deps): update django to 5.1.5"
```

## Pull Request Guidelines

### PR Title Format

```
[TYPE] Brief description of changes
```

Examples:

- `[FEAT] Add payment certificate PDF export`
- `[FIX] Resolve retention balance calculation error`
- `[REFACTOR] Extract ledger transaction list logic`

### PR Description Template

```markdown
## Description

Brief description of what this PR does.

## Changes Made

- Change 1
- Change 2
- Change 3

## Testing Performed

- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

## Screenshots (if applicable)

[Add screenshots here]

## Related Issues

Closes #123
Related to #456

## Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No breaking changes (or documented if necessary)
```

## Hotfix Workflow

For critical production bugs that need immediate fixing:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-name

# Fix the bug
# ... make changes ...

# Commit and push
git commit -m "fix: resolve critical payment calculation error"
git push origin hotfix/critical-bug-name

# Create PR to main (emergency approval)
# After merge to main, also merge to staging and development
git checkout staging
git merge main
git push origin staging

git checkout development
git merge main
git push origin development
```

## Environment-Specific Configuration

### Development Environment

- `DJANGO_SETTINGS_MODULE=settings.local`
- Debug mode enabled
- SQLite database
- Email backend: Console
- Auto-reload enabled

### Staging Environment

- `DJANGO_SETTINGS_MODULE=settings.prod`
- Debug mode disabled
- PostgreSQL database (production-like)
- Email backend: SMTP (test account)
- Mirrors production configuration

### Production Environment

- `DJANGO_SETTINGS_MODULE=settings.prod`
- Debug mode disabled
- PostgreSQL database
- Email backend: SMTP (production)
- Performance optimizations enabled
- Static files served via CDN/nginx

## CI/CD Pipeline

### On Push to Feature Branch

1. Run linting checks (ruff)
2. Run unit tests
3. Report coverage

### On PR to Development

1. Run full test suite
2. Check code coverage (minimum 80%)
3. Run security checks
4. Build check

### On Merge to Development

1. Run full test suite
2. Deploy to development environment
3. Run integration tests
4. Notify team in Slack/Teams

### On Merge to Staging

1. Run full test suite
2. Deploy to staging environment
3. Run smoke tests
4. Notify QA team

### On Merge to Main

1. Run full test suite
2. Create release notes
3. Deploy to production
4. Run smoke tests
5. Monitor error tracking
6. Notify team of successful deployment

## Best Practices

### Do's ✅

- Always create feature branches from `development`
- Write descriptive commit messages
- Keep commits small and focused
- Write tests for new features
- Update documentation
- Request code reviews
- Test locally before pushing
- Keep feature branches short-lived (< 1 week)
- Rebase/merge `development` into your branch regularly
- Delete merged feature branches

### Don'ts ❌

- Never commit directly to `main`, `staging`, or `development`
- Don't push broken code
- Don't commit secrets or sensitive data
- Don't merge without code review
- Don't create long-living feature branches
- Don't skip tests
- Don't force push to shared branches
- Don't merge your own PRs (unless emergency)

## Versioning

We follow **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes (v2.0.0)
- **MINOR**: New features, backward compatible (v1.1.0)
- **PATCH**: Bug fixes, backward compatible (v1.0.1)

### Examples

- `v1.0.0` - Initial release
- `v1.1.0` - Added payment certificate export feature
- `v1.1.1` - Fixed retention calculation bug
- `v2.0.0` - Redesigned ledger system (breaking change)

## Release Process

1. **Feature Freeze**: No new features merged to `development`
2. **Merge to Staging**: `development` → `staging`
3. **QA Testing**: 2-3 days of testing in staging
4. **Bug Fixes**: Fix any issues found, merge back to `development`, then `staging`
5. **Release Approval**: Team lead approves release
6. **Merge to Main**: `staging` → `main`
7. **Tag Release**: Create version tag
8. **Deploy**: Automatic deployment to production
9. **Monitor**: Watch error logs and metrics
10. **Release Notes**: Document changes for users

## Getting Help

- **Git Issues**: Ask in #dev-help channel
- **Merge Conflicts**: Pair with senior developer
- **CI/CD Failures**: Check build logs, ask DevOps team
- **Deployment Issues**: Contact DevOps immediately

## Quick Reference

```bash
# Start new feature
git checkout development && git pull && git checkout -b feat/my-feature

# Update feature branch
git checkout development && git pull && git checkout feat/my-feature && git rebase development

# Finish feature
git push origin feat/my-feature
# Then create PR on GitHub/GitLab

# Emergency hotfix
git checkout main && git pull && git checkout -b hotfix/critical-fix
```

---

**Remember**: `main` is the source of truth. All code flows through the pipeline: `feat/*` → `development` → `staging` → `main`
