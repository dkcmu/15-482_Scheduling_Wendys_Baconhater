from monitor import *
from terrabot_utils import clock_time, time_since_midnight
import os
import computer_vision

class ScheduleMonitor(Monitor):
    seedling_height_threshold = 2.0
    mature_height_threshold = 5.0

    base_insolation_target = 8500
    seedling_insolation_target = 9000
    mature_insolation_target = 9500

    # Location of saved images from Camera Behavior
    img_dir = "/home/robotanist/User/images/"
    
    def __init__(self, period=60*60*24): # Perceive every 24 hours
        super(ScheduleMonitor, self).__init__("ScheduleMonitor", period)
        self.plant_height = 0
        self.greenery = 0

        # Files & Models for Plant Height Estimation
        self.stick_mask = "./computer_vision/masks/stick_mask_A.jpg"
        self.ref_img = "./computer_vision/images/measure_ref_image.jpg"
        self.foliage_model = "./computer_vision/foliage_classifier.pkl"
        self.calib_model = "./computer_vision/calib_classifier.pkl"

        # TODO: pass height and greenery data to logging monitor
    
    def get_most_recent_image(self):
        # Gets most recent image from saved images from camera behavior
        img_paths = []
        for entry in os.listdir(self.img_dir):
            path = os.path.join(self.img_dir, entry)
            if os.path.isfile(path):
                img_paths.append(path)
        if len(img_paths) == 0:
            return None
        else:
            img_cdates = map(lambda p: os.path.getctime(p), img_paths)
            self.target_img = img_paths[img_cdates.index(max(img_cdates))]
    
    def calibratePlantHeight(self):
        # Perform color calibration on target image based on reference image
        corrector = computer_vision.color_correct.ColorCorrector(self.ref_img)
        corrector.findRegion(self.calib_model)
        corrected_image = corrector.correct(self.target_img)

        # Estimate plant health
        self.greenery, self.plant_height, health_msg = computer_vision.vision.plantHealth(
            corrected_image, self.classifier, self.measurer, self.greenery, self.plant_height)
        
        print(f"New estimated plant height of {self.greenery} cm and greenery of {self.plant_height}%.")
        print("Estimated plant health is %s" %health_msg)
        # TODO: loggingMonitor.logPlantInfo(self.greenery, self.plant_height)
        

    def activate(self):
        self.lightMonitor = self.getExecutive().getMonitor("LightMonitor")
        self.schedule = self.getExecutive().schedule
        self.classifier = computer_vision.classify.FoliageClassifier(self.foliage_model)
        self.measurer = computer_vision.measure.MeasureHeight(self.ref_img, self.stick_mask)

    def monitor(self):
        self.get_most_recent_image()
        self.calibratePlantHeight()

        # LIGHT
        # If height passes threshold, assign new insolation value
        if self.plant_height < self.seedling_height_threshold:
            self.lightMonitor.setTarget(self.base_insolation_target)
            #TODO: Assign new schedule
        elif self.plant_height < self.mature_height_threshold:
            self.lightMonitor.setTarget(self.seedling_insolation_target)
            #TODO: Assign new schedule
        else:
            self.lightMonitor.setTarget(self.mature_insolation_target)
            #TODO: Assign new schedule
        
        # WATER
        if self.plant_height < self.seedling_height_threshold:
            pass
            #TODO: Assign new schedule
        elif self.plant_height < self.mature_height_threshold:
            pass
            #TODO: Assign new schedule
        else:
            pass
            #TODO: Assign new schedule
