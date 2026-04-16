# G--SLAM Project Structure

This document maps the paper-level modules of `G--SLAM` to the repository layout used in this release snapshot.

## Naming Rules

- Repository name: `G--SLAM`
- Python package: `g2slam`
- Main runtime class: `G2`
- Demo/evaluation entrypoints: top-level `demo.py`, `tsdf_integrate.py`, and `scripts/*.py`

The goal of this naming scheme is to keep the user-facing paths consistent while preserving the internal modular structure inherited from the baseline codebase.

## Top-Level Layout

```text
G--SLAM/
├── demo.py
├── tsdf_integrate.py
├── environment.yaml
├── setup.py
├── config/
├── calib/
├── g2slam/
├── scripts/
├── pretrained_models/
├── media/
└── docs/
```

## Module-to-File Mapping

### 1. Tracking
These files implement online keyframe selection, dense tracking, and local optimization.

- `g2slam/motion_filter.py`
- `g2slam/track_frontend.py`
- `g2slam/track_backend.py`
- `g2slam/depth_video.py`
- `g2slam/factor_graph.py`

### 2. Loop Validation and Pose Graph Optimization
These files handle loop candidate management and Sim(3)-style global correction.

- `g2slam/pgo_buffer.py`
- `g2slam/factor_graph.py`
- `g2slam/depth_video.py`

### 3. Online Gaussian Mapping
These files manage Gaussian map construction and incremental refinement.

- `g2slam/gs_backend.py`
- `g2slam/gaussian/*`

### 4. Offline Refinement
This stage refines poses and Gaussians after online tracking is complete.

- `g2slam/g2.py`
- `g2slam/gs_backend.py`
- `g2slam/gaussian/*`

## User-Facing Entry Points

- `demo.py`
  Main entrypoint for running the released monocular SLAM pipeline on image folders.
- `scripts/preprocess_owndata.py`
  Converts a monocular video into extracted frames and estimates intrinsics using COLMAP.
- `scripts/run_replica.py`
  Automates the public Replica evaluation path.
- `scripts/run_scannet.py`
  Automates the public ScanNet evaluation path.
- `tsdf_integrate.py`
  Converts reconstructed depth/rendering results into a TSDF mesh.

## Notes on This Snapshot

- The public structure is intentionally documentation-first.
- Public-dataset workflows are kept visible and consistent.
- Private or deferred release components are documented in [release_scope.md](release_scope.md).
