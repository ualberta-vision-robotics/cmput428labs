---
layout: page
title: Get pointcloud from image example
permalink: /get_pointcloud
---

# Pointcloud Example

The below code can be used to extract a pointcloud from an image.

```python
import matplotlib.pyplot as plt
import numpy as np
import cv2

def get_point_cloud(image, scale = 1):
    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (dimy, dimx) = image.shape
    dimx = int(dimx*scale)
    dimy = int(dimy*scale)
    image = cv2.resize(image, (dimx, dimy), interpolation=cv2.INTER_AREA)
    _, image = cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    y, x = np.nonzero(image == 0)
    x = x.T
    y = -y.T + dimy
    return x, y


image = cv2.imread("bubble.jpg")
scale = 0.5
image_pts = get_point_cloud(image, scale=scale)
fig = plt.figure()

ax1 = fig.add_subplot(1, 2, 1)
plt.imshow(image)
ax1.set_aspect('equal', 'box')
plt.title("Original")

ax2 = fig.add_subplot(1, 2, 2)
plt.scatter(image_pts[0], image_pts[1], color='gray', s=1, marker='s', linewidths=0)
ax2.set_aspect('equal', 'box')
ax2.set_xlim([0, image.shape[1]*scale])
ax2.set_ylim([0, image.shape[0]*scale])
plt.title("Point Cloud")

plt.show()
```