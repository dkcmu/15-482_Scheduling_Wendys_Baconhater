from monitor import *
from terrabot_utils import clock_time, time_since_midnight
import os

class ScheduleMonitor(Monitor):
    seedling_height_threshold = 2.0
    mature_height_threshold = 5.0

    base_insolation_target = 8500
    seedling_insolation_target = 9000
    mature_insolation_target = 9500

    img_dir = ""
    
    def __init__(self, period=60*60*24): # Perceive every 24 hours
        super(ScheduleMonitor, self).__init__("ScheduleMonitor", period)
        self.plant_height = 0
    
    def get_most_recent_image(self):
        img_paths = []
        for entry in os.listdir(self.img_dir):
            path = os.path.join(self.img_dir, entry)
            if os.path.isfile(path):
                img_paths.append(path)
        if len(img_paths) == 0:
            return None
        else:
            img_cdates = map(lambda p: os.path.getctime(p), img_paths)
            return img_paths[img_cdates.index(max(img_cdates))]
    
    def getPlantHeight(self):
        pass

    def activate(self):
        self.lightMonitor = self.getExecutive().getMonitor("LightMonitor")
        self.schedule = self.getExecutive().schedule

    def monitor(self):
        # Get plant height

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
