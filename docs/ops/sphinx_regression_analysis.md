# Sphinx Documentation Regression Analysis

**Date**: 2025-10-30
**Issue**: Documentation build failing again after PR #62
**Previous Fix**: PR #60, #61 (fixed 44 → 17 → 10 → 0 warnings)

## What Went Wrong

### Changes in PR #62

#### 1. Removed "toc" Warning Suppression (docs/api/conf.py)

**Before** (our working fix):
```python
suppress_warnings = [
    "ref.python",  # Ambiguous Python cross-references
    "autodoc",     # Duplicate object descriptions and other autodoc warnings
    "toc",         # TOC/toctree warnings (nonexistent documents, etc.)
]
```

**After** (current broken state):
```python
suppress_warnings = [
    "ref.python",  # Ambiguous Python cross-references
    "autodoc.duplicate_object_description",  # Re-exported classes documented twice
]
```

**Problem**:
- Removed "toc" suppression entirely
- Changed "autodoc" to more specific "autodoc.duplicate_object_description"
- This will cause toctree warnings if referenced documents don't exist

#### 2. Re-added Toctree References (docs/api/index.rst)

**Before** (our working fix):
```rst
For tutorials, guides, and strategy documentation, please visit the main
documentation site at https://quartumse.com/

.. toctree::
   :maxdepth: 2
   :caption: API Modules

   reference/index
```

**After** (current broken state):
```rst
.. toctree::
   :maxdepth: 2
   :caption: Guides & Strategy

   ../README
   ../tutorials/quickstart
   ../how-to/run-tests
   strategy/roadmap

.. toctree::
   :hidden:

   ../strategy/phase1_task_checklist
   ../ops/ci_expansion_guide

.. toctree::
   :maxdepth: 2
   :caption: API Modules

   reference/index
```

**Problem**:
- Re-added references to files that DON'T exist in Sphinx build context
- `../README`, `../tutorials/quickstart`, `../how-to/run-tests` don't exist
- Only created `strategy/roadmap.md` as wrapper, but not others
- Inconsistent approach (some wrappers, some missing)

#### 3. Created Partial Workaround (docs/api/strategy/roadmap.md)

```markdown
```{include} ../../strategy/roadmap.md
:relative-docs: ../../strategy
:relative-images: ../../strategy
```
```

**Problem**:
- Only ONE wrapper file created
- Still references 5 other non-existent documents
- This violates the lesson: "Don't mix Sphinx and MkDocs documentation"

## Violation of Lessons Learned

### From docs/ops/lessons_learned_sphinx_ci.md

**Lesson #4: Invalid Toctree References**
> **Problem**: Sphinx API docs referenced documents from MkDocs site (`../strategy/roadmap`)
> **Symptom**: "toctree contains reference to nonexisting document"
> **Fix**: Removed cross-documentation references; added link to main docs site instead
> **Lesson**: Sphinx and MkDocs are separate documentation systems; don't mix toctree references

**We explicitly learned this and fixed it in commit a3163ec:**
- Removed all toctree references to MkDocs documents
- Added text link to main documentation site
- Added "toc" to suppress_warnings as defense

**PR #62 undid ALL of this work** and made it worse by:
- Removing the "toc" suppression
- Re-adding the toctree references
- Only creating 1 out of 6 needed wrapper files

## Why This Approach is Wrong

### Option 1: Separate Documentation (Our Original Fix) ✅
- **Pros**: Clean separation, no duplication, no complex includes
- **Cons**: API docs don't have strategy/tutorial links in toctree
- **Our solution**: Text link to main site (https://quartumse.com/)

### Option 2: Full Integration (Not Implemented)
- **Pros**: Everything in one place, unified navigation
- **Cons**: Duplicates content, complex maintenance
- **Requires**: ALL documents wrapped, not just one

### Option 3: Partial Integration (Current Broken State) ❌
- **Pros**: None
- **Cons**:
  - Inconsistent (1 wrapper exists, 5 don't)
  - Still causes toctree warnings
  - Removed warning suppression
  - Violates learned lessons
  - More complex than either clean solution

## Expected Build Failures

With current configuration, expect these warnings:

```
/docs/api/index.rst:12: WARNING: toctree contains reference to nonexisting document '../README'
/docs/api/index.rst:13: WARNING: toctree contains reference to nonexisting document '../tutorials/quickstart'
/docs/api/index.rst:14: WARNING: toctree contains reference to nonexisting document '../how-to/run-tests'
/docs/api/index.rst:20: WARNING: toctree contains reference to nonexisting document '../strategy/phase1_task_checklist'
/docs/api/index.rst:21: WARNING: toctree contains reference to nonexisting document '../ops/ci_expansion_guide'
```

**Total**: 5+ warnings (treated as errors with `-W` flag)

## Correct Fix Options

### Option A: Revert to Separation (Recommended) ✅

Restore our working configuration:

1. **docs/api/index.rst**: Remove all toctree references to MkDocs docs
2. **docs/api/conf.py**: Restore "toc" and "autodoc" (not specific) to suppress_warnings
3. **Delete docs/api/strategy/**: Remove the partial wrapper
4. **Result**: Clean separation, no warnings, follows lessons learned

### Option B: Full Integration (More Work)

If unified navigation is really needed:

1. Create wrapper files for ALL referenced documents:
   - docs/api/README.md
   - docs/api/tutorials/quickstart.md
   - docs/api/how-to/run-tests.md
   - docs/api/strategy/roadmap.md (exists)
   - docs/api/strategy/phase1_task_checklist.md
   - docs/api/ops/ci_expansion_guide.md

2. Each wrapper uses `{include}` directive

3. Keep "toc" suppression in case includes fail

4. **Result**: Full integration, more maintenance burden

### Why Option A is Better

1. **Simpler**: One documentation system for API, one for user docs
2. **Cleaner**: No file duplication or complex includes
3. **Proven**: This configuration worked (0 warnings)
4. **Maintainable**: Changes to one system don't affect the other
5. **Follows lessons**: Respects the "separate systems" lesson

## Recommended Action

**Revert PR #62 changes to docs/api/** and restore our working configuration:

```bash
git revert de83088  # Or cherry-pick the working commits
```

Then update docs/api/index.rst with clear explanation:

```rst
QuartumSE API Reference
=======================

Welcome to the autogenerated API reference for QuartumSE.

**For tutorials, guides, and strategy docs**, visit the main documentation:
https://quartumse.com/

This API reference focuses on module, class, and function documentation
extracted from source code docstrings.

.. toctree::
   :maxdepth: 2
   :caption: API Modules

   reference/index
```

## Lessons Reinforced

1. **Don't mix documentation systems** - Sphinx ≠ MkDocs
2. **Keep working solutions** - If it's not broken, don't fix it
3. **Follow documented lessons** - We wrote lessons_learned_sphinx_ci.md for a reason
4. **Be consistent** - Partial solutions cause more problems than they solve
5. **Test before merging** - This should have failed CI

## Prevention

Update CI to catch this:
- Ensure docs job runs on all PRs
- Fail on warnings (already using `-W`)
- Review docs/api/ changes carefully
- Reference lessons_learned_sphinx_ci.md in PR reviews

## Timeline

- **2025-10-30 morning**: Fixed Sphinx warnings (44 → 0) in PR #60, #61
- **2025-10-30 afternoon**: PR #62 merged, UNDID the fixes
- **2025-10-30 now**: Documentation build failing again

**Root cause**: PR #62 author didn't review lessons_learned_sphinx_ci.md or understand why the original fix worked.
