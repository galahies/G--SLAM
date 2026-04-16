import os
import sys

import cv2
from tqdm import tqdm


def extract_frames(input_video_path, output, output_colmap):
    os.makedirs(output, exist_ok=True)
    os.makedirs(output_colmap, exist_ok=True)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Couldn't open video file.")
        return

    frame_number = 0
    pbar = tqdm(total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), desc="Extracting frames")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imwrite(os.path.join(output, f"{frame_number:06d}.jpg"), frame)

        if frame_number % 10 == 0 and frame_number < 1000:
            cv2.imwrite(os.path.join(output_colmap, f"{frame_number:06d}.jpg"), frame)

        frame_number += 1
        pbar.update(1)

    pbar.close()
    cap.release()


def run_colmap(output):
    colmap_binary = "colmap"
    db = f"{output}/colmap.db"
    images = f"{output}/images_colmap"

    os.system(
        f"{colmap_binary} feature_extractor "
        f"--ImageReader.camera_model OPENCV "
        f"--SiftExtraction.estimate_affine_shape=true "
        f"--SiftExtraction.domain_size_pooling=true "
        f"--ImageReader.single_camera 1 "
        f"--database_path {db} --image_path {images}"
    )
    os.system(f"{colmap_binary} sequential_matcher --SiftMatching.guided_matching=true --database_path {db}")
    os.system(f"mkdir -p {output}/sparse")
    os.system(f"{colmap_binary} mapper --database_path {db} --image_path {images} --output_path {output}/sparse")
    os.system(
        f"{colmap_binary} bundle_adjuster "
        f"--input_path {output}/sparse/0 "
        f"--output_path {output}/sparse/0 "
        f"--BundleAdjustment.refine_principal_point 1"
    )
    os.system(f"mkdir -p {output}/sparse_txt")
    os.system(
        f"{colmap_binary} model_converter "
        f"--input_path {output}/sparse/0 "
        f"--output_path {output}/sparse_txt "
        f"--output_type TXT"
    )


if __name__ == "__main__":
    input_video_path = sys.argv[1]
    output = sys.argv[2]

    extract_frames(input_video_path, output + "/images", output + "/images_colmap")
    run_colmap(output)

    calib = open(f"{output}/sparse_txt/cameras.txt").readlines()[-1].split()[4:]
    open(f"{output}/calib.txt", "w").write(" ".join(calib))
