import cv2, numpy as np
from cv_utils import *
from cv_learn import *
import torch
import torchvision.transforms.v2 as T
import onnxruntime as ort
import matplotlib.pyplot as plt
    
class CalibrationClassifier(Classifier):
    def __init__(self, modelfilename=None, isOnnx=None):
        super(CalibrationClassifier, self).__init__(modelfilename, isOnnx)
        # Add any desired initialization options
        # BEGIN STUDENT CODE
        self.image_size = 112
        self.transform_list = [
            T.ToTensor(),
            T.Resize((self.image_size, self.image_size)),
            T.ToDtype(torch.float32, scale=True),
        ]
        self.transforms = T.Compose(self.transform_list)
        # END STUDENT CODE

    def createModel(self):
        # If you want to use this class to train your model, fill in this function
        # Return an ML model to be trained to classify foliage
        model = None
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        return model

    def preprocessImage(self, image):
        # Process the image as needed (e.g., normalizing, reshaping, changing color space)
        # BEGIN STUDENT CODE
        # im = readImage(image)
        im = image
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = self.transforms(im)
        # END STUDENT CODE
        return im

    def preprocessMask(self, mask):
        # Process the image as needed (e.g., reshaping)
        # BEGIN STUDENT CODE
        ma = readMask(mask)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        ma = self.transforms(ma)
        # END STUDENT CODE
        return mask

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        # BEGIN STUDENT CODE'
        Transformmm = T.Resize((orig_shape))
        gray = mask.reshape(1, self.image_size, self.image_size)
        gray = Transformmm(gray)
        gray = gray.permute(1, 2, 0).numpy().squeeze()
        gray = gray.clip(0, 1).astype(np.uint8)
        # END STUDENT CODE
        return gray

class ColorCorrector:
    def __init__(self, ref_image):
        self.ref_image = ref_image
        self.calib_region = None

    def findRegion(self, modelfilename):
        # Use your saved trained model to recognize the calibration target and 
        #  return a mask that indicates where the calibration target is found in the image
        image = self.ref_image
        shape = image.shape
        calib_mask = np.zeros(image.shape[2:])
        # BEGIN STUDENT CODE

        classifier = CalibrationClassifier(modelfilename, True)
        im = classifier.preprocessImage(image)

        session = ort.InferenceSession(modelfilename, providers=["CPUExecutionProvider"])
        im = im.unsqueeze(0)
        inputs = {"input": im.numpy()}
        mask = session.run(["out"], inputs)
        mask = torch.from_numpy(mask[0])

        mask = classifier.postprocessMask(mask, shape[0:2])

        # END STUDENT CODE
        self.calib_region = mask
    
    def correct(self, image):
        # Use the region found (calib_mask) to mask out the calibration targets
        #  in both the image and reference image (ref_image)
        # Transform the images to your desired color space,
        #   and compute and apply the affine transform (see slides from 9/22)
        # Don't forget to clip the corrected image to the range [0,255]!
        # Also, pay attention to the type of the returned image - it needs to be uint8
        # DON'T MODIFY THE IMAGE PASSED INTO THE FUNCTION!
        # Return the corrected image, in BGR color space
        if self.calib_region is None:
            print("ERROR: No calibration region saved - need to call findRegion")
            return image
        corrected_image = image
        ref_image = self.ref_image
        calib_mask = self.calib_region
        # BEGIN STUDENT CODE
        calib_mask = calib_mask.astype(bool)

        refLAB = cv2.cvtColor(ref_image, cv2.COLOR_BGR2LAB)
        imgLAB = cv2.cvtColor(corrected_image, cv2.COLOR_BGR2LAB)

        target_ref = refLAB[calib_mask]
        target_img = imgLAB[calib_mask]

        target_img_mean = np.mean(target_img, axis=0)
        target_img_std = np.std(target_img, axis=0)
        target_ref_mean = np.mean(target_ref, axis=0)
        target_ref_std = np.std(target_ref, axis=0)

        target_img_norm = (target_img - target_img_mean) / target_img_std
        target_ref_norm = (target_ref - target_ref_mean) / target_ref_std

        M_aug = np.hstack((target_img_norm, np.ones((target_img_norm.shape[0], 1))))

        Tf = np.linalg.pinv(M_aug.T @ M_aug) @ (M_aug.T @ target_ref_norm)

        imgLAB = imgLAB.reshape(-1, 3)
        imgLAB_norm = (imgLAB - target_img_mean) / target_img_std
        imgLAB_norm_aug = np.hstack((imgLAB_norm, np.ones((imgLAB_norm.shape[0], 1))))
        imgLAB_affine = imgLAB_norm_aug @ Tf

        imgLAB_unnorm = imgLAB_affine * target_ref_std + target_ref_mean
        imgLAB_unnorm = np.clip(imgLAB_unnorm, 0, 255).reshape(ref_image.shape[0], ref_image.shape[1], 3).astype(np.uint8)

        corrected_image = cv2.cvtColor(imgLAB_unnorm, cv2.COLOR_LAB2BGR)
        # END STUDENT CODE
        return corrected_image
    
def main():
    classifier = CalibrationClassifier()
    classifier.preprocessImage('/Users/michael/Desktop/Autonomous Agents/CV_HW/images/train_calib/train_calib_01.jpg')
    classifier.preprocessMask('/Users/michael/Desktop/Autonomous Agents/CV_HW/masks/train_calib_mask/train_calib_mask_01.jpg')

if __name__ == "__main__":
    main()

