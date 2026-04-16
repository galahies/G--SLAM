# Reproducibility Guide

This document explains what can be reproduced from the current public snapshot of `G--SLAM` and what remains outside the release boundary.

## Publicly Documented Workflows

The current snapshot is organized around the following public pathways:

### 1. Replica demo and evaluation

```bash
bash scripts/download_replica.sh
python scripts/preprocess_replica.py
python demo.py --imagedir data/Replica/room0/colors --calib calib/replica.txt --config config/replica_config.yaml --output outputs/room0
python scripts/run_replica.py
```

### 2. ScanNet preprocessing and evaluation

```bash
python scripts/preprocess_scannet.py
python scripts/run_scannet.py
```

### 3. Custom monocular video workflow

```bash
python scripts/preprocess_owndata.py PATH_TO_VIDEO PATH_TO_OUTPUT_DIR
python demo.py --imagedir PATH_TO_OUTPUT_DIR/images --calib PATH_TO_OUTPUT_DIR/calib.txt --config config/owndata_config.yaml --output outputs/owndata
```

### 4. TSDF mesh extraction

```bash
python tsdf_integrate.py --result outputs/room0 --voxel_size 0.01 --weight 2
```

## What This Snapshot Is Designed For

This repository snapshot is primarily meant for:

- understanding the main system layout;
- reviewing the released implementation structure;
- following public demo/evaluation entrypoints;
- reproducing the public-facing workflow organization of the project.

## What Is Not Included Here

The manuscript also references experiments on:

- LLFF; and
- a self-collected RTK-GPS outdoor driving benchmark.

These assets are not bundled into the current snapshot.
As a result, the repository should be interpreted as a public code snapshot rather than a full benchmark pack for every table in the manuscript.

## Environment Notes

The repository expects:

- Python/Conda environment created from `environment.yaml`
- CUDA 11.8-compatible PyTorch build
- compiled local extensions from `setup.py`
- Omnidata depth/normal prior checkpoints in `pretrained_models/`

## Output Conventions

Typical outputs include:

- `traj_kf.txt`
- `traj_full.txt`
- rendering metrics under `psnr/`
- Gaussian-map artifacts
- optional TSDF meshes created by `tsdf_integrate.py`

## Recommended Citation Practice

If this repository snapshot is used while the manuscript is still under review, cite the manuscript as an under-review work and describe the repository as a pre-acceptance public snapshot.
