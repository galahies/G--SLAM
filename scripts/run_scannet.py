import ast
import os
from collections import defaultdict
from glob import glob
from shutil import copyfile


out = "outputs/scannet"
os.makedirs(f"{out}/meshes", exist_ok=True)
metrics = defaultdict(float)
nrs = ["0000", "0054", "0059", "0106", "0169", "0181", "0207", "0233"]
seqs = [scan for scan in sorted(glob("data/ScanNet/scene*")) if any(n in scan for n in nrs)]

for seq in seqs:
    name = os.path.basename(seq)
    os.makedirs(f"{out}/{name}", exist_ok=True)
    print(name, out)

    cmd = (
        f"python demo.py --imagedir {seq}/color --calib {seq}/calib.txt --cropborder 12 "
        f"--config config/scannet_config.yaml --output {out}/{name} > {out}/{name}/log.txt"
    )
    if not os.path.exists(f"{out}/{name}/traj_full.txt"):
        os.system(cmd)

    if not os.path.exists(f"{out}/{name}/ape.txt") or len(open(f"{out}/{name}/ape.txt").readlines()) < 10:
        os.system(f"evo_ape tum {seq}/traj.txt {out}/{name}/traj_full.txt -vas --no_warnings > {out}/{name}/ape.txt")

    ate = float([line for line in open(f"{out}/{name}/ape.txt").readlines() if "rmse" in line][0][-10:-1]) * 100
    metrics["ATE full"] += ate
    print(f"- full ATE: {ate:.4f}")

    psnr = ast.literal_eval(open(f"{out}/{name}/psnr/after_opt/final_result_kf.json").read())
    metrics["PSNR"] += psnr["mean_psnr"]
    metrics["SSIM"] += psnr["mean_ssim"]
    metrics["LPIPS"] += psnr["mean_lpips"]
    print(f"- psnr: {psnr['mean_psnr']:.3f}, ssim: {psnr['mean_ssim']:.3f}, lpips: {psnr['mean_lpips']:.3f}")

    weights = ["5.0", "10.0"]
    if not os.path.exists(f"{out}/{name}/tsdf_mesh_w{weights[-1]}.ply"):
        os.system(
            f"python tsdf_integrate.py --result {out}/{name} --voxel_size 0.015 --weight {' '.join(weights)} > /dev/null"
        )
        for weight in weights:
            copyfile(f"{out}/{name}/tsdf_mesh_w{weight}.ply", f"{out}/meshes/{name}_w{weight}.ply")

for key in metrics:
    print(f"{key}:\t {metrics[key] / len(seqs):.4f}")
