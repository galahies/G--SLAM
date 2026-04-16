import os  # noqa: E402
import sys  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "g2slam"))  # noqa: E402

import argparse
import os
import re
import resource
import time

import cv2
import lietorch
import numpy as np
import torch
from torch.multiprocessing import Process, Queue
from tqdm import tqdm

from g2 import G2


rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (100000, rlimit[1]))


def show_image(image, depth_prior, depth, normal):
    from util.utils import colorize_np

    image = image[[2, 1, 0]].permute(1, 2, 0).cpu().numpy()
    depth = colorize_np(
        np.concatenate((depth_prior.cpu().numpy(), depth.cpu().numpy()), axis=1),
        range=(0, 4),
    )
    normal = normal.permute(1, 2, 0).cpu().numpy()
    preview = np.concatenate(
        (image / 255.0, (normal[..., [2, 1, 0]] + 1.0) / 2.0, depth),
        axis=1,
    )
    cv2.imshow("rgb / prior normal / aligned prior depth / JDSA depth", preview[::2, ::2])
    cv2.waitKey(1)


def mono_stream(queue, imagedir, calib, undistort=False, cropborder=False, start=0, length=100000):
    res = 341 * 640

    calib = np.loadtxt(calib, delimiter=" ")
    k_mat = np.array([[calib[0], 0, calib[2]], [0, calib[1], calib[3]], [0, 0, 1]])
    image_list = sorted(os.listdir(imagedir))[start : start + length]

    for t, image_name in enumerate(image_list):
        image = cv2.imread(os.path.join(imagedir, image_name))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        intrinsics = torch.tensor(calib[:4])

        if len(calib) > 4 and undistort:
            image = cv2.undistort(image, k_mat, calib[4:])

        if cropborder > 0:
            image = image[cropborder:-cropborder, cropborder:-cropborder]
            intrinsics[2:] -= cropborder

        h0, w0, _ = image.shape
        h1 = int(h0 * np.sqrt(res / (h0 * w0)))
        w1 = int(w0 * np.sqrt(res / (h0 * w0)))
        h1 = h1 - h1 % 8
        w1 = w1 - w1 % 8
        image = cv2.resize(image, (w1, h1))
        image = torch.as_tensor(image).permute(2, 0, 1)

        intrinsics[[0, 2]] *= w1 / w0
        intrinsics[[1, 3]] *= h1 / h0

        is_last = t == len(image_list) - 1
        queue.put((t, image[None], intrinsics[None], is_last))

    time.sleep(10)


def save_trajectory(slam, traj_full, imagedir, output, start=0, length=100000):
    t = slam.video.counter.value
    tstamps = slam.video.tstamp[:t]
    poses_wc = lietorch.SE3(slam.video.poses[:t]).inv().data
    np.save(f"{output}/intrinsics.npy", slam.video.intrinsics[0].cpu().numpy() * 8)

    image_list = sorted(os.listdir(imagedir))[start : start + length]
    tstamps_full = np.array(
        [float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1]) for name in image_list]
    )[..., np.newaxis]
    tstamps_kf = tstamps_full[tstamps.cpu().numpy().astype(int)]
    ttraj_kf = np.concatenate([tstamps_kf, poses_wc.cpu().numpy()], axis=1)
    np.savetxt(f"{output}/traj_kf.txt", ttraj_kf)

    if traj_full is not None:
        ttraj_full = np.concatenate([tstamps_full[: len(traj_full)], traj_full], axis=1)
        np.savetxt(f"{output}/traj_full.txt", ttraj_full)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run G--SLAM on a monocular image sequence.")
    parser.add_argument("--imagedir", type=str, help="Path to the image directory.")
    parser.add_argument("--calib", type=str, help="Path to the camera calibration file.")
    parser.add_argument("--config", type=str, help="Path to the configuration file.")
    parser.add_argument("--output", default="outputs/demo", help="Directory used to save outputs.")
    parser.add_argument(
        "--gtdepthdir",
        type=str,
        default=None,
        help="Optional depth directory for rendering evaluation. Assumes 16-bit depth scaled by 6553.5.",
    )
    parser.add_argument(
        "--weights",
        default=os.path.join(os.path.dirname(__file__), "pretrained_models/droid.pth"),
        help="Path to the DROID-SLAM weights.",
    )
    parser.add_argument(
        "--buffer",
        type=int,
        default=-1,
        help="Number of keyframes to pre-allocate. Defaults to a heuristic based on sequence length.",
    )
    parser.add_argument(
        "--undistort",
        action="store_true",
        help="Undistort images when distortion parameters are present in the calibration file.",
    )
    parser.add_argument("--cropborder", type=int, default=0, help="Crop border size in pixels.")
    parser.add_argument("--droidvis", action="store_true", help="Visualize intermediate SLAM states.")
    parser.add_argument("--gsvis", action="store_true", help="Visualize the Gaussian map.")
    parser.add_argument("--start", type=int, default=0, help="Start frame index.")
    parser.add_argument("--length", type=int, default=100000, help="Number of frames to process.")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    torch.multiprocessing.set_start_method("spawn")

    queue = Queue(maxsize=8)
    reader = Process(
        target=mono_stream,
        args=(queue, args.imagedir, args.calib, args.undistort, args.cropborder, args.start, args.length),
    )
    reader.start()

    image_list = sorted(os.listdir(args.imagedir))[args.start : args.start + args.length]
    n_images = len(image_list)
    args.buffer = min(1000, n_images // 10 + 150) if args.buffer < 0 else args.buffer

    slam = None
    pbar = tqdm(range(n_images), desc="Processing keyframes")
    while True:
        t, image, intrinsics, is_last = queue.get()
        pbar.update()

        if slam is None:
            args.image_size = [image.shape[2], image.shape[3]]
            slam = G2(args)

        slam.track(t, image, intrinsics=intrinsics, is_last=is_last)

        if args.droidvis and slam.video.tstamp[slam.video.counter.value - 1] == t:
            from geom.ba import get_prior_depth_aligned

            index = slam.video.counter.value - 2
            depth_prior, _ = get_prior_depth_aligned(
                slam.video.disps_prior_up[index][None].cuda(),
                slam.video.dscales[index][None],
            )
            show_image(
                image[0],
                1.0 / depth_prior.squeeze(),
                1.0 / slam.video.disps_up[index],
                slam.video.normals[index],
            )

        pbar.set_description(
            f"Processing keyframe {slam.video.counter.value} gs {slam.gs.gaussians._xyz.shape[0]}"
        )

        if is_last:
            pbar.close()
            break

    reader.join()

    traj = slam.terminate()
    save_trajectory(slam, traj, args.imagedir, args.output, start=args.start, length=args.length)
    print("Done")
