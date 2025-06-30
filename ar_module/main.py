import cv2 as cv
import torch
import numpy as np
from PIL import Image
from transformers import (
    AutoProcessor,
    RTDetrForObjectDetection,
    VitPoseForPoseEstimation,
    pipeline,
)
import open3d as o3d

device = "cuda" if torch.cuda.is_available() else "cpu"


person_image_processor = AutoProcessor.from_pretrained("PekingU/rtdetr_r50vd_coco_o365")
person_model = RTDetrForObjectDetection.from_pretrained("PekingU/rtdetr_r50vd_coco_o365", device_map=device)
pose_processor = AutoProcessor.from_pretrained("usyd-community/vitpose-base-simple")
pose_model = VitPoseForPoseEstimation.from_pretrained("usyd-community/vitpose-base-simple", device_map=device)
depth_pipe = pipeline("depth-estimation", model="LiheYoung/depth-anything-small-hf", device=0 if device == "cuda" else -1)

# Webcam
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Open3D visualizer
vis = o3d.visualization.Visualizer()
vis.create_window(window_name='Open3D Point Cloud')
pcd = o3d.geometry.PointCloud()
added = False

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        height, width = frame.shape[:2]
        image = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))  # Use RGB input for depth-anything

        # Object detection
        inputs = person_image_processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = person_model(**inputs)
        results = person_image_processor.post_process_object_detection(
            outputs, target_sizes=torch.tensor([(image.height, image.width)]), threshold=0.3
        )
        result = results[0]

        person_boxes = result["boxes"][result["labels"] == 0].cpu().numpy()
        if len(person_boxes) > 0:
            person_boxes[:, 2] -= person_boxes[:, 0]
            person_boxes[:, 3] -= person_boxes[:, 1]

            # Pose estimation
            inputs_pose = pose_processor(image, boxes=[person_boxes], return_tensors="pt").to(device)
            with torch.no_grad():
                outputs_pose = pose_model(**inputs_pose)
            pose_results = pose_processor.post_process_pose_estimation(outputs_pose, boxes=[person_boxes], threshold=0.3)
            image_pose_result = pose_results[0]

            overlay = frame.copy()
            for person_pose in image_pose_result:
                keypoints = {}
                for keypoint, label, score in zip(
                        person_pose["keypoints"], person_pose["labels"], person_pose["scores"]
                ):
                    kp_name = pose_model.config.id2label[label.item()]
                    x, y = keypoint
                    keypoints[kp_name] = (int(x), int(y))
                if "R_Shoulder" in keypoints and "R_Elbow" in keypoints:
                    pt1 = keypoints["R_Shoulder"]
                    pt2 = keypoints["R_Elbow"]
                    alpha = 0.9
                    mid = tuple((pt1[i] + pt2[i]) / 2 for i in range(len(pt1)))
                    pt1_new = tuple(int(pt1[i] + alpha * (mid[i] - pt1[i])) for i in range(len(pt1)))
                    pt2_new = tuple(int(pt2[i] + alpha * (mid[i] - pt2[i])) for i in range(len(pt1)))
                    color_alpha = 0.4
                    blue_color = (255, 0, 0)
                    thickness = 100
                    cv.line(overlay, pt1_new, pt2_new, blue_color, thickness)
                    cv.addWeighted(overlay, color_alpha, frame, 1 - color_alpha, 0, frame)

        depth_np = np.array(depth_pipe(image)["depth"])
        depth_scaled = (depth_np / depth_np.max() * 1000).astype(np.uint16)

        # Convert to Open3D images
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        color_o3d = o3d.geometry.Image(frame_rgb)
        depth_o3d = o3d.geometry.Image(depth_scaled)

        # Set intrinsics with focal length approx
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

        pcd_tmp.transform([[1, 0, 0, 0],
                           [0, -1, 0, 0],
                           [0, 0, -1, 0],
                           [0, 0, 0, 1]])

        if not added:
            pcd.points = pcd_tmp.points
            pcd.colors = pcd_tmp.colors
            vis.add_geometry(pcd)
            added = True
        else:
            pcd.points = pcd_tmp.points
            pcd.colors = pcd_tmp.colors
            vis.update_geometry(pcd)

        vis.poll_events()
        vis.update_renderer()
        cv.imshow("Video", frame)
        cv.imshow("Depth", depth_np / depth_np.max())

        if cv.waitKey(1) == ord('q'):
            break

finally:
    cap.release()
    cv.destroyAllWindows()
    vis.destroy_window()
