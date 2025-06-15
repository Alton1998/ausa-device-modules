import cv2 as cv
import torch
import numpy as np
from PIL import Image
from transformers import (
    AutoProcessor,
    RTDetrForObjectDetection, VitPoseForPoseEstimation, pipeline,
)

device = "cuda" if torch.cuda.is_available() else "cpu"

person_image_processor = AutoProcessor.from_pretrained("PekingU/rtdetr_r50vd_coco_o365")
person_model = RTDetrForObjectDetection.from_pretrained("PekingU/rtdetr_r50vd_coco_o365", device_map=device)
pose_processor = AutoProcessor.from_pretrained("usyd-community/vitpose-base-simple")
pose_model = VitPoseForPoseEstimation.from_pretrained("usyd-community/vitpose-base-simple", device_map=device)
# depth_pipe = pipeline("depth-estimation", model="hf-tiny-model-private/tiny-random-GLPNForDepthEstimation")

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width = frame.shape[:2]
    image = Image.fromarray(frame)

    inputs = person_image_processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = person_model(**inputs)
    results = person_image_processor.post_process_object_detection(
        outputs, target_sizes=torch.tensor([(image.height, image.width)]), threshold=0.3
    )
    result = results[0]

    person_boxes = result["boxes"][result["labels"] == 0].cpu().numpy()
    if len(person_boxes) == 0:
        cv.imshow("frame", frame)
        if cv.waitKey(1) == ord('q'):
            break
        continue

    person_boxes[:, 2] -= person_boxes[:, 0]
    person_boxes[:, 3] -= person_boxes[:, 1]

    inputs = pose_processor(image, boxes=[person_boxes], return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = pose_model(**inputs)
    pose_results = pose_processor.post_process_pose_estimation(outputs, boxes=[person_boxes], threshold=0.3)
    image_pose_result = pose_results[0]
    depth = np.array(depth_pipe(image)["depth"])
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
    cv.imshow("frame", frame)
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
