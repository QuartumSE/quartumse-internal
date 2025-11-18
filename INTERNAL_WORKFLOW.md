# QuartumSE Internal Development Workflow

**Repository:** `QuartumSE-internal` (Private)  
**Purpose:** R&D, experiments, strategy, internal documentation

---

## Repository Structure

This is the **canonical development repository** for the QuartumSE team:

```
QuartumSE-internal/
├── src/quartumse/               # SDK source (synced to public)
├── tests/                       # Test suite (synced to public)
├── docs/
│   ├── api/                     # API docs (public)
│   ├── tutorials/               # Tutorials (public)
│   ├── how-to/                  # How-to guides (public)
│   ├── explanation/             # Theory docs (public)
│   ├── community/               # Community docs (public)
│   ├── reference/               # API reference (public)
│   ├── strategy/                # ⚠️ INTERNAL - Roadmaps, planning
│   ├── research/                # ⚠️ INTERNAL - Experiment results
│   └── ops/                     # ⚠️ INTERNAL - Runbooks
├── experiments/                 # ⚠️ INTERNAL - Research implementations
├── Research/                    # ⚠️ INTERNAL - Papers, analysis
├── templates/                   # ⚠️ INTERNAL - Document templates
├── SESSION_PROGRESS_*.md        # ⚠️ INTERNAL - Dev session logs
└── STRATEGIC_ANALYSIS.md        # ⚠️ INTERNAL - Strategy docs
```

---

## Two-Repo Workflow

### **QuartumSE-internal** (This Repo - Private)
- **Purpose:** R&D, experiments, strategy
- **Who works here:** Internal team only
- **What's here:** Everything (SDK + internal docs)
- **Workflow:**
  1. Develop features in `src/quartumse/`
  2. Run experiments in `experiments/`
  3. Document results in `docs/research/`
  4. Update strategy in `docs/strategy/`
  5. When ready → sync to public repo

### **QuartumSE** (Public Repo)
- **Purpose:** User-facing SDK and documentation
- **Who works here:** Public contributors + internal team
- **What's here:** SDK, tests, public docs, examples
- **Workflow:**
  1. Receive synced SDK updates from internal
  2. Users clone lean repo (no internal docs)
  3. External PRs reviewed and merged
  4. Backport public contributions to internal

---

## Syncing to Public Repo

When SDK changes are ready for release:

```bash
# From QuartumSE-internal, commit your changes
git add src/ tests/ docs/
git commit -m "feat: Add new shadow estimator feature"
git push

# Switch to public repo
# Stay in internal repo

# Run sync script
./sync-to-public.sh

# Review changes
git status
git diff

# Test
pytest tests/

# Commit and push
git add .
git commit -m "Sync: Add new shadow estimator feature

Synced from QuartumSE-internal commit abc1234

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## What Gets Synced

| Content | Synced? | Notes |
|---------|---------|-------|
| `src/quartumse/` | ✅ Yes | SDK source code |
| `tests/` | ✅ Yes | Full test suite |
| `docs/api/` | ✅ Yes | API reference |
| `docs/tutorials/` | ✅ Yes | User tutorials |
| `docs/how-to/` | ✅ Yes | How-to guides |
| `docs/explanation/` | ✅ Yes | Theory & concepts |
| `docs/community/` | ✅ Yes | Community docs |
| `docs/strategy/` | ❌ No | Internal planning |
| `docs/research/` | ❌ No | Experiment results |
| `docs/ops/` | ❌ No | Operational runbooks |
| `experiments/` | ❌ No | Research code |
| `SESSION_PROGRESS_*.md` | ❌ No | Dev logs |
| `README.md` | ❌ No | Different per repo |

---

## Development Guidelines

### Working on Features

1. **Develop internally first:**
   ```bash
   cd QuartumSE-internal
   # Make changes to src/quartumse/
   # Add tests to tests/
   # Update public docs if needed
   ```

2. **Test thoroughly:**
   ```bash
   pytest tests/
   mypy src/
   ruff check src/
   ```

3. **Document experiments:**
   ```bash
   # Add results to docs/research/experiments/
   # Update workstream overviews in docs/research/workflows/
   ```

4. **When stable → sync to public:**
   ```bash
   # Stay in internal repo
   ./sync-to-public.sh
   ```

### Handling External Contributions

1. **Receive PR on public repo:**
   - User submits PR to `QuartumSE`
   - Review on GitHub

2. **Merge to public:**
   ```bash
   cd QuartumSE
   # Review and merge PR on GitHub
   git pull
   ```

3. **Backport to internal:**
   ```bash
   # Stay in internal repo-internal
   # Manually copy changes or cherry-pick
   cp ../QuartumSE/src/quartumse/new_feature.py src/quartumse/
   git add src/
   git commit -m "Backport: User contribution from public PR #123"
   ```

---

## Best Practices

✅ **Do:**
- Develop all new features in internal repo first
- Run full test suite before syncing
- Update both public and internal docs as appropriate
- Keep internal docs (strategy, research) up to date
- Sync regularly to keep public repo fresh

❌ **Don't:**
- Develop directly in public repo (always start internal)
- Commit internal docs to public repo
- Sync without testing
- Let public repo lag behind internal for too long

---

## Quick Reference

**Start development:**
```bash
cd QuartumSE-internal
# Work on src/, tests/, experiments/, docs/
```

**Sync to public:**
```bash
cd QuartumSE
./sync-to-public.sh
git add . && git commit && git push
```

**Deploy docs:**
```bash
cd QuartumSE
mkdocs gh-deploy
```
