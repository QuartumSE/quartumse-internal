# Archive

Historical documentation and experiment starter scripts have been removed as of October 2025 to streamline the repository and improve navigation for new users.

## What was removed

### Documentation Archives
- `docs/archive/bootstrap_summary_20251020.md` - Bootstrap phase summary
- `docs/archive/status_report_20251022.md` - Phase 1 status report
- `docs/archive/strategic_analysis_20251021.md` - Strategic analysis

### Experiment Starter Scripts
- `experiments/archive/benchmarking/B_T01_rb_starter.py` - Randomized benchmarking starter
- `experiments/archive/chemistry/C_T01_h2_vqe_starter.py` - H₂ VQE starter
- `experiments/archive/metrology/M_T01_ghz_phase_starter.py` - GHZ phase metrology starter
- `experiments/archive/optimization/O_T01_maxcut_starter.py` - MaxCut optimization starter

### Archived Notebooks
- `notebooks/archive/preliminary_smoke_test.ipynb` - Early smoke test (superseded by `notebooks/comprehensive_test_suite.ipynb`)
- `notebooks/archive/review_smoke_test_results.ipynb` - Smoke test analysis
- `notebooks/archive/s_t01_ghz_classical_shadows.ipynb` - Old S-T01 notebook

## Accessing archived content

All removed files remain accessible in the Git history. To retrieve archived content:

**View list of archived files:**
```bash
git show fa5e756 --name-only --diff-filter=D
```

**Restore a specific archived file to your working directory:**
```bash
# Example: restore the bootstrap summary
git show fa5e756:docs/archive/bootstrap_summary_20251020.md > bootstrap_summary.md
```

**Check out the repository state before archive removal:**
```bash
git checkout fa5e756^  # One commit before removal
```

**Browse archived files on GitHub:**
Visit the commit directly: [fa5e756](https://github.com/quartumse/quartumse/tree/fa5e756)

## Current documentation structure

For up-to-date documentation, see:

- [Documentation index](README.md) - Complete navigation guide
- [Tutorials](tutorials/) - Getting started guides
- [How-to guides](how-to/) - Task-oriented walkthroughs
- [Explanation](explanation/) - Deep dives into architecture and theory
- [Strategy](strategy/) - Project roadmap and planning

## Superseding resources

Content from archived materials has been integrated into current documentation:

- **Bootstrap & status reports** → [Phase 1 Task Checklist](strategy/phase1_task_checklist.md)
- **Strategic analysis** → [Project Bible](strategy/project_bible.md) and [Roadmap](strategy/roadmap.md)
- **Starter experiments** → [Shadow Experiments Directory](../experiments/shadows/)
- **Old notebooks** → [Current Notebooks](../notebooks/) with comprehensive test suite

If you need specific information from archived files that isn't covered in current docs, please [open a discussion](https://github.com/quartumse/quartumse/discussions) or [file an issue](https://github.com/quartumse/quartumse/issues).
