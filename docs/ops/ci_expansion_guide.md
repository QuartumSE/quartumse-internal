# CI Matrix Expansion Guide

This guide explains how to expand the GitHub Actions CI matrix from the reduced configuration (Phase 1-2) to full multi-platform testing when the repository becomes public.

---

## Current State (Phase 1-2)

**Configuration:** Reduced matrix
**File:** `.github/workflows/ci.yml`
**Jobs:** 1 (Ubuntu + Python 3.11 only)
**Reason:** Private repository + cost optimization

```yaml
matrix:
  os: [ubuntu-latest]
  python-version: ["3.11"]
```

**What's tested:**
- ✅ Code formatting (black, ruff)
- ✅ Type checking (mypy)
- ✅ Core unit tests on Python 3.11
- ✅ Coverage reporting to Codecov

**What's NOT tested:**
- ❌ Windows compatibility
- ❌ macOS compatibility
- ❌ Python 3.10, 3.12, 3.13 edge cases

---

## When to Expand

**Trigger:** Repository becomes public (planned for Phase 3)

**Phase 3 Checklist Item:**
- Internal validation complete
- SSR ≥ 1.5× achieved
- Ready for external contributors
- No secrets in Git history
- **→ Make repo public**
- **→ Expand CI matrix**

**Why wait until Phase 3:**
- Phase 1-2: Private repo, cost-sensitive, core team only
- Phase 3+: Public repo, unlimited Actions, external contributors need cross-platform validation

---

## Expansion Steps

### Step 1: Verify Repository is Public

**Check visibility:**
```bash
# Visit repo settings
open https://github.com/QuartumSE/quartumse/settings

# Or check with gh CLI
gh repo view QuartumSE/quartumse --json visibility -q .visibility
# Should output: "public"
```

**Confirm unlimited Actions:**
- Go to: https://github.com/settings/billing
- Public repos show: "GitHub Actions: Unlimited" ✅

---

### Step 2: Edit CI Workflow

**File:** `.github/workflows/ci.yml`

**Find the matrix section (around line 14):**

```yaml
matrix:
  # REDUCED MATRIX: Keeping private repo during Phase 1-2
  # ...
  os: [ubuntu-latest]
  python-version: ["3.11"]
  #
  # EXPAND WHEN REPO GOES PUBLIC (Phase 3+):
  # ...
```

**Replace with full matrix:**

```yaml
matrix:
  os: [ubuntu-latest, macos-latest, windows-latest]
  python-version: ["3.10", "3.11", "3.12", "3.13"]
```

**Remove all the comment blocks** about reduced/expanded matrix.

---

### Step 3: Test the Expansion

**Create a test PR:**

```bash
# Create a branch
git checkout -b ci/expand-matrix

# Edit .github/workflows/ci.yml (apply Step 2 changes)

# Commit
git add .github/workflows/ci.yml
git commit -m "Expand CI matrix to full platform coverage

Repository is now public, enabling full cross-platform testing:
- 3 operating systems (Ubuntu, macOS, Windows)
- 4 Python versions (3.10, 3.11, 3.12, 3.13)
- Total: 12 test jobs per run

This provides comprehensive validation for external contributors
and ensures QuartumSE works across all supported environments."

# Push and create PR
git push -u origin ci/expand-matrix
gh pr create --title "Expand CI matrix for public repo" --body "Restores full cross-platform testing now that repo is public. See docs/ops/ci_expansion_guide.md"
```

**Watch the PR checks:**
- All 12 jobs should run
- Expect some Windows/macOS-specific issues initially
- Fix any platform-specific failures before merging

---

### Step 4: Fix Platform-Specific Issues

Common issues when expanding to full matrix:

#### Windows Path Issues
```python
# Before (Unix-only)
path = "data/manifests/file.json"

# After (cross-platform)
from pathlib import Path
path = Path("data") / "manifests" / "file.json"
```

#### macOS Line Ending Issues
```bash
# In CI workflow, normalize line endings
- name: Normalize line endings (macOS)
  if: runner.os == 'macOS'
  run: |
    find . -name "*.py" -exec dos2unix {} \;
```

#### Python 3.13 Compatibility
```python
# Check for deprecated features removed in 3.13
# Update dependencies if needed
pip install --upgrade qiskit qiskit-aer
```

---

### Step 5: Update Documentation

**Update references mentioning reduced matrix:**

1. **CHANGELOG.md:**
   ```markdown
   ## [Unreleased]
   ### Changed
   - Expanded CI matrix to full platform coverage (12 jobs) now that repository is public
   ```

2. **README.md badges:**
   ```markdown
   [![CI](https://github.com/quartumse/quartumse/workflows/CI/badge.svg)](https://github.com/quartumse/quartumse/actions)
   ```
   Badge will now show "12 passing" instead of "1 passing"

3. **CONTRIBUTING.md:**
   Add note about cross-platform testing:
   ```markdown
   ## Testing

   Pull requests are tested on:
   - Ubuntu, macOS, Windows
   - Python 3.10, 3.11, 3.12, 3.13

   Ensure your changes work on all platforms before submitting.
   ```

---

### Step 6: Monitor Actions Usage

Even with unlimited minutes, monitor for efficiency:

```bash
# Check Actions usage
gh api /repos/QuartumSE/quartumse/actions/runs \
  --jq '.workflow_runs[] | select(.name=="CI") | {id, status, conclusion, duration: .run_duration_ms}'

# View workflow run times
gh run list --workflow=ci.yml --limit 10
```

**Optimization tips if runs are slow:**
- Use `fail-fast: true` to cancel remaining jobs on first failure
- Cache pip dependencies with `actions/cache`
- Run expensive checks (mypy, integration tests) only on one platform

---

## Rollback Procedure

If full matrix causes issues, temporarily rollback:

**Quick rollback:**
```yaml
matrix:
  os: [ubuntu-latest]  # Rollback to single platform
  python-version: ["3.11"]
```

**Fix issues offline:**
- Test problematic platforms locally
- Fix compatibility issues
- Re-expand when ready

---

## Expected Results

### Before Expansion (Current)
```
✅ test (ubuntu-latest, 3.11)
```
**Time:** ~3 minutes
**Coverage:** Core functionality only

### After Expansion (Phase 3+)
```
✅ test (ubuntu-latest, 3.10)
✅ test (ubuntu-latest, 3.11)
✅ test (ubuntu-latest, 3.12)
✅ test (ubuntu-latest, 3.13)
✅ test (macos-latest, 3.10)
✅ test (macos-latest, 3.11)
✅ test (macos-latest, 3.12)
✅ test (macos-latest, 3.13)
✅ test (windows-latest, 3.10)
✅ test (windows-latest, 3.11)
✅ test (windows-latest, 3.12)
✅ test (windows-latest, 3.13)
```
**Time:** ~8-10 minutes (parallel execution)
**Coverage:** Full cross-platform validation

---

## Validation Checklist

After expansion, verify:

- [ ] All 12 jobs complete successfully
- [ ] Coverage reports upload correctly (Ubuntu 3.11 job)
- [ ] No platform-specific test failures
- [ ] Codecov badge shows correct coverage
- [ ] CI badge shows "12 passing"
- [ ] PR checks show all jobs
- [ ] No excessive Actions usage warnings
- [ ] Windows path handling works
- [ ] macOS-specific issues resolved
- [ ] Python 3.10-3.13 all pass

---

## Cost Analysis

### Private Repo (Current)
```
Matrix: 1 job
Duration: 3 min
Cost per run: 3 minutes (Ubuntu 1×)
Monthly estimate: ~100-300 minutes
Status: Within 2,000 min free tier
```

### Public Repo (After Expansion)
```
Matrix: 12 jobs
Duration: 3-4 min per job (parallel)
Cost per run: 0 minutes (unlimited for public)
Monthly estimate: Unlimited ✅
Status: Free forever
```

**Key takeaway:** Expansion is cost-free once repo is public!

---

## Related Documentation

- [Phase 1 Task Checklist](../strategy/phase1_task_checklist.md)
- [Roadmap](../strategy/roadmap.md) - Phase 3 milestones
- [CI Workflow](.github/workflows/ci.yml) - Current configuration
- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)

---

## Questions?

**When should I expand?**
→ When repo becomes public (Phase 3+)

**Can I expand before repo is public?**
→ Not recommended (cost ~$20-50/month for private repos)

**What if some jobs fail after expansion?**
→ Normal! Fix platform-specific issues and re-run

**Do I need to change anything else?**
→ Just update docs mentioning "reduced matrix" or "Ubuntu only"

**How do I test locally before expanding?**
→ Use `tox` with multiple Python versions, test on VM for other OSes

---

**Last updated:** 2025-10-30
**Next review:** Phase 3 (Internal Validation) - Target Mar 2026
