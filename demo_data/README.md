# Demo Data Directory

This directory stores data from **demo notebooks and quickstart examples**.

## Purpose

Temporary storage for notebook demonstrations and testing. Data here is ephemeral and can be safely deleted.

## Used By

- `notebooks/quickstart_shot_persistence.ipynb`
- `notebooks/comprehensive_test_suite.ipynb`
- `notebooks/noise_aware_shadows_demo.ipynb`
- Any other demo or tutorial notebooks

## Directory Structure

Auto-created subdirectories when notebooks run:
```
demo_data/
├── manifests/     # Demo experiment manifests
├── shots/         # Demo shot data (Parquet)
├── reports/       # Demo reports
└── README.md
```

## Cleanup

Safe to delete at any time:
```bash
rm -rf demo_data/{manifests,shots,reports}/*
```

Or recreate entirely:
```bash
rm -rf demo_data
mkdir -p demo_data
```

---

**Note:** This directory is git-ignored. Only this README is version-controlled.
