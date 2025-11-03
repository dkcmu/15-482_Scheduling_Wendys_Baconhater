from computer_vision.classify import FoliageClassifier
from computer_vision.measure import MeasureHeight

# Given an image, return three values:
# 1. An image with all non-foliage parts masked out
# 2. An image with:
#    (a) an overlay on the stick_region and
#    (b) a line at the row corresponding to the tallest plant
#        that overlaps the measuring stick (if any)
# 3. The height of the foliage
def foliageImages (image, modelfilename, ref_image, stick_mask):
    classifier = FoliageClassifier(modelfilename)
    foliage_mask = classifier.classify(image)
    measurer = MeasureHeight(ref_image, stick_mask)
    height, row = measurer.measure(foliage_mask)
    stick_mask = measurer.stick_mask
    foliage_image = stick_image = None
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    return foliage_image, stick_image, height

# Given an image, return two values:
# 1. The amount of foliage in the image
# 2. An estimate of the plant health (as a string), based on changes from the
#    previous day (changes in both the amount of foliage and plant height).
def plantHealth (image, modelfilename):
    classifier = FoliageClassifier(modelfilename)
    foliage_mask = classifier.classify(image)
    measurer = MeasureHeight(ref_image, stick_mask)
    height, row = measurer.measure(foliage_mask)
    greenery = 0
    health_msg = ""
    # BEGIN STUDENT CODE
    # END STUDENT CODE
    return greenery, health_msg
