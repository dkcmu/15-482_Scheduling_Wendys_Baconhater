import numpy as np, pickle as pkl
from computer_vision.cv_utils import *
from sklearn.model_selection import cross_val_score

def loadPickleModel(modelfilename):
    with open(modelfilename, "rb") as infile:
        return pkl.load(infile)

def dumpPickleModel(model, modelfilename):
    with open(modelfilename, "wb") as outfile:
        pkl.dump(model, outfile)

def loadOnnxModel(modelfilename):
   return cv2.dnn.readNetFromONNX(modelfilename)


import torch
def dumpOnnxModelFromTorch(modelfilename, model):
    model.eval().cpu()  # IMPORTANT: eval() for correct BN/Dropout
    dummy = torch.randn(1, 3, 224, 224, dtype=torch.float32)
    torch.onnx.export(model, dummy, modelfilename, opset_version=12,
                      input_names=["input"], output_names=["out"],
                      dynamic_axes={"input": {0:"batch", 2:"height", 3:"width"},
                                    "out":   {0:"batch", 2:"height", 3:"width"}},
                        export_params=True, do_constant_folding=True)

'''
import tensorflow as tf, tf2onnx, onnx
def dumpOnnxModelFromTensorflow(modelfilename, model):
    spec = (tf.TensorSpec((None, 224, 224, 3), tf.float32, name="input"),)
    onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=13)
    onnx.save(onnx_model, modelfilename)
'''

def loadImages(image_names, directory=""):
    return np.array([readImage(f"{directory}/{image}") for image in image_names])
            
def loadMasks(mask_names, directory=""):
    return np.array([readMask(f"{directory}/{mask}") for mask in mask_names])

# A simple class for creating classifiers (developed for sklearn, primarily)
# If modelfilename is None, create a model, o/w load it in
# isOnnx is None, determine model type using the modelfilename suffix (pkl or onnx)
class Classifier():
    def __init__(self, modelfilename=None, isOnnx=None):
        if modelfilename is None:
            self.isOnnxModel = False
            self.model = self.createModel()
        else:
            self.isOnnxModel = (isOnnx or modelfilename.lower().endswith(".onnx"))
            self.model = self.loadModel(modelfilename) 
        # Try to make things repeatable
        if ('random_state' in dir(self.model)): self.model.random_state = 42

    def createModel(self):
        # Create a model for training and return the model
        assert False, "Need to implement createModel!"

    def preprocessImage(self, image):
        # Process the image as needed (e.g., normalizing, reshaping, changing color space)
        assert False, "Need to implement preprocessImage!"

    def preprocessImages(self, images):
        arr = np.array([self.preprocessImage(image) for image in images])
        return arr.reshape(-1, arr[0].shape[-1]).squeeze()

    def preprocessMask(self, mask):
        # Process the mask as needed (e.g., reshaping)
        assert False, "Need to implement preprocessMask!"

    def preprocessMasks(self, masks):
        arr = np.array([self.preprocessMask(mask) for mask in masks])
        return arr.reshape(-1, 1).squeeze()

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        assert False, "Need to implement postprocessMask!"

    def train(self, train_images, train_masks):
        assert self.model != None, "Model has not been created!"
        train_images = self.preprocessImages(train_images)
        train_masks = self.preprocessMasks(train_masks)
        self.model.fit(train_images, train_masks)
        score = self.model.score(train_images, train_masks)
        print("Training score: %0.4f" %score)
        return score

    def test(self, test_images, test_masks):
        assert self.model != None, "Model has not been created!"
        score = self.model.score(self.preprocessImages(test_images),
                                 self.preprocessMasks(test_masks))
        print("Testing score: %0.4f" %score)
        return score

    def classify(self, image):
        assert self.model != None, "Model has not been created!"
        processed_image = self.preprocessImage(image)
        if self.isOnnxModel:
            self.model.setInput(processed_image)
            mask = self.model.forward()
        else:
            mask = self.model.predict(processed_image)
        mask = (mask >= 0.5).astype(np.uint8) * 255
        mask = self.postprocessMask(mask, image.shape[:2])
        return mask

    def crossValidate(self, images, masks, cv=10):
        assert self.model != None, "Model has not been created!"
        scores = cross_val_score(self.model, self.preprocessImages(test_images),
                                 self.preprocessMasks(test_masks), cv=cv)
        print("Crossfold score: %0.4f (std %0.4f)" %(scores.mean(), scores.std()))
        return scores.mean()

    def saveModel(self, filename):
        assert self.model != None, "Model has not been created!"
        dumpPickleModel(self.model, filename)

    def loadModel(self, modelfilename):
        return (loadOnnxModel(modelfilename) if self.isOnnxModel else 
                loadPickleModel(modelfilename))
