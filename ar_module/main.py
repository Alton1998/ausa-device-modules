import cv2 as cv
import pyrender
import torch
import trimesh
from transformers import (
    AutoProcessor,
    RTDetrForObjectDetection, VitPoseForPoseEstimation, AutoImageProcessor, AutoModelForDepthEstimation, pipeline,
)
from PIL import Image
from scipy.linalg import inv
import numpy as np
print("CUDA is available:")
print(torch.cuda.is_available())

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Device:")
print(device)


person_image_processor = AutoProcessor.from_pretrained("PekingU/rtdetr_r50vd_coco_o365")
person_model = RTDetrForObjectDetection.from_pretrained("PekingU/rtdetr_r50vd_coco_o365", device_map=device)
image_processor = AutoProcessor.from_pretrained("usyd-community/vitpose-base-simple")
model = VitPoseForPoseEstimation.from_pretrained("usyd-community/vitpose-base-simple", device_map=device)
depth_pipe = pipeline("depth-estimation", model="hf-tiny-model-private/tiny-random-GLPNForDepthEstimation")

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
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
    person_boxes = result["boxes"][result["labels"]==0].cpu().numpy()
    person_boxes[:, 2] = person_boxes[:, 2] - person_boxes[:, 0]
    person_boxes[:, 3] = person_boxes[:, 3] - person_boxes[:, 1]

    inputs = image_processor(image, boxes=[person_boxes], return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    pose_results = image_processor.post_process_pose_estimation(outputs, boxes=[person_boxes], threshold=0.3)
    image_pose_result = pose_results[0]  # results for first image
    depth = depth_pipe(image)["depth"]

    for i, person_pose in enumerate(image_pose_result):
        bp = dict()
        for keypoint, label, score in zip(
                person_pose["keypoints"], person_pose["labels"], person_pose["scores"]
        ):
            keypoint_name = model.config.id2label[label.item()]
            if keypoint_name=="R_Shoulder" or keypoint_name=="R_Elbow":
                x, y = keypoint
                z = np.array(depth)[int(x)][int(y)]
                cv.circle(frame, (int(x),int(y)), radius=4, color=(0, 0, 255), thickness=-1)
                bp[keypoint_name]=np.array([x,y,z])
        cv.imshow('frame',frame)

    if cv.waitKey(1) == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv.destroyAllWindows()


