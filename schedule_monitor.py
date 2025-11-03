from monitor import *
from terrabot_utils import clock_time, time_since_midnight
from greenhouse_scheduler_ref import BehaviorInfo, GreenhouseScheduler

import os
from computer_vision import classify, measure, vision, color_correct, cv_utils

class ScheduleMonitor(Monitor):
    seedling_height_threshold = 2.0
    mature_height_threshold = 5.0

    base_insolation_target = 8500
    seedling_insolation_target = 9000
    mature_insolation_target = 9500

    # Location of saved images from Camera Behavior
    img_dir = "/home/robotanist/User/images/"
    
    def __init__(self, period=10): # Perceive every 10 seconds
        super(ScheduleMonitor, self).__init__("ScheduleMonitor", period)
        self.plant_height = 0
        self.greenery = 0
        self.day = 1

        # Files & Models for Plant Height Estimation
        # stick_mask_path = "./computer_vision/masks/stick_mask_A.jpg"
        # ref_img_path = "./computer_vision/images/measure_ref_image_A.jpg"
        stick_mask_path = "./computer_vision/masks/stick_mask_sim.jpg"
        ref_img_path = "./computer_vision/images/measure_ref_image_sim.jpg"
        self.foliage_model = "./computer_vision/foliage_classifier.pkl"
        self.calib_model = "./computer_vision/calib_classifier.onnx"

        self.ref_img = cv_utils.readImage(ref_img_path)
        self.stick_mask = cv_utils.readMask(stick_mask_path)

        self.classifier = classify.FoliageClassifier(self.foliage_model)
        self.measurer = measure.MeasureHeight(self.ref_img, self.stick_mask)

        self.reset_behaviors_info()
    
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
            img_cdates = list(map(lambda p: os.path.getctime(p), img_paths))
            self.target_img_path = img_paths[img_cdates.index(max(img_cdates))]

            print(f"Images: {img_paths}")
            print(f"Most Recent: {self.target_img_path}")
    
    def calibratePlantHeight(self):
        # Perform color calibration on target image based on reference image
        target_img = cv_utils.readImage(self.target_img_path)

        corrector = color_correct.ColorCorrector(self.ref_img)
        corrector.findRegion(self.calib_model)
        corrected_image = corrector.correct(target_img)

        # Estimate plant health
        self.greenery, self.plant_height, health_msg = vision.plantHealth(
            corrected_image, self.classifier, self.measurer, self.greenery, self.plant_height)
        
        self.plant_height = 0 if self.plant_height is None else self.plant_height
        print(f"New estimated plant height of {self.plant_height} cm and greenery of {self.greenery}%.")
        print("Estimated plant health is %s" %health_msg)
        self.loggingMonitor.logPlantData({"greenery": self.greenery, "height": self.plant_height})
    
    def reset_behaviors_info(self):
        # Light should be on for at least 8 hours during the day (not on at night)
        #   Instances can be scheduled back-to-back (0 min time) but
        #   at least every 4 hours during the day
        self.behaviors_info = {}
        self.behaviors_info["Light"] =      BehaviorInfo(8*60,     0,    0, 4*60)
        self.behaviors_info["LowerHumid"] = BehaviorInfo(8*60, 12*60,   30, 2*60)
        self.behaviors_info["LowerTemp"] =  BehaviorInfo(4*60, 12*60, 2*60, 4*60)
        self.behaviors_info["RaiseTemp"] =  BehaviorInfo(2*60, 12*60, 2*60, 4*60)
        self.behaviors_info["LowerMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
        self.behaviors_info["RaiseMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
        # camera should not be on at all at night
        self.behaviors_info["TakeImage"] =  BehaviorInfo(1*60, 0,     3*60, 6*60)
    
    def setLightLowFreqSchedule(self):
        self.behaviors_info["Light"] = BehaviorInfo(8*60, 0, 0, 4*60)
    
    def setLightHighFreqSchedule(self):
        self.behaviors_info["Light"] = BehaviorInfo(12*60, 0, 0, 4*60)
    
    def setRaiseSmoistLowFreqSchedule(self):
        self.behaviors_info["RaiseMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
    
    def setRaiseSmoistHighFreqSchedule(self):
        self.behaviors_info["RaiseMoist"] = BehaviorInfo(3*60, 12*60, 2*60, 4*60)

    def activate(self):
        self.lightMonitor = self.getExecutive().getMonitor("LightMonitor")
        self.loggingMonitor = self.getExecutive().getMonitor("LoggingMonitor")
    
    def perceive(self):
        self.mtime = self.sensordata['midnight_time']

    def monitor(self):
        if self.mtime >= time_since_midnight(self.last_time):
            return
        
        # Only create schedule changes at around midnight of the next day
        self.day += 1

        self.get_most_recent_image()
        self.calibratePlantHeight()

        # LIGHT
        # If height passes threshold, assign new insolation value
        if self.plant_height < self.seedling_height_threshold:
            self.lightMonitor.setTarget(self.base_insolation_target)
            self.setLightLowFreqSchedule()
        elif self.plant_height < self.mature_height_threshold:
            self.lightMonitor.setTarget(self.seedling_insolation_target)
            self.setLightHighFreqSchedule()
        else:
            self.lightMonitor.setTarget(self.mature_insolation_target)
            self.setLightHighFreqSchedule()
        
        # WATER
        if self.plant_height < self.seedling_height_threshold:
            self.setRaiseSmoistLowFreqSchedule()
        elif self.plant_height < self.mature_height_threshold:
            self.setRaiseSmoistLowFreqSchedule()
        else:
            self.setRaiseSmoistHighFreqSchedule()
        
        schedule_fname = f"./schedules/new_schedule_day_{self.day}.txt"
        problem = GreenhouseScheduler(self.behaviors_info, 30, schedule_fname)
        
        if problem.solveProblem(verbose=False) is None:
            print(f"Failed creating new schedule for day {self.day}")
            self.reset_behaviors_info()
            problem = GreenhouseScheduler(self.behaviors_info, 30, schedule_fname)
            problem.solveProblem()
        print(f"Succeeded creating new schedule for day {self.day}")
        
        planningLayer = self.getExecutive().agent.getPlanningLayer()
        planningLayer.setTestingSchedule(schedule_fname)
        # planningLayer.switch_to_test_sched()
