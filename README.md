# Vehicle-Vibration IRI Estimation: Re-examined

[![Verification Checks](https://img.shields.io/badge/Verification-40%2F40%20Passing-brightgreen)](evaluation/verify_final.py)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue)](requirements.txt)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-orange)](requirements.txt)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-100%25%20Automated-success)](run_all_experiments.py)
[![Paper](https://img.shields.io/badge/PDF-Paper%20%26%20Supplement-red)](paper/)

This repository contains the complete reproduction package, simulation pipeline, data processing, experimental evaluation, and audit trail for:

> **Vehicle-Vibration IRI Estimation: Re-examined**  
> *A rigorously verified, reproducible empirical study across real-world profilometer benchmarks (LiRA-CD, ARAN, P79) and parametric quarter-car simulation.*

---

## Key Documents and Paper Sources

| Document | Description | Format |
|---|---|---|
| **Main Paper** | 10-page main manuscript | [`paper/main.pdf`](paper/main.pdf) |
| **Supplementary Material** | 18-page comprehensive appendix with proofs, tables, and extended analyses | [`paper/supplementary.pdf`](paper/supplementary.pdf) |
| **LaTeX Sources** | Full modular LaTeX sources with auto-generated macro pipelines | [`paper/`](paper/) |
| **Audits and Reports** | Pre-registered protocol deviations, claim audits, and verification records | [`docs/`](docs/) |
| **Independent Reviews** | Full adversarial peer reviews, check scripts, and reviewer outputs | [`review/`](review/) |

---

## Quick Start: Verify Reproduction in 30 Seconds

All headline numbers, figures, tables, and claims in the paper are derived deterministically. You can run the independent verification test suite immediately without retraining:

```bash
# 1. Verify final corrections and macro integrity (15 checks)
python evaluation/verify_final.py

# 2. Verify numerical claims, protocol bounds and checkpoints (25 checks)
python evaluation/verify_v3.py
```

Both scripts run self-contained statistical audits and re-derive every headline metric from raw prediction records in `results/`, exiting with `0 failed`.

---

## Environment Setup

### Option 1: Standard Installation (Recommended)
Python 3.10 or 3.11 is recommended. Install core dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Exact Pinned Lockfile
To replicate the exact binary environment used during the evaluation:
```bash
pip install -r environment_lock.txt
```
*Note: PyTorch can be run in CUDA 11.8 or CPU mode.*

---

## Reproducing the Study

### 1. One-Command End-to-End Reproduction
To re-run all pipelines whose outputs are missing:
```bash
python run_all_experiments.py
```
To force a complete recomputation of all experimental steps:
```bash
python run_all_experiments.py --force
```

### 2. Fast Artifact Generation (Figures, Tables and Numbers)
To regenerate all paper artifacts from stored results in seconds:
```bash
# Generate LaTeX macros for all paper numbers
python make_numbers_v3.py

# Generate all LaTeX and markdown tables
python make_tables_v3.py

# Generate all publication figures (PDF and PNG)
python make_figures_v3.py

# Generate headline summary CSVs with provenance
python make_final_results_v3.py
```

### 3. Running Specific Experimental Protocol Steps
You can run individual protocol steps via `--only`:
```bash
python run_all_experiments.py --only v3_pooled v3_band_limited v3_rank_paired
```

---

## Repository Architecture

```
.
├── common/                  # Shared core library (physics engine, sensor models, features, IRI math)
│   ├── vehsim.py            # Calibrated quarter-car simulator
│   ├── sensor.py            # Mounting compliance and sensor transfer functions
│   ├── simpipe.py           # Simulation pipeline orchestrator
│   ├── iri.py               # Golden reference ASTM E1926 Golden Car IRI calculation
│   └── models.py            # Model architectures (LightGBM, MLP, CNN, quarter-car inversion)
├── config/                  # Frozen configurations
│   ├── models.json          # Model hyperparameters
│   └── sim_ranges.json      # Physical parameter variation bounds
├── data/                    # Dataset downloaders and preprocessed caches
│   ├── raw/                 # LiRA-CD downloaders (data downloaded on demand)
│   └── processed/           # Filtered segment arrays and feature matrices
├── docs/                    # Formal audit trails, plans, and verification reports
│   ├── audits/              # Claim audits (CLAIM_AUDIT_V2/V3), implementation audits
│   ├── reports/             # Milestone verification and submission reports
│   └── history/             # Baseline initial state and research rescue plan
├── evaluation/              # Frozen protocols, profilometer alignment and verification suites
│   ├── verify_final.py      # 15-check post-audit verification script
│   ├── verify_v3.py         # 25-check protocol validation suite
│   ├── PROTOCOL_V3.md       # Pre-registered protocol (frozen SHA-256)
│   └── PROTOCOL_V3_DEVIATIONS.md # Pre-registered protocol deviations log
├── experiments/             # Experiment drivers across research rounds
│   ├── v2/                  # Round 2 experimental scripts (variants, value of sim, etc.)
│   └── v3/                  # Round 3 experimental scripts (joint training, band-limited, etc.)
├── figures/                 # Generated vector figures (PDF) and previews (PNG)
├── logs/                    # Execution logs with per-step timing
├── paper/                   # Modular LaTeX manuscript sources, macros, and compiled PDFs
├── references/              # BibTeX database, crossref validation, and citation audit
├── results/                 # Numerical result tables, prediction arrays, and metrics
├── review/                  # External adversarial reviews, reviewer check scripts, and outputs
└── tables/                  # Generated paper tables (.tex, .csv, .md)
```

---

## Audits, Reports and Governance Index

Every stage of this study was conducted under an adversarial audit methodology. Key documents are cataloged below:

| Category | Document | Description |
|---|---|---|
| **Reports** | [`docs/reports/FINAL_SUBMISSION_REPORT.md`](docs/reports/FINAL_SUBMISSION_REPORT.md) | Final resolution of all audit issues, files changed, and check summaries |
| | [`docs/reports/FINAL_VERIFICATION_REPORT_V3.md`](docs/reports/FINAL_VERIFICATION_REPORT_V3.md) | Third-round verification outcomes and open questions |
| | [`docs/reports/FINAL_REPORT_V2.md`](docs/reports/FINAL_REPORT_V2.md) | Second-round verification and methodological revisions |
| | [`docs/reports/FINAL_REPORT.md`](docs/reports/FINAL_REPORT.md) | Initial rescue phase audit findings |
| **Claim Audits** | [`docs/audits/CLAIM_AUDIT_V3.md`](docs/audits/CLAIM_AUDIT_V3.md) | Line-by-line verification of every textual claim against numerical output files |
| | [`docs/audits/CLAIM_AUDIT_V2.md`](docs/audits/CLAIM_AUDIT_V2.md) | Claim verification for round 2 |
| | [`docs/audits/IMPLEMENTATION_AUDIT_V3.md`](docs/audits/IMPLEMENTATION_AUDIT_V3.md) | Audit tracking each review recommendation (Class A-E decisions) |
| | [`docs/audits/REVISION_PLAN_V2.md`](docs/audits/REVISION_PLAN_V2.md) | Review concerns: evidence, validity, and resolution plan |
| | [`docs/audits/REVIEWER_AUDIT_V2.md`](docs/audits/REVIEWER_AUDIT_V2.md) | 15-question adversarial self-audit |
| **Reviews** | [`review/INDEPENDENT_REVIEW_V3.md`](review/INDEPENDENT_REVIEW_V3.md) | Comprehensive round 3 independent adversarial review |
| | [`review/first.md`](review/first.md) | Original round 1 review |
| | [`review/final_audit/audit.md`](review/final_audit/audit.md) | Final verification audit report |
| | [`review/v3_checks/`](review/v3_checks/) | Read-only verification scripts used by independent reviewers |
| **Protocols** | [`evaluation/PROTOCOL_V3.md`](evaluation/PROTOCOL_V3.md) | Frozen analysis protocol (SHA-256 verified) |
| | [`evaluation/PROTOCOL_V3_DEVIATIONS.md`](evaluation/PROTOCOL_V3_DEVIATIONS.md) | Documented deviations from initial protocol |

---

## Determinism and Provenance

1. **Macro-Tied Numbers**: Every single number in `paper/main.tex` and `paper/supplementary.tex` is an automatically generated macro (`paper/numbers_v3.tex`, `numbers_v2.tex`, `numbers.tex`). If an underlying data point shifts, the macro updates or flags `??`.
2. **Fixed Seeds**:
   - Simulation generators: fixed seeds (V7: `41001`, V8: `41002`, vehicle sweep: `20261003`).
   - Calibration draws: `numpy.random.default_rng(1000 * d + 7)` for paired draws $d \in [0, 19]$.
   - Bootstraps: fixed seed `3003` ($B=2000$), paired ranking seed `2026` ($B=2000$), speed robustness seed `5` ($B=1000$).
3. **Cryptographic Checkpoints**: The reviewed checkpoint states are preserved under `checkpoints/` with verified `MANIFEST.sha256` checksums.

---

## Citation and License

- Code and Methodology: Released under the MIT License.
- Dataset (LiRA-CD): CC BY 4.0 (doi:10.11583/DTU.c.6659909).
- Contact: Refer to the authors listed in `paper/main.tex`.
