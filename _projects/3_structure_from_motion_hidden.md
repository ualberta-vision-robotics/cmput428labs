---
layout: page
title: Lab 3 - Structure from Motion
description:
permalink: /structurefrommotion_HIDDEN
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

__Important: You can obtain 2 bonus marks for each section you finish and demo while present during the lab period we introduce the lab.__

__Lab Introduction Slides:__ [available here](https://drive.google.com/file/d/1WO_6l_5ahdXfd3KD4GXC_8o5GZIDWVxt/view?usp=drive_link)


## Prelab Questions (5%)

The link to the prelab questions [can be found here](https://docs.google.com/document/d/1fvlDDaNz-Rpgvy0fRTXoXno6cYgGdCDelvnrAFbNlWU/edit?usp=sharing). You will need your University of Alberta email for access; they are also available under the Canvas assignment. __Due Tuesday, March 3rd at 5pm.__ 

---

## Setup

__First, download the lab code and report templates.__ These contain the structure for your report, and the file structure for your code. You can write your code however you wish within the files; however, please ensure that it is adequately commented, and that each part of the lab can be run by running the file corresponding to that question.

You will need to use your University of Alberta email to access the below templates.

Code template: [can be found here.](https://drive.google.com/file/d/1Ekj8H6lKf_nT5LgrRhr1Vs7xFEdgSzqN/view?usp=drive_link)

Report template: [can be found here.](https://docs.google.com/document/d/1__gIg8VwW_CSDC29df8aPO6hyBeuQaVjwcyFKl6CP4A/edit?usp=sharing)

---

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
- Final submission format: a single zip file named `CompVisW26_lab3_lastname_firstname.zip` containing the above structure.
- Your report for Lab 3 is to be submitted at a later date. The report contains all media, results, and answers as specified in the instructions above. Ensure your answers are concise and directly address the questions.
- Total marks for this lab is __100__ for all students. Your lab assignment grade with bonus marks is capped at __110%__.
