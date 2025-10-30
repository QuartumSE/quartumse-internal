# CI Test Strategy & Matrix Analysis

**Date**: 2025-10-30
**Current State**: Only testing ubuntu-latest + Python 3.11 (1 configuration)
**Goal**: Expand to catch real-world compatibility issues without excessive cost

## Problem Analysis

### Current Limitations

**What we test now:**
- OS: Ubuntu only
- Python: 3.11 only
- Total: **1 environment**

**What we claim to support** (from `pyproject.toml`):
- Python: 3.10, 3.11, 3.12, 3.13
- Platforms: Not specified, but quantum researchers use Windows, macOS, Linux

**What could break without broader testing:**

1. **Platform-specific failures**:
   - Path handling (`C:\Users\...` vs `/home/...`)
   - Line endings (CRLF on Windows vs LF on Unix)
   - File permissions (executable bits don't exist on Windows)
   - Case sensitivity (Windows/macOS are case-insensitive, Linux is not)
   - Process spawning differences
   - Temp directory locations (`TEMP` vs `/tmp`)

2. **Python version compatibility**:
   - **3.10**: Introduced `match/case`, some type hint improvements
   - **3.11**: `Self` type, exception groups, faster performance
   - **3.12**: New type parameter syntax, f-string improvements
   - **3.13**: Experimental JIT, GIL improvements, removed legacy features
   - Dependency version compatibility varies by Python version

3. **Dependency issues**:
   - Qiskit has different behavior on different Python versions
   - NumPy binary compatibility varies by platform
   - Some packages drop old Python support without warning

4. **Real-world evidence this matters**:
   - We support Python 3.13 but haven't tested it yet
   - We claim cross-platform support but only test on Linux
   - Users will try to `pip install` on Windows and expect it to work

## Test Matrix Design

### Principles

1. **Boundary testing**: Test min/max supported versions
2. **Platform diversity**: Each major OS at least once
3. **Cost consciousness**: Avoid redundant combinations
4. **Fast feedback**: Use `fail-fast: false` to see all failures

### Proposed Matrix (Pragmatic)

| OS | Python | Why |
|---|---|---|
| ubuntu-latest | 3.10 | **Minimum** supported version, most common OS |
| ubuntu-latest | 3.11 | **Current baseline** (existing config) |
| ubuntu-latest | 3.12 | Intermediate version coverage |
| ubuntu-latest | 3.13 | **Maximum** supported version, catch future issues |
| windows-latest | 3.11 | **Windows compatibility** (30%+ of users) |
| macos-latest | 3.11 | **macOS compatibility** (researchers love Macs) |

**Total**: 6 configurations (vs current 1)

**Cost analysis**:
- Current: ~5 min/run × 1 config = 5 minutes/run
- Proposed: ~5 min/run × 6 configs = 30 minutes/run
- Monthly (20 PRs + commits): ~600 minutes vs 100 minutes
- Well within free tier for private repos (2000-3000 min/month)

### Alternative: Minimal Expansion (If Cost Constrained)

If we need to minimize costs, prioritize:

| OS | Python | Why |
|---|---|---|
| ubuntu-latest | 3.10 | Min version boundary |
| ubuntu-latest | 3.11 | Baseline |
| ubuntu-latest | 3.13 | Max version boundary |
| windows-latest | 3.11 | Most common platform issue source |

**Total**: 4 configurations
**Cost**: ~20 minutes/run (~400 min/month)

## What Each Job Tests

### Main Test Job (Matrix)
- Linting (ruff)
- Formatting (black)
- Type checking (mypy)
- Unit tests (pytest with coverage)
- ~104 tests covering core functionality

**Coverage**: 23% (from latest run)
**Time**: ~5 minutes per config

### Integration Tests Job
- Currently: ubuntu-latest + 3.11 only
- **Should expand**: Run on at least one Windows and macOS config
- Tests real Qiskit integration with AerSimulator

### Experiments Job
- Currently: ubuntu-latest + 3.11 only
- **Can stay limited**: Computational experiments are expensive
- Use `continue-on-error: true` (already implemented)

### Docs Job
- Currently: ubuntu-latest + 3.11 only
- **Can stay limited**: Sphinx builds are platform-independent
- Focus is documentation correctness, not runtime compatibility

## Test Categories

### Unit Tests (fast, run everywhere)
```bash
pytest tests/ -v -m "not slow and not hardware"
```
- 104 tests
- ~2-3 minutes
- Should run on all matrix configurations

### Integration Tests (slower, selective)
```bash
pytest tests/integration/ -v -m "integration"
```
- Tests actual quantum simulators
- ~5-10 minutes
- Run on: ubuntu (3.11), windows (3.11), macos (3.11)

### Smoke Tests (critical paths)
```bash
pytest tests/smoke/ -v
```
- End-to-end workflow validation
- Should pass on all platforms

## Risk Assessment

### High Risk (must test)
✅ **Python 3.10 compatibility**: It's our minimum, users WILL use it
✅ **Python 3.13 compatibility**: It's our maximum, early adopters WILL try it
✅ **Windows compatibility**: Large user base, completely different OS

### Medium Risk (should test)
✅ **macOS compatibility**: Popular among researchers
✅ **Python 3.12 compatibility**: Recent stable, increasingly common

### Low Risk (optional)
- Python 3.11 on all three platforms (redundant after testing one each)
- Every Python version on every platform (exponential explosion)

## Implementation Priority

### Phase 1 (Immediate) ✅
Expand main test matrix to 6 configs as proposed above.

### Phase 2 (After Phase 1 Validation)
- Expand integration tests to windows + macos
- Add smoke tests to all platform combinations
- Consider adding dependency version matrix (min vs latest)

### Phase 3 (When Repo Goes Public)
- Full matrix: all platforms × all Python versions = 12 configs
- Zero cost (unlimited Actions for public repos)
- Maximum confidence for production use

## Metrics to Track

After expansion, monitor:
1. **Failure patterns**: Which configs fail most often?
2. **Time per config**: Are some platforms slower?
3. **Cost**: Monthly Actions minutes consumed
4. **Coverage**: Does it improve with more environments?

## Expected Findings

Based on experience, we'll likely discover:

1. **Windows path issues**: 80% chance
   - Fix: Use `pathlib.Path` everywhere (already doing this!)

2. **Line ending issues**: 30% chance
   - Fix: Configure git to normalize line endings

3. **Python 3.13 compatibility**: 50% chance
   - Fix: Update dependencies or adjust code

4. **macOS surprises**: 20% chance
   - Fix: Platform-specific workarounds if needed

## Recommendation

**Implement the 6-configuration matrix immediately.** The cost is reasonable (~500 min/month, well within limits), and the risk of shipping broken code to 3.10, 3.13, or Windows users is much higher than the cost of testing.

The current "ubuntu-latest + 3.11 only" configuration is a false economy. We're saving ~20 minutes per run at the cost of potentially broken releases and user frustration.

## Next Steps

1. Update `.github/workflows/ci.yml` with new matrix
2. Run on a test branch to validate timing
3. Monitor first few runs for unexpected failures
4. Document any platform-specific workarounds needed
5. Update this document with findings

## References

- [GitHub Actions pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Python compatibility guide](https://devguide.python.org/versions/)
- [Cross-platform Python best practices](https://docs.python.org/3/library/os.html#os.name)
