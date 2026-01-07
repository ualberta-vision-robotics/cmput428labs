---
layout: page
title: Lab 3 - Structure from Motion
description:
permalink: /structurefrommotion
img: 
importance: 1
category: Structure from Motion
related_publications: false
---
<div class="row justify-content-sm-center">
    <div class="col-sm-4 mt-3 mt-md-0">
        {% include figure.liquid path="assets/img/max_head1.webp" title="3D mesh of head" class="img-fluid rounded z-depth-1" %}
    </div>
    <div class="col-sm-4 mt-3 mt-md-0">
        {% include figure.liquid path="assets/img/max_head2.webp" title="Tracked feature points" class="img-fluid rounded z-depth-1" %}
    </div>
    <div class="col-sm-4 mt-3 mt-md-0">
        {% include figure.liquid path="assets/img/max_head3.webp" title="Fill matrix visualization" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
Left: 3D mesh of head reconstructed from a sequence of 60 orthographic images. <br>
Middle: Sequence of tracked feature points on ground truth mesh viewed from an orthographic camera. <br>
Right: Fill matrix visualization showing gradual accumulation of observations across frames (shaded entries are known image coordinates).
</div>

## Overview

In this assignment you will implement an **affine factorization** method for structure from motion. You will then extend it to handle **missing data** (occlusions) via matrix completion, and perform a **metric upgrade** to recover the true Euclidean structure. You will test your implementation on provided datasets and on your own videos, and document your results with code, figures, and analysis.

__Important: You can obtain 3 bonus marks for each section you finish and demo while present during the lab period we introduce the lab.__

---
## Lab questions will be available before the introductory session.
---
---

## Submission Details

- Include accompanying code used to complete each question. Ensure they are adequately commented.
- Ensure all functions are and sections are clearly labeled in your report to match the tasks and deliverables outlined in the lab.
- Organize files as follows:
  - `code/` folder containing all scripts used in the assignment.
  - `media/` folder for images, videos, and results.
- Final submission format: a single zip file named `CompVisW25_lab3_lastname_firstname.zip` containing the above structure.
- Your report for Lab 3 is to be submitted at a later date. The report contains all media, results, and answers as specified in the instructions above. Ensure your answers are concise and directly address the questions.
- Total marks for this lab is __100__ for all students. Your lab assignment grade with bonus marks is capped at __130%__.
