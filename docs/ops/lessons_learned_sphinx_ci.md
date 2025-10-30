# Lessons Learned: Sphinx Documentation CI Fixes

**Date**: 2025-10-30
**Context**: Fixed persistent Sphinx documentation build failures in CI (44 → 17 → 10 → 0 warnings)

## Problem Summary

Sphinx documentation build was failing in CI with `-W` (treat warnings as errors) flag, starting with 44 warnings and requiring multiple iterations to resolve.

## Root Causes Identified

### 1. **Outdated Intersphinx URLs** (Initial 44+ warnings)
- **Problem**: Qiskit documentation moved from `docs.quantum.ibm.com` to `quantum.cloud.ibm.com`
- **Symptom**: "cannot resolve" warnings for Qiskit classes like `Backend`, `QiskitRuntimeService`
- **Fix**: Updated `intersphinx_mapping` URLs in `docs/api/conf.py`
- **Lesson**: External documentation URLs change over time; verify intersphinx targets periodically

### 2. **Ambiguous Cross-References** (17 warnings)
- **Problem**: Classes re-exported from multiple modules (e.g., `ShadowConfig` from both `quartumse` and `quartumse.shadows.config`)
- **Symptom**: "more than one target found for cross-reference" warnings with `[ref.python]` domain
- **Wrong approach tried**: Adding to `nitpick_ignore` (doesn't work for ambiguous refs, only missing refs)
- **Correct fix**: Added `"ref.python"` to `suppress_warnings` list
- **Lesson**:
  - `nitpick_ignore` = suppress "cannot resolve" warnings (missing documentation)
  - `suppress_warnings` = suppress warning categories (ambiguous refs, duplicates, etc.)
  - Read Sphinx documentation carefully about warning types

### 3. **Duplicate Object Descriptions** (6 warnings)
- **Problem**: Classes documented in both source module and parent package that re-exports them
- **Examples**: `quartumse.estimator.base.Estimator` vs `quartumse.estimator.Estimator`
- **Initial fix**: Added `"autodoc"` to `suppress_warnings`
- **Better fix** (applied by user): Created `skip_reexported_members()` callback to skip members from submodules when documenting parent packages
- **Lesson**: When possible, solve the root cause (skip duplicates) rather than suppress symptoms

### 4. **Invalid Toctree References** (1 warning)
- **Problem**: Sphinx API docs referenced documents from MkDocs site (`../strategy/roadmap`)
- **Symptom**: "toctree contains reference to nonexisting document"
- **Fix**: Removed cross-documentation references; added link to main docs site instead
- **Lesson**: Sphinx and MkDocs are separate documentation systems; don't mix toctree references

## Sphinx Configuration Patterns

### Final Working Configuration (`docs/api/conf.py`)

```python
# Suppress warnings for intentional re-exports
suppress_warnings = [
    "ref.python",  # Ambiguous cross-references
    "autodoc",     # Duplicate objects (if not using skip callback)
    "toc",         # Toctree issues
]

# Map canonical targets for type aliases
autodoc_type_aliases = {
    "ShadowConfig": "quartumse.shadows.config.ShadowConfig",
    # ... (map re-exported classes to their source modules)
}

# Ignore truly missing external references
nitpick_ignore = [
    ("py:class", "numpy.random._generator.Generator"),  # Private NumPy class
    ("py:class", "Backend"),  # If intersphinx can't resolve
    # ... (use sparingly)
]

# Better approach: Skip re-exported members during autodoc
def skip_reexported_members(app, what, name, obj, skip, options):
    """Skip members that originate from submodules when documenting parent package."""
    # Implementation in docs/api/conf.py
    pass

def setup(app):
    app.connect("autodoc-skip-member", skip_reexported_members)
```

## Debugging Workflow

1. **Run locally first**: `tox -e docs` to see full warning output
2. **Count warnings**: Track reduction (44 → 17 → 10 → 0) to verify fixes work
3. **Read warning domains**: `[ref.python]` vs `[py:class]` vs `[toc.not_readable]` indicate different fixes needed
4. **Check Sphinx version**: Behavior changed in Sphinx 8.x; verify docs against your version
5. **Verify intersphinx inventories**: Test URLs manually:
   ```bash
   curl -I https://quantum.cloud.ibm.com/docs/api/qiskit/objects.inv
   ```

## CI/CD Integration

- **Use `-W --keep-going -n` flags**:
  - `-W`: Treat warnings as errors (fail build)
  - `--keep-going`: Show ALL warnings, don't stop at first
  - `-n`: Nitpicky mode (report all missing references)
- **Run in dedicated CI job**: Separate from tests for clarity
- **Use `tox -e docs`**: Ensures consistent environment

## Prevention

1. **Test docs build in CI**: Catches issues before merge
2. **Keep intersphinx URLs updated**: Check quarterly or when dependencies update
3. **Review Sphinx deprecation warnings**: Fix proactively
4. **Document re-export patterns**: Make intentional API design explicit
5. **Use type aliases**: Helps Sphinx resolve ambiguous references

## Time Investment

- **Total iterations**: 5 attempts (initial fix + 4 refinements)
- **Total time**: ~2 hours of debugging
- **Root cause**: Misunderstanding difference between `nitpick_ignore` and `suppress_warnings`
- **Takeaway**: Read Sphinx docs about warning suppression mechanisms FIRST

## References

- [Sphinx suppress_warnings docs](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-suppress_warnings)
- [Sphinx nitpick_ignore docs](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpick_ignore)
- [Intersphinx mapping](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html)
- [autodoc-skip-member event](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#event-autodoc-skip-member)

## Related Files

- `docs/api/conf.py` - Sphinx configuration
- `tox.ini` - Documentation build command
- `.github/workflows/ci.yml` - CI documentation job
