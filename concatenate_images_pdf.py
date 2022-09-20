# concatenate_image_pdf.py - a command-line utility to convert images from a camera to neat, multi-page PDF files.
# (C) Robert Ryder, September 2022
import cv2
import PIL.Image
import numpy as np
import argparse
import logging
import math
import glob
import sys

# Parameters, with default values
THRESHOLD_AMOUNT = 120  # Control the necessary lightness for the threshold to use white.
MARGIN_ESTIMATE = 150  # A rough estimate of how far the paper is from the edge of the image; used in the auto-rotate logic.

def rotate_image(img, theta):
    rot_mat = cv2.getRotationMatrix2D((img.shape[1] // 2, image.shape[0] // 2), theta, 1.0)  #  compute the rotation matrix
    rtd = cv2.warpAffine(img, rot_mat, (w, h))  # apply the transformation
    return rtd  # pass the result back to the main function, from which this convenience routine is called.

def auto_rotate(img, w, h):
    # Ensure that the page is aligned straight with the image. Depending on the angle from which the photograph was taken, the top may look wider than the bottom or vice versa.
    # There are three potential solutions to this problem: leave portions of the background in, cut portions of the margins out, or warp the page to make it a perfect square.
    # As written, this code exhibits a mix of the latter two depending on the effect.
    
    # store measurements
    left_check = 0
    right_check = 0
    
    # check the left side
    for i in range(h):
        pxl = img[i, MARGIN_ESTIMATE]
        if (int(pxl[0]) + int(pxl[1]) + int(pxl[2])) > 449:  # RGB is at least (150, 150, 150)
            left_check = i  # mark the spot; this is the distance of the paper's edge from the image boundary
            break  # Veni Vici Inveni Exiti - I came, I saw, I found, I exited - stop here(I hope the Latin is correct).

    # check the right side
    for i in range(h):
        pxl = img[i, w-MARGIN_ESTIMATE]
        if (int(pxl[0]) + int(pxl[1]) + int(pxl[2])) > 449:  # RGB is at least (150, 150, 150)
            right_check = i
            break
        
    theta = 0
    hdist = w - (2*MARGIN_ESTIMATE)
    vdist = 0
    if left_check < right_check:
        # rotate right, negative angle
        log.debug('rotating right with negative angle')
        vdist = right_check - left_check  # always positive, due to the conditional
        log.info('horizontal distance: %d\tvertical distance: %d' % (hdist, vdist))
        theta = math.atan(vdist / hdist)  # the opposite side over the adjacent yields the necessary angle.
        theta *= -1  # make the angle negative to rotate in the desired direction.
        
    elif left_check > right_check:
        # rotate left, positive angle,
        log.debug('rotating left with a positive angle')
        vdist = left_check - right_check
        log.info('horizontal distance: %d\tvertical distance %d' % (hdist, vdist))
        theta = math.atan(vdist / hdist)

    else:
        # if the values are equal, don't bother to rotate.
        return img

    #rotate the image with the angle determined above.
    mat = cv2.getRotationMatrix2D((w // 2, h //2), theta, 1.0)  # use floor division to avoid decimal values in computing the center of the image
    rot = cv2.warpAffine(img, mat, (w, h))

    return rot  # pass the result back to process_image()

def process_image(path):
    # Generate image for OpenCV internals/finding contours - that requires a threshold map.
    img = cv2.imread(path)
    img = auto_rotate(img, img.shape[1]-1, img.shape[0]-1)
    gsc = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thold = cv2.threshold(gsc, THRESHOLD_AMOUNT, 255, cv2.THRESH_BINARY)[1]

    # Find contours and crop accordingly.
    ctr = cv2.findContours(thold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(ctr) == 2:
        ctr = ctr[0]
    else:
        ctr = ctr[1]

    ctr = sorted(ctr, key=cv2.contourArea, reverse=True) # the largest contour is the main focus of the image; put that one first.

    # Crop based on image contours
    x, y, w, h = cv2.boundingRect(ctr[0])
    tmp = img[y:y+h, x:x+w]

    # Sometimes, the above will leave portions of the border visible in the final shot - I have most often observed this phenomenon on the top and right hand margins.
    # To correct for this, iterate over the pixels from the edge (correcting for the right means this must be in reverse) and detect an abrupt change in color/brightness.
    extra_crop_right = tmp.shape[1]
    extra_crop_top = tmp.shape[0]

    # The logic to check for adjustment is essentially the same as that used to determine the proper angle for auto-rotation as used above. Conseqently, the explanation is less verbose here.
    # Horizontal adjustment:
    for i in range(w-1):
        pxl = tmp[MARGIN_ESTIMATE, w-i-1]  # Without subtracting 1, this will read the index at the len() of tmp and thus cause an IndexError
        log.info('horizontal pixel values: %d %d %d \t total: %d' % ( pxl[0], pxl[1], pxl[2], (int(pxl[0]) + int(pxl[1]) + int(pxl[2]))))
        # To compute the sum of pixel values, each of red, green, and blue must explicitly be converted to int. If this type cast is omitted, the result will not come out properly. I don't profess to know why this is - I assume it has something to do with miscelllaneous arcana of the OpenCV internals.
        if (int(pxl[0]) + int(pxl[1]) + int(pxl[2])) > 449:  # assume that the paper has an RGB value of at least (150, 150, 150) and that the background does not.
            log.info('edge detected')
            extra_crop_right = w - i  # The new width of the image is the width of tmp subtracting whatever pixels exist past the edge - this is the number of cycles that the loop has run.
            break
        
    # Vertical adjustment
    for i in range(h-1):
        pxl = tmp[i, MARGIN_ESTIMATE]
        log.info('vertical pixel values: %d, %d, %d, total %d', pxl[0], pxl[1], pxl[2], (int(pxl[0]) + int(pxl[1]) + int(pxl[2])))
        if (int(pxl[0]) + int(pxl[1]) + int(pxl[2])) > 449:
            log.info('edge detected')
            extra_crop_top = i
            break

    # Allow developer/user to sanity-check the margins
    log.info('horizontal crop: %d / %d' % (tmp.shape[0], extra_crop_right))
    log.info('vertical crop: %d / %d' % (tmp.shape[1],  extra_crop_top))

    # Crop extra margins as now determined
    extra_crop_bottom = 0
    result = tmp[extra_crop_top:tmp.shape[0], 0:extra_crop_right]

    return result  # pass to main loop

# Usage message
USAGE = '''
concatenate_images_pdf.py - a command-line utility to convert images from a camera to neat, multi-page PDF files.


Usage: python3 concatenate_images_pdf.py [OPTIONS]

Options:
-h, --help \t print this usage message and exit
-o [filename] \t specify the name/path of the output PDF file
-f [files...] \t provide a list of image files to be combined into a PDF document.
-r [regex] \t provide a regex pattern to select image files that will be combined into a PDF document. Don't use this option with expressions that the shell will automatically complete before they get to this script - that will induce an error.
-m [int] \t specify the approximate margins around the paper in each image. If unset, this defaults to 150 pixels.
-t [int] \t specify the threshold amount used to generate the map from which image contours are calculated. If unset, this defaults to 120.
-c \t concatenate images only - don't auto-crop or auto-rotate

-v \t specify whether in fact you deem it advisable to apply verbosity which may perhaps be in excess of necessary levels depending, of course, on the circumstances of the present application, or not.

Both -o and either of -f or -r must be set, unless using -h for the help message.

(C) 2022 Robert Ryder
'''

# Basic initialization
logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s %(funcName)s:%(lineno)d %(name)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)
enable_verbose_mode = lambda dest: log.setLevel(logging.INFO)

# Command-line switches
cmdline = argparse.ArgumentParser(usage=USAGE)
cmdline.add_argument('-f', dest='cli_files', metavar='N', type=str, nargs='+')
cmdline.add_argument('-r', dest='glob_regex', type=str)
cmdline.add_argument('-o', dest='pdf_output', type=str)
cmdline.add_argument('-m', dest='user_margin', type=int)
cmdline.add_argument('-t', dest='user_threshold', type=int)
cmdline.add_argument('-c', action=argparse.BooleanOptionalAction)
cmdline.add_argument('-v', action=argparse.BooleanOptionalAction)

argv = cmdline.parse_args()

if argv.v: log.setLevel(logging.INFO)

# Replace default values with user-specified ones, if applicable.
if argv.user_margin:
    MARGIN_ESTIMATE = argv.user_margin

if argv.user_threshold:
    THRESHOLD_AMOUNT = argv.user_threshold

files = []
# Determine whether to use list of files passed explicitly or a glob/regex pattern.
if argv.cli_files:
    files = argv.cli_files
elif argv.glob_regex:
    files = glob.glob(argv.glob_regex)
else:
    sys.stderr.write('please supply files using either -f or -r')
    raise SystemExit  # nothing to do.

if not argv.pdf_output:
    sys.stderr.write('please supply an output filename with -o')
    raise SystemExit

log.debug('files are: %s' % str(files))

result_pages = []
for i in files:
    try:
        # PIL is used to create the PDF files. Therefore, convert the OpenCV images to PIL images using PIL.Image.fromarray(). To do that, the color format must be converted from BGR to RGB
        # using cv2.cvtColor(). Add the result to the list of results
        if argv.c:  # check whether to do auto-rotate and auto-crop or not.
            result_pages.append(PIL.Image.open(i))
        else:
            result_pages.append(PIL.Image.fromarray(cv2.cvtColor(process_image(i), cv2.COLOR_BGR2RGB)))
    except cv2.error:
        # Sometimes, empty images occur; this causes an assertion made somewhere in the OpenCV internals to fail. This doesn't really matter for our purposes, so trap the exception.
        log.debug('%s', 'encountered an empty image; skipping it.')

result_pages[0].save(argv.pdf_output, save_all=True, append_images=result_pages[1:])  # create a multi-page PDF document of the results.
print('Result saved to ' + argv.pdf_output)
