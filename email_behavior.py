from behavior import *
from transitions import Machine
from greenhouse_behaviors import Greenhouse_Behavior
import send_email
import datetime

from computer_vision import classify, measure, vision, color_correct, cv_utils

class Email(Greenhouse_Behavior):
    def __init__(self, agent):
        super(Email, self).__init__(agent, "EmailBehavior")

        self.IMAGE_DIRECTORY = "/home/robotanist/User/images"

        # BEGIN STUDENT CODE
        self.initial = 'Halt'
        self.sending_email = 'sending_email'
        self.on = "init"
        self.states = [self.initial, self.on, self.sending_email]
        self._sent_email = False
        self.receiver_emails = [
            "chrissu@andrew.cmu.edu",
        ]

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                            ignore_invalid_triggers=True)
        self.fsm.add_transition('enable', self.initial, self.on, before="unset_bit")
        self.fsm.add_transition('doStep', self.on, self.sending_email, after="email")
        self.fsm.add_transition('doStep', self.sending_email, self.sending_email, unless="sent_email")
        self.fsm.add_transition('disable', self.sending_email, self.initial)
        self.fsm.add_transition('disable', self.on, self.initial)
        # END STUDENT CODE

        # CV-related Initializations
        stick_mask_path = "./computer_vision/masks/stick_mask_A.jpg"
        ref_img_path = "./computer_vision/images/measure_ref_image_A.jpg"
        self.foliage_model = "./computer_vision/foliage_classifier.pkl"
        self.calib_model = "./computer_vision/calib_classifier.onnx"

        self.ref_img = cv_utils.readImage(ref_img_path)
        self.stick_mask = cv_utils.readMask(stick_mask_path)

        self.classifier = classify.FoliageClassifier(self.foliage_model)
        self.measurer = measure.MeasureHeight(self.ref_img, self.stick_mask)

        self.greenery = self.height = 0

    def parse_sensor_data(self):
        sensors = self.sensors
        sensor_data = f"""
        <b>Sensor Data</b>\n
        <p>Light Level:       {float(sensors.light_level):.2f}</p>
        <p>Temperature:       {float(sensors.temperature):.2f}</p>
        <p>Humidity:          {float(sensors.humidity):.2f}</p>
        <p>Weight:            {float(sensors.weight):.2f}</p>
        <p>Moisture:          {float(sensors.moisture):.2f}</p>
        <p>Water Level:       {float(sensors.wlevel):.2f}</p>
        <p>Light Level (raw): {float(sensors.light_level_raw[0]):.2f},{float(sensors.light_level_raw[1]):.2f}</p>
        <p>Temperature (raw): {float(sensors.temperature_raw[0]):.2f},{float(sensors.temperature_raw[1]):.2f}</p>
        <p>Humidity (raw):    {float(sensors.humidity_raw[0]):.2f},{float(sensors.humidity_raw[1]):.2f}</p>
        <p>Weight (raw):      {float(sensors.weight_raw[0]):.2f},{float(sensors.weight_raw[1]):.2f}</p>
        <p>Moisture (raw):    {float(sensors.moisture_raw[0]):.2f},{float(sensors.moisture_raw[1]):.2f}</p>
        <p>Water Level (raw): {float(sensors.wlevel_raw):.2f}</p>
        """
        return sensor_data
    
    def parse_actuator_state(self):
        actuators = self.actuators
        actuator_state = actuators.actuator_state
        actuator_data = f"""
        <b>Actuator Data</b>\n
        <p>Fan: {"On" if actuator_state["fan"] else "Off"}</p>
        <p>Water Pump: {"On" if actuator_state["wpump"] else "Off"}</p>
        <p>LED: {"On" if actuator_state["led"] else "Off"}</p>
        """
        return actuator_data
    
    def get_most_recent_image(self):
        # Gets most recent image from saved images from camera behavior
        import os

        img_paths = []
        for entry in os.listdir(self.img_dir):
            path = os.path.join(self.img_dir, entry)
            if os.path.isfile(path):
                img_paths.append(path)
        if len(img_paths) == 0:
            return None
        else:
            img_cdates = list(map(lambda p: os.path.getctime(p), img_paths))
            target_img_path = img_paths[img_cdates.index(max(img_cdates))]
            return target_img_path
    
    def get_foliage_images(self):
        # Perform color calibration on target image based on reference image
        target_img_path = self.get_most_recent_image()
        target_img = cv_utils.readImage(target_img_path)

        corrector = color_correct.ColorCorrector(self.ref_img)
        corrector.findRegion(self.calib_model)
        corrected_image = corrector.correct(target_img)

        # Get foliage images
        foliage_image, height_image, height = vision.foliageImages(corrected_image, self.classifer, self.measurer)
        return foliage_image, height_image


    def get_plant_health_assessment(self):
        # Perform color calibration on target image based on reference image
        target_img_path = self.get_most_recent_image()
        target_img = cv_utils.readImage(target_img_path)

        corrector = color_correct.ColorCorrector(self.ref_img)
        corrector.findRegion(self.calib_model)
        corrected_image = corrector.correct(target_img)

        # Estimate plant health
        self.greenery, self.plant_height, health_msg = vision.plantHealth(
            corrected_image, self.classifier, self.measurer, self.greenery, self.plant_height)
        self.plant_height = 0 if self.plant_height is None else self.plant_height

        return health_msg
    
    def get_previous_insolation(self):
        lightMonitor = self.agent.getExecutiveLayer().getMonitor('LightMonitor')
        return lightMonitor.getPrevInsolation()
    
    def get_water_weight_info(self):
        loggingMonitor = self.agent.getExecutiveLayer().getMonitor('LoggingMonitor')
        total_water, contributed_weight, succ, fail_count = loggingMonitor.getWaterWeightData(self.time)
        
        watered_enough_count = fail_count[0]
        reservoir_empty = fail_count[1]
        smoist_enough_count  = fail_count[2]

        return (
            watered_enough_count,
            reservoir_empty,
            smoist_enough_count,
            total_water,
            contributed_weight,
            succ
        )

    def create_email(self):
        import os
        import datetime

        # IMAGE_DIRECTORY = "/home/robotanist/User/images"
        IMAGE_DIRECTORY = self.IMAGE_DIRECTORY

        TEAM_NAME = "Team Wendy's Baconhater"
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        subject = f"{TEAM_NAME} TerraBot 7 Daily Mail"
        images = []

        if os.path.isdir(IMAGE_DIRECTORY):
            files = [os.path.join(IMAGE_DIRECTORY, f) for f in os.listdir(IMAGE_DIRECTORY)]
            files = [f for f in files if os.path.isfile(f)]
            if files:
                last_image = max(files, key=os.path.getmtime)
                with open(last_image, "rb") as f:
                    images.append(f.read())

                body = f"""
                <h2>{TEAM_NAME} - TerraBot 7</h2>
                <p><b>Time:</b> {timestamp}</p>
                <p>{self.parse_sensor_data()}</p>
                <p>{self.parse_actuator_state()}</p>
                <p>Most recent image:</p>
                <p><img src="cid:image1" style="width:25%;height:auto;" /></p>
                """
            else:
                body = f"""
                <h2>{TEAM_NAME} - TerraBot 7</h2>
                <p><b>Time:</b> {timestamp}</p>
                <p>{self.parse_sensor_data()}</p>
                <p>{self.parse_actuator_state()}</p>
                <p>No image available.</p>
                """
        else:
            body = f"""
            <h2>{TEAM_NAME} - TerraBot 7</h2>
            <p><b>Time:</b> {timestamp}</p>
            <p>{self.parse_sensor_data()}</p>
            <p>{self.parse_actuator_state()}</p>
            <p>Image directory not found.</p>
            """

        return subject, body, images


    def email(self):
        subject, body, images = self.create_email()
        if send_email.send(
            "terrabot7@outlook.com", 
            "Railing213", 
            ",".join(self.receiver_emails),
            subject, 
            body,
            images, 
            inline=True
        ):
            print("Successfully sent!")
        self._sent_email = True

    def sent_email(self):
        return self._sent_email
    
    def unset_bit(self):
        self._sent_email = False

    def perceive(self):
        self.time = self.sensordata['unix_time']
        # Add any sensor data variables you need for the behavior
        # BEGIN STUDENT CODE

        # END STUDENT CODE

    def act(self):
        self.trigger("doStep")
