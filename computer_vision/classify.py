import cv2, numpy as np
from cv_utils import *
from cv_learn import *

# Detect the plants in the image using a classifier model (of type MLearn).
# If modelfilename is None, create a model, o/w load it in
# isOnnx is None, determine model type using the modelfilename suffix (pkl or onnx)
class FoliageClassifier(Classifier):
    def __init__(self, modelfilename=None, isOnnx=None):
        super(FoliageClassifier, self).__init__(modelfilename, isOnnx)
        # Add any desired initialization options
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def createModel(self):
        # If you want to use this class to train your model, fill in this function
        # Return an ML model to be trained to classify foliage
        model = None
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        return model

    def preprocessImage(self, image):
        # Process the image as needed in preparation for training, testing, and classifying
        #   (e.g., normalizing, reshaping, changing color space)
        # BEGIN STUDENT CODE
        image_as_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        image_as_hsv = image_as_hsv.astype(np.float32)
        image_as_hsv /= 255
        image = image_as_hsv.reshape(-1, 3)
        # END STUDENT CODE
        return image

    def preprocessMask(self, mask):
        # Process the mask as needed in preparation for training, testing, and classifying
        #   (e.g., reshaping)
        # BEGIN STUDENT CODE
        mask = mask > 0
        # END STUDENT CODE
        return mask

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        # BEGIN STUDENT CODE
        mask = mask.reshape(orig_shape)
        # END STUDENT CODE
        return mask

