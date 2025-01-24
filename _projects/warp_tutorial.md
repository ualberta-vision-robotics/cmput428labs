---
layout: page
title: Lab 1.2 - Tracking
description:
permalink: /warp_tutorial
img: 
category: Motion Estimation and Tracking
related_publications: false
---

## Overview

This page will cover warping with OpenCV. We will show how to warp by manually finding our warped coordinates and then show how we can use OpenCV's built in functions. We first define the warp functions:

\begin{equation}
\mathrm{~W}(\mathbf{x}, \mathbf{p})=\binom{\mathrm{p}_1 \mathrm{x}+\mathrm{p}_3 \mathrm{y}+\mathrm{p}_5}{\mathrm{p}_2 \mathrm{x}+\mathrm{p}_4 \mathrm{y}+\mathrm{p}_6} \\
\end{equation}
\begin{equation}
\mathrm{~W}(\mathbf{x}, \mathbf{p})=\frac{1}{1+p_7 x+p_8 y}\binom{\mathrm{p}_1 \mathrm{x}+\mathrm{p}_3 \mathrm{y}+\mathrm{p}_5}{\mathrm{p}_2 \mathrm{x}+\mathrm{p}_4 \mathrm{y}+\mathrm{p}_6}
\end{equation}

These serve as the basis for our transformations.

---

## Warping with remap

```python
h, w = img.shape[:2]
X = np.arange(0, w, 1, dtype=int)
Y = np.arange(0, h, 1, dtype=int)
X, Y = np.meshgrid(X, Y)
```
Here X and Y are the coordinate grids for our system. We will use them with remap to warp our function. Let's call remap on the source image using these coordinates.

```python
img_remapped = cv2.remap(img, X, Y, cv2.INTER_LINEAR)
cv2.imshow("remapped", img_remapped)
cv2.imshow("original", img)
cv2.waitKey(0)
```
When we display our remapped image, we can see that nothing changed. This is because X and Y contain the unwarped coordinate grid of our image.

What remap is doing is for every pixel `img_remapped[i,i]`, we take find its intensity from `img[X[i,i], Y[i,i]]`. How interpixel values are treated is defined by the cv2.INTER_LINEAR flag.

Let's try warping our image.

```python
Affine = np.array([[1, 0.2, 10], [0.1, 1, 10]])
Homography = np.array([[1, 0, 0], [0, 1, 0], [0.0004, 0, 1]])

h, w = img.shape[:2]
X = np.arange(0, w, 1, dtype=int)
Y = np.arange(0, h, 1, dtype=int)
X, Y = np.meshgrid(X, Y)

coords_homogeneous = np.array([X.flatten(), Y.flatten(), np.ones_like(X).flatten()])

# matrix multiplication to apply equation 1
warped_affine_coords = Affine @ coords_homogeneous
# our coordinates are now warped, we reshape them back to match the source shape
warped_affine_X = warped_affine_coords[0].reshape(img.shape).astype(np.float32)
warped_affine_Y = warped_affine_coords[1].reshape(img.shape).astype(np.float32)
# grabbing pixels from source image according to these new coordinates
affine_img = cv2.remap(img, warped_affine_X, warped_affine_Y, cv2.INTER_LINEAR)

# matrix multiplication to apply equation 2
warped_homo_coords = Homography @ coords_homogeneous
# we divide by the last element in each column to ensure homogeneity (basically, all same scale)
warped_homo_X, warped_homo_Y = warped_homo_coords[:-1]/warped_homo_coords[-1]
# reshaping back to source shape
warped_homo_X = warped_homo_X.reshape(img.shape).astype(np.float32)
warped_homo_Y = warped_homo_Y.reshape(img.shape).astype(np.float32)
# grabbing pixels from source image according to these new coordinates
homo_img = cv2.remap(img, warped_homo_X, warped_homo_Y, cv2.INTER_LINEAR)

# comparing these warped images
cv2.imshow("affine", affine_img)
cv2.imshow("homography", homo_img)
cv2.imshow("original", img)
cv2.waitKey(0)

```

--- 

## Grabbing a template with remap
Instead of defining our coordinate system in the entire image, let's define it just in our region of interest.

```python
roi = (38, 323, 178, 204)
img0 = cv2.cvtColor(cv2.imread("./cereal/frame00001.jpg"), cv2.COLOR_BGR2GRAY)
img = cv2.cvtColor(cv2.imread("./cereal/frame00212.jpg"), cv2.COLOR_BGR2GRAY)
template = img0[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]

# meshgrid in full image coordinates
h, w = img.shape[:2]
X = np.arange(0, w, 1, dtype=int)
Y = np.arange(0, h, 1, dtype=int)
X, Y = np.meshgrid(X, Y)
# cropping to roi
template_X = X[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
template_Y = Y[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
# creating homogenous coordinate system
template_homogeneous = np.array([template_X.flatten(), template_Y.flatten(), np.ones_like(template_X).flatten()])
```

Now let's warp our template coordinates:

```python
Affine = np.array([[-3.9929888e-01, -7.6305789e-01, 8.6678418e+02],
 [ 7.4395186e-01, -3.7666887e-01,  3.9476602e+02]])
# matrix multiplication to apply equation 1
warped_roi_coords = Affine @ template_homogeneous
# our coordinates are now warped, we reshape them back to match the template shape
warped_roi_X = warped_roi_coords[0].reshape(template_X.shape).astype(np.float32)
warped_roi_Y = warped_roi_coords[1].reshape(template_X.shape).astype(np.float32)
# grabbing pixels from source image according to these new coordinates
affine_img = cv2.remap(img, warped_roi_X, warped_roi_Y, cv2.INTER_LINEAR)

cv2.imshow("warped roi", affine_img)
cv2.imshow("template", template)
cv2.imshow("first frame", img0)
cv2.imshow("current frame", img)
cv2.waitKey(0)
```

Visualize these yourself and you should see a match!

---

## Warping with built-in functions

We can warp with OpenCV's built-in functions using the following format. Make sure cv2.WARP_INVERSE_MAP is entered as a flag to see warps in the way we've defined them in this course.

```python
warp = cv2.warpAffine(img, Affine, img.shape, flags=cv2.WARP_INVERSE_MAP)
```

We can also crop the warped image like so:

```python
warped_template = cv2.warpAffine(img, Affine, img.shape, flags=cv2.WARP_INVERSE_MAP)[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
```

It's important to not use these functions blindly. 

I recommend you test your code with remap to gain a deeper understanding of what our code is actually doing during the development phase, and then switch over to these built-in functions later.
To plot a bounding box, I like to use `cv2.polylines()`. To construct the corner points for your box, warp the points of your original roi with `@`.
Lastly, by change the source image of `remap()` or `warpAffine()` to the spatial gradients, we can obtain warped versions of our gradients too! Try this out for yourself!

