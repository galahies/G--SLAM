import ast
import os
from collections import defaultdict
from glob import glob
from shutil import copyfile

import numpy as np
import open3d as o3d


out = "outputs/replica"
os.makedirs(f"{out}/meshes", exist_ok=True)
seqs = sorted(glob("data/Replica/ro*")) + sorted(glob("data/Replica/off*"))
metrics = defaultdict(float)

for seq in seqs:
    name = os.path.basename(seq)
    os.makedirs(f"{out}/{name}", exist_ok=True)
    print(name, out)

    cmd = f"python demo.py --imagedir {seq}/colors --gtdepthdir {seq}/depths "
    cmd += f"--config config/replica_config.yaml --calib calib/replica.txt --output {out}/{name} > {out}/{name}/log.txt"
    if not os.path.exists(f"{out}/{name}/traj_full.txt"):
        os.system(cmd)

    if not os.path.exists(f"{out}/{name}/ape.txt") or len(open(f"{out}/{name}/ape.txt").readlines()) < 10:
        os.system(
            f"evo_ape tum {seq}/traj_tum.txt {out}/{name}/traj_full.txt "
            f"-vas --save_results {out}/{name}/evo.zip --no_warnings > {out}/{name}/ape.txt"
        )
        os.system(f"unzip -q {out}/{name}/evo.zip -d {out}/{name}/evo")

    ate = float([line for line in open(f"{out}/{name}/ape.txt").readlines() if "rmse" in line][0][-10:-1]) * 100
    metrics["ATE full"] += ate
    print(f"- full ATE: {ate:.4f}")

    psnr = ast.literal_eval(open(f"{out}/{name}/psnr/after_opt/final_result.json").read())
    print(f"- psnr: {psnr['mean_psnr']:.3f}, ssim: {psnr['mean_ssim']:.3f}, lpips: {psnr['mean_lpips']:.3f}")
    metrics["PSNR"] += psnr["mean_psnr"]
    metrics["SSIM"] += psnr["mean_ssim"]
    metrics["LPIPS"] += psnr["mean_lpips"]

    weight_value = 2
    weight_tag = f"w{weight_value:.1f}"
    if not os.path.exists(f"{out}/{name}/tsdf_mesh_{weight_tag}.ply"):
        os.system(
            f"python tsdf_integrate.py --result {out}/{name} --voxel_size 0.006 --weight {weight_value} > /dev/null"
        )
        ply = o3d.io.read_triangle_mesh(f"{out}/{name}/tsdf_mesh_{weight_tag}.ply")
        ply = ply.transform(np.load(f"{out}/{name}/evo/alignment_transformation_sim3.npy"))
        o3d.io.write_triangle_mesh(f"{out}/{name}/tsdf_mesh_{weight_tag}_aligned.ply", ply)
        copyfile(f"{out}/{name}/tsdf_mesh_{weight_tag}_aligned.ply", f"{out}/meshes/{name}.ply")

    if not os.path.exists(f"{out}/{name}/eval_recon_{weight_tag}.txt"):
        os.system(
            f"python scripts/eval_recon.py {out}/{name}/tsdf_mesh_{weight_tag}_aligned.ply "
            f"data/Replica/gt_mesh_culled/{name}.ply --eval_3d --save {out}/{name}/eval_recon_{weight_tag}.txt > /dev/null"
        )

    result = ast.literal_eval(open(f"{out}/{name}/eval_recon_{weight_tag}.txt").read())
    metrics["accu"] += result["mean precision"]
    metrics["comp"] += result["mean recall"]
    metrics["compr"] += result["recall"]
    print(
        f"- acc: {result['mean precision']:.3f}, "
        f"comp: {result['mean recall']:.3f}, "
        f"comp rat: {result['recall']:.3f}\n"
    )

for key in metrics:
    print(f"{key}:\t {metrics[key] / len(seqs):.4f}")
