# Release Scope

This repository is a pre-acceptance public snapshot of `G--SLAM`.
It is intended to make the method understandable, inspectable, and runnable along the released public workflows without disclosing every internal asset tied to an unpublished submission.

## Released in This Snapshot

- Core `g2slam` source code
- Configuration files and calibration files
- Monocular demo entrypoint: `demo.py`
- Public preprocessing and evaluation scripts under `scripts/`
- TSDF integration utility
- The released DROID backbone weight placed in `pretrained_models/`
- Documentation for repository structure and public reproduction steps

## Intentionally Deferred

- Private outdoor driving benchmark assets used in the paper
- Internal experiment bookkeeping and large result archives
- Full packaging of paper-only artifacts that depend on unreleased assets
- Any release material that would prematurely expose unpublished benchmark content

## Practical Interpretation

This means:

1. You can inspect the main implementation structure of `G--SLAM`.
2. You can follow the released public workflows documented in the repository.
3. You should not expect this snapshot to contain every asset referenced in the manuscript.

## Why This Split Exists

The paper is still under review, so the repository is deliberately split into:

- a public, documentation-friendly snapshot for code reading and public workflows; and
- deferred assets that can be released later without exposing unpublished benchmark content too early.
