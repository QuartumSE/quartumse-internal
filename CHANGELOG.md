# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Automated documentation workflow that validates MkDocs builds on pull requests and publishes updates to GitHub Pages on master merges.
- `src/quartumse/utils/args.py` with reusable argparse helpers (`add_backend_option`, `add_data_dir_option`, `add_seed_option`, `add_shadow_size_option`) for standardized experiment CLI arguments.
- `SUPPORT.md` with community support policy and contact information.
- Guided learning path table in README (Step 1-5 progression from quickstart to automation).
- Repository tour with ASCII directory tree structure in README.
- Configurable `--data-dir`, `--seed`, and `--shadow-size` flags to `S_T01_ghz_baseline.py`.
- `docs/ops/ci_expansion_guide.md` - Step-by-step guide for expanding CI matrix when repository becomes public (Phase 3).
- MkDocs extras dependency group in `pyproject.toml` with `mkdocs-section-index` and `markdown-include` plugins.

### Changed
- Streamlined README.md from ~500 lines to ~180 lines with clearer vision, 10-minute quickstart, and documentation index.
- Updated documentation navigation structure (removed archive section, moved Phase 1 Checklist to Strategy).
- Refactored `experiments/shadows/S_T01_ghz_baseline.py` to use standardized CLI argument helpers and improved config resolution logic.
- Updated `docs/README.md` with comprehensive how-to guide listing and clearer section organization.
- Simplified `docs/index.md` to 13-line narrative with navigation pointers.
- **Reduced CI matrix from 12 jobs to 1 job** (Ubuntu + Python 3.11) during Phase 1-2 while repository is private. Full matrix (3 OSes × 4 Python versions) will be restored in Phase 3 when repository becomes public. See Phase 3 exit criteria in roadmap.

### Removed
- Archive directories (`docs/archive/`, `experiments/archive/`, `notebooks/archive/`) containing:
  - Historical bootstrap documentation (bootstrap_summary, status_report, strategic_analysis)
  - Superseded experiment starter scripts (B_T01_rb, C_T01_h2_vqe, M_T01_ghz_phase, O_T01_maxcut)
  - Outdated notebooks (preliminary_smoke_test, review_smoke_test_results, s_t01_ghz_classical_shadows)
  - Total reduction: ~3,285 lines of stale content
  - Files remain accessible in Git history for reference.

### Fixed
- Deprecated `actions/upload-artifact@v3` in CI workflow (upgraded to v4).
- MkDocs deployment workflow failures caused by missing `markdown-include` and `mkdocs-section-index` dependencies.
- Type annotation compatibility issues with Python 3.10+ (replaced `Optional[X]` with `X | None`, removed deprecated typing imports).
- Exception handling patterns to properly chain exceptions with `from err` or `from None`.
- Windows path compatibility in test suite (`test_manifest_io.py`).

## [0.1.0] - 2024-05-01
### Added
- Baseline (v0) and noise-aware (v1) classical shadow estimation pipelines with CLI integration for quantum experiments.
- End-to-end provenance tracking that records manifests, calibration snapshots, and shot data for reproducible studies.
- IBM Quantum Runtime and Aer simulator backends with automatic fallbacks for local development.
- Shared analysis utilities for shot-saving ratio (SSR), confidence interval coverage, and variance tracking across experiments.

[Unreleased]: https://github.com/quartumse/quartumse/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/quartumse/quartumse/releases/tag/v0.1.0
