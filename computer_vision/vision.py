import classify, color_correct, measure
import numpy as np
import cv2
from cv_utils import *

# Given an image, an instance of classify.FoliageClassifier, and
#    an instance of mesure.MeasureHeight and returns three values:
# 1. An image with all non-foliage parts masked out
# 2. The original image with overlaid with the stick mask and
#    a line at the height of the foliage, if any
# 3. The height of the foliage
def foliageImages (target_image, classifier, measurer):
    foliage_image, height_image, height = None, None, -1
    # BEGIN STUDENT CODE
    # 1
    # Classifier process
    preprocessed_image = classifier.preprocessImage(target_image)
    foliage_mask = classifier.model.predict(preprocessed_image)
    foliage_mask = classifier.postprocessMask(foliage_mask, target_image.shape[0:2])

    stacked_foliage_mask = np.stack((foliage_mask, foliage_mask, foliage_mask), axis=-1)
    foliage_image = np.uint8(np.where(stacked_foliage_mask != 0, target_image, 0))

    '''window_name = "Foliage Image"
    createWindow(wname=window_name)
    showImageWait(wname=window_name, image=foliage_image)'''

    # 2
    stick_mask = measurer.stick_mask
    height_image = overlayMask(target_image, stick_mask)
    height, top_row = measurer.measure(foliage_mask) # 3
    # print(f"Estimated height and row: {height}/{top_row}")

    if height is not None and top_row is not None:
        # Find left/right bounds of stick mask
        cols = np.any(stick_mask == 255, axis=0).reshape(-1)
        left, right = cols.argmax(), len(cols) - np.flip(cols).argmax()
        # print(f"Estimated L/R: ({left},{right})")

        # Draw line
        START, END = (left - 50, top_row), (right + 50, top_row)
        COLOR = (255, 0, 0)
        THICKNESS = 7
        cv2.line(height_image, START, END, COLOR, THICKNESS)

        '''window_name = "Height Image"
        createWindow(wname=window_name)
        showImageWait(wname=window_name, image=height_image)'''

    # END STUDENT CODE
    return foliage_image, height_image, height

# Given an image, return two values:
# 1. The percentage of foliage in the image
# 2. The height of the plans
# 2. An estimate of the plant health (as a string), compared to the reference
#    foliage percentage and height.
def plantHealth (target_image, classifier, measurer, prev_greenery, prev_height):
    greenery, height, health_msg = 0, 0, ""
    # BEGIN STUDENT CODE
    preprocessed_image = classifier.preprocessImage(target_image)
    foliage_mask = classifier.model.predict(preprocessed_image)
    foliage_mask = classifier.postprocessMask(foliage_mask, target_image.shape[0:2])
    greenery = np.sum(foliage_mask == 1) / (np.sum(foliage_mask == 0) + np.sum(foliage_mask != 0))
    height = measurer.measure(foliage_mask)[0]
    if height is None or prev_height is None:
        print('hi')
        if greenery < prev_greenery:
            health_msg = "bad: greenery less than previous estimates"
        else:
            health_msg = "good: greenery greater than or equal to previous estimates"
    else: 
        if greenery < prev_greenery and height < prev_height:
            health_msg = "bad: greenery and height less than previous estimates"
        elif greenery < prev_greenery and height >= prev_height:
            health_msg = "ok: greenery is less than previous, but height is equal or taller"
        elif greenery >= prev_greenery and height < prev_height:
            health_msg = "ok: greenery is equal or more than previous, but height is shorter"
        elif greenery >= prev_greenery and height >= prev_height:
            health_msg = "good: greenery and height has both improved"
    # END STUDENT CODE
    return greenery, height, health_msg

