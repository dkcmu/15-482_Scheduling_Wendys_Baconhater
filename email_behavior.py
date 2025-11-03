from behavior import *
from transitions import Machine
from greenhouse_behaviors import Greenhouse_Behavior
import send_email
import datetime


class Email(Greenhouse_Behavior):
    def __init__(self, agent):
        super(Email, self).__init__(agent, "EmailBehavior")

        # BEGIN STUDENT CODE
        self.initial = 'Halt'
        self.sending_email = 'sending_email'
        self.on = "init"
        self.states = [self.initial, self.on, self.sending_email]
        self._sent_email = False
        self.receiver_emails = [
            "chrissu@andrew.cmu.edu",
            "dkouatch@andrew.cmu.edu",
            "mliang4@andrew.cmu.edu",
            "rsimmons@andrew.cmu.edu",
            "shashwa3@andrew.cmu.edu",
            "abhinanv@andrew.cmu.edu"
        ]

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                            ignore_invalid_triggers=True)
        self.fsm.add_transition('enable', self.initial, self.on, before="unset_bit")
        self.fsm.add_transition('doStep', self.on, self.sending_email, after="email")
        self.fsm.add_transition('doStep', self.sending_email, self.sending_email, unless="sent_email")
        self.fsm.add_transition('disable', self.sending_email, self.initial)
        self.fsm.add_transition('disable', self.on, self.initial)
        # END STUDENT CODE

    def parse_sensor_data(self):
        sensors = self.sensors
        sensor_data = f"""
        <b>Sensor Data</b>\n
        <p>Light Level:       {sensors.light_level}</p>
        <p>Temperature:       {sensors.temperature}</p>
        <p>Humidity:          {sensors.humidity}</p>
        <p>Weight:            {sensors.weight}</p>
        <p>Moisture:          {sensors.moisture}</p>
        <p>Water Level:       {sensors.wlevel}</p>
        <p>Light Level (raw): {sensors.light_level_raw[0]},{sensors.light_level_raw[1]}</p>
        <p>Temperature (raw): {sensors.temperature_raw[0]},{sensors.temperature_raw[1]}</p>
        <p>Humidity (raw):    {sensors.humidity_raw[0]},{sensors.humidity_raw[1]}</p>
        <p>Weight (raw):      {sensors.weight_raw[0]},{sensors.weight_raw[1]}</p>
        <p>Moisture (raw):    {sensors.moisture_raw[0]},{sensors.moisture_raw[1]}</p>
        <p>Water Level (raw): {sensors.wlevel_raw}</p>
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

    def create_email(self):
        import os
        import datetime

        IMAGE_DIRECTORY = "/home/robotanist/User/images"

        TEAM_NAME = "Team Wendy's Baconhater"
        timestamp = datetime.datetime.fromtimestamp(
            self.sensordata['unix_time']
        ).strftime("%d/%m/%Y %H:%M:%S")

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
                <p><img src="cid:image1" /></p>
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
