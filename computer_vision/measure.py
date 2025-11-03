import cv2, numpy as np
from computer_vision.cv_utils import *
from computer_vision.filterColor import *

class MeasureHeight:
    def __init__(self, ref_image, stick_mask):
        self.ref_image = ref_image
        self.stick_mask = self.adjustStickMask(stick_mask)
        self.tickMarks = self.findTickMarks(self.ref_image, self.stick_mask)

    def adjustStickMask(self, stick_mask):
        # Do what you want to clean up the stick mask (e.g., erode, fill in any gaps)
        # BEGIN STUDENT CODE
        kernel = np.ones((5, 5), np.uint8)
        stick_mask = cv2.erode(stick_mask, kernel, iterations=1)
        # END STUDENT CODE
        return stick_mask

    def findTickMarks (self, ref_image, stick_mask):
        # Find the tick marks on the stick.  The tick marks appear every 0.5cm from the top (9cm)
        #   down to the bottom (0cm).  One way to do it is to mask out the stick in the image and
        #   find the darker areas of the stick, which are the tick marks.  Note that sometimes you
        #   won't be able to find all the marks, so you'll need to interpolate.  Also note that, due
        #   to the angle of the camera, the tick marks are not uniformly spread in the image.
        # See the handout for more hints about how to solve this
        tickMarks = []
        # BEGIN STUDENT CODE
        # Image size: 2464 x 3280
        # Stick Mask: GRAYSCALE [0, 255]

        stick_mask = self.adjustStickMask(stick_mask)
        hsv_ref_img = transformFromBGR(ref_image, "HSV")
        v_ref_img = hsv_ref_img[:, :, 2]

        threshold_v = np.median(v_ref_img[stick_mask == 255])
        v_stick_img = np.where(stick_mask == 255, v_ref_img, 0)
        # print(f"Calculated Median V Threshold: {threshold_v}")

        '''window_name = "Masked Image"
        img = v_stick_img
        createWindow(wname=window_name)
        showImageWait(wname=window_name, image=img)'''

        # Find POI (Points of Interest)
        points = []
        counts = np.where((v_stick_img != 0) & (v_stick_img < threshold_v), 1, 0)
        counts = counts.sum(axis=1)
        for i in range(len(counts)):
            points += [i]*counts[i]

        points = np.array(points)
        # print(f"Calculated Points: {points}")

        # K-Means Clustering
        kmeans_img = np.float32(points)
        max_iter, eps = 100, 1
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, max_iter, eps)
        num_attempts = 10
        K = 19
        flags = cv2.KMEANS_PP_CENTERS

        # Apply K-Means
        ssds, labels, centers = cv2.kmeans(kmeans_img, K, None, criteria, num_attempts, flags)

        # Reshape, Sort, and Round Centers
        tickMarks = np.round(np.sort(centers.flatten())).astype(int)
        
        '''print(f"Tick Marks: {tickMarks}")
        for t in tickMarks:
            cv2.line(v_stick_img, (50, t), (3500, t), 255, 2)
        window_name = "Masked Image"
        img = v_stick_img
        createWindow(wname=window_name)
        showImageWait(wname=window_name, image=img)'''
        # END STUDENT CODE
        return tickMarks


    def measure(self, foliage_mask):
        # Given the foliage mask (as would be returned from FoliageClassifer.classify),
        #   the stick mask, and the tick marks on the stick, find the tallest plant that 
        #   crosses in front of the measuring stick.  
        # NOTE: You don't need the actual image - all the information you need is contained in
        #   the foliage and stick
        # Basically, combine the foliage from the stick masks and find the highest point (lowest row)
        #   in which there is both the stick and foliage.
        # Based on the list of tick marks (from findTickMarks), calculate and return the height of 
        #    the tallest plant (in cms) and the row in the image where it appears; 
        #    If the plants cover the top of the stick, return 9cm (maximum tick mark)
        #    If no foliage overlaps the stick, return (None, None)
        # DON'T MODIFY THE IMAGE PASSED INTO THE FUNCTION!
        stick_mask = self.stick_mask
        height = top_row = None
        # BEGIN STUDENT CODE
        # Combine Masks
        combined_mask = np.uint8(np.where(stick_mask == 255, foliage_mask, 0))
        
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.erode(combined_mask, kernel, iterations=5)
        
        '''window_name = "Combined Mask"
        createWindow(wname=window_name)
        showImageWait(wname=window_name, image=combined_mask)'''

        # Row Calculation: first occurrence of non-zero elem
        rows = np.any(combined_mask, axis=1)
        if True not in rows: # No foliage overlaps
            return None, None
        else:
            top_row = rows.argmax()
        # print(f"Calculated Row: {top_row}")

        height_map = list(i / 2.0 for i in range(18, -1, -1))

        # Height Calculation
        if top_row < self.tickMarks[0]:
            height = 9.
            top_row = self.tickMarks[0]
        elif top_row > self.tickMarks[-1]:
            height = 0.
            top_row = self.tickMarks[-1]
        elif top_row in self.tickMarks:
            height = height_map[self.tickMarks.index(top_row)]
        else:
            height = -1. # Indicates something went wrong
            for i in range(len(self.tickMarks) - 2, -1, -1):
                if top_row > self.tickMarks[i]:
                    # Interpolation between tick marks
                    baseDiff = self.tickMarks[i+1] - self.tickMarks[i]
                    diff = self.tickMarks[i+1] - top_row
                    add = 0.5 * (diff / baseDiff)
                    height = height_map[i+1] + add
                    break

        # END STUDENT CODE
        return height, top_row

