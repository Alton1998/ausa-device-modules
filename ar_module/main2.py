import torch
import numpy as np
import cv2
from PIL import Image
import open3d as o3d
from transformers import pipeline

# --------------------------------------
# Step 1: Load RGB image and estimate depth using Depth Anything
# --------------------------------------

# Load RGB image
rgb_path = "frame.png"
image = Image.open(rgb_path).convert("RGB")

# Load Depth Anything model
depth_anything = pipeline(task="depth-estimation", model="LiheYoung/depth-anything-small-hf")

# Predict depth
depth_result = depth_anything(image)
depth = depth_result["depth"]

# Convert to numpy array
depth_np = np.array(depth)

# Normalize depth for visualization or to use as 16-bit image
depth_min = depth_np.min()
depth_max = depth_np.max()
depth_norm = (depth_np - depth_min) / (depth_max - depth_min)  # normalize to 0-1
depth_16bit = (depth_norm * 1000).astype(np.uint16)  # Scale to simulate "millimeter" style

# Save depth image (optional)
cv2.imwrite("depth_anything.png", depth_16bit)

# --------------------------------------
# Step 2: Load RGB and estimated depth into Open3D
# --------------------------------------

# Load images in Open3D
color_raw = o3d.io.read_image(rgb_path)
depth_raw = o3d.io.read_image("depth_anything.png")

# Get dimensions
width = np.asarray(color_raw).shape[1]
height = np.asarray(color_raw).shape[0]
print("Image dimensions:", width, height)

# Approximate intrinsics (adjust fx, fy if you know actual values!)
intrinsic = o3d.camera.PinholeCameraIntrinsic()
intrinsic.set_intrinsics(width, height,
                         fx=360, fy=360,
                         cx=width / 2, cy=height / 2)

# Create RGBD image
rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
    color_raw, depth_raw,
    depth_scale=1000.0,   # Matches the *1000 above to simulate millimeter depth
    convert_rgb_to_intensity=False
)

# Create point cloud
pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)

# Optionally transform to match Open3D view convention
pcd.transform([[1, 0, 0, 0],
               [0, -1, 0, 0],
               [0, 0, -1, 0],
               [0, 0, 0, 1]])

# Visualize
o3d.visualization.draw_geometries([pcd])
