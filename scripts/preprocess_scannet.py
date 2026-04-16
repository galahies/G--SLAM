from glob import glob

import numpy as np
from scipy.spatial.transform import Rotation as R


def to_se3_vec(pose_mat):
    quat = R.from_matrix(pose_mat[:3, :3]).as_quat()
    return np.hstack((pose_mat[:3, 3], quat))


nrs = ["0000", "0054", "0059", "0106", "0169", "0181", "0207", "0233"]
seqs = [scan for scan in sorted(glob("data/ScanNet/scene*")) if any(n in scan for n in nrs)]

for scan_path in seqs:
    print("preprocessing", scan_path.split("/")[-1])

    k_mat = np.loadtxt(f"{scan_path}/intrinsic/intrinsic_color.txt")
    k_vec = [k_mat[0, 0], k_mat[1, 1], k_mat[0, 2], k_mat[1, 2]]
    np.savetxt(f"{scan_path}/calib.txt", k_vec)

    traj = []
    for i, pose_file in enumerate(sorted(glob(f"{scan_path}/pose/*"))):
        pose = np.loadtxt(pose_file)
        pose = to_se3_vec(pose)
        if np.isnan(pose).any():
            print(f"skip {i} {pose} due to NaN values")
            pose = np.zeros(7)
        traj.append([i] + list(pose))

    traj = np.stack(traj)
    np.savetxt(f"{scan_path}/traj.txt", traj)
