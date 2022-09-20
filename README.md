# concatenate_images_pdf

This is a command-line application that creates neat, multi-page PDF documents from images, presumably of sheets of paper, taken using a normal camera. It will automatically rotate the image so that the page is aligned straight with the image, as well as crop automatically based both on OpenCV contours and its own checks.

---

## I. Prerequisites

1. Python 3.8+

2. The following non-standard Python modules: pillow (PIL for Python 3) and cv2 (bindings to OpenCV).

3. A few dozen megabytes of extra disk space.

---

## II. Setup and Installation

1. Clone this GitHub repository and change into its directory

   	 git clone https://github.com/thisisrobertr/images_to_pdf
	 cd images_to_pdf

#### Using a Virtual Environment

A virtual environment creates a Python environment separate from the system interpreter and package directories; it provides a sort of sandbox for a particular application. This step is optional, but it can help prevent conflicts between system packages and dependencies for this project. To create a venv, execute the following commands between steps 1 and 2:
		
		python3 -m venv venv/
		source venv/bin/activate
		
Note the `source` command: the activation script cannot be directly executed in the shell.

2. Install dependencies (if you do not already have them)

   	   pip3 install opencv-python
	   pip3 install pillow

---

## III. Using this Script

Usage: python3 images_to_pdf.py [OPTIONS]

Options:
-h, --help - print usage message and exit
-o [filename] - specify the name/path of the output PDF file
-f [files...] - provide a list of image files to be combined into a PDF document.
-r [regex] - provide a regex pattern to select image files that will be combined into a PDF document.
-m [int] - specify the approximate margins around the paper in each image. If unset, this defaults to 150 pixels.
-t [int] - specify the threshold amount used to generate the map from which image contours are calculated. If unset, this defaults to 120.
-c - only concatenate images, don't do auto-rotate or auto-crop.
-v - specify whether in fact you deem it advisable to apply verbosity which may perhaps be in excess of necessary levels depending, of course, on the circumstances of the present application, or not.

Both -o and either of -f or -r must be set, unless using -h for the help message

---

## III. Advice and Notes

- Use a background that contrasts with the paper, preferably one that is much darker. If the background is too close in brightness to the paper itself, the auto-crop will not work properly. To a degree, this can be addressed by adjusting the theshold value, but that only goes so far.

- Wood (or faux wood) that is especially light in color does not work very well.

- Pages may end up being different sizes; this script does not add any padding - bear that in mind when using it to prepare documents.

- Ideally, hold the camera directly above the page to avoid excessive parallax/linear perspective. This program will attempt to correct for that, but the image will look warped if that is doing too much.

- Usually, I e-mail images to myself from my smartphone, download them, and then run this script to create a single PDF document.

---
