import numpy as np
import cv2

# Simulate a 3D volume
volume = np.random.randint(0, 255, (50, 256, 256), dtype=np.uint8)

# Show the middle slice
cv2.imshow("Mid Slice", volume[25])
cv2.waitKey(0)
cv2.destroyAllWindows()
