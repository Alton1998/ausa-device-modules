import cv2 as cv
import torch
import numpy as np
from PIL import Image
from transformers import pipeline
import open3d as o3d

device = "cuda" if torch.cuda.is_available() else "cpu"

depth_pipe = pipeline("depth-estimation", model="LiheYoung/depth-anything-small-hf", device=0 if device == "cuda" else -1)

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

vis = o3d.visualization.Visualizer()
vis.create_window(window_name='Open3D Point Cloud')

global_pcd = o3d.geometry.PointCloud()
added = False

def create_gyro_extrinsic(angle_deg):
    angle_rad = np.radians(angle_deg)
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    R = np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ])
    extrinsic = np.eye(4)
    extrinsic[:3, :3] = R
    return extrinsic

frame_idx = 0
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        height, width = frame.shape[:2]
        image = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))

        depth_np = np.array(depth_pipe(image)["depth"])
        depth_scaled = (depth_np / depth_np.max() * 1000).astype(np.uint16)

        color_o3d = o3d.geometry.Image(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
        depth_o3d = o3d.geometry.Image(depth_scaled)

        focal_length = 0.5 * (width + height)
        intrinsic = o3d.camera.PinholeCameraIntrinsic()
        intrinsic.set_intrinsics(width, height,
                                 fx=focal_length, fy=focal_length,
                                 cx=width / 2, cy=height / 2)

        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color_o3d, depth_o3d,
            depth_scale=1000.0,
            convert_rgb_to_intensity=False
        )

        pcd_tmp = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)

        extrinsic = create_gyro_extrinsic(frame_idx % 360)
        pcd_tmp.transform(extrinsic)

        pcd_tmp.transform([[1, 0, 0, 0],
                           [0, -1, 0, 0],
                           [0, 0, -1, 0],
                           [0, 0, 0, 1]])

        # FIXED: accumulate in a new point cloud, then update in-place
        combined_pcd = global_pcd + pcd_tmp
        combined_pcd = combined_pcd.voxel_down_sample(voxel_size=0.01)

        global_pcd.points = combined_pcd.points
        global_pcd.colors = combined_pcd.colors

        if not added:
            vis.add_geometry(global_pcd)
            added = True
        else:
            vis.update_geometry(global_pcd)

        vis.poll_events()
        vis.update_renderer()

        cv.imshow("Video", frame)
        cv.imshow("Depth", depth_np / depth_np.max())

        frame_idx += 1
        if cv.waitKey(1) == ord('q'):
            break

finally:
    cap.release()
    cv.destroyAllWindows()
    vis.destroy_window()
