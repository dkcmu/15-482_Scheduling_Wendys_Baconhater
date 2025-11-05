from monitor import *
from terrabot_utils import clock_time, time_since_midnight
import os
import time

class LoggingMonitor(Monitor):

    def __init__(self, period=10):
        super(LoggingMonitor, self).__init__("LoggingMonitor", period)
        # Put any iniitialization code here
        # BEGIN STUDENT CODE
        self.normal_sensors = ['unix_time',
            'light', 'temp', 'humid', 'weight',
            'smoist', 'level', 'level_raw']
        self.array_sensors = ['light_raw', 'temp_raw', 'humid_raw', 'weight_raw' ,'smoist_raw']
        self.actuators = ['fan', 'wpump', 'led', 'camera']
        self.day = 1

        # Create log directory
        if not os.path.exists("./logs/"):
            os.makedirs("./logs/")
        # END STUDENT CODE
    
    def reset(self):
        self.day += 1
    
    def logGreenhouseData(self, data=None):
        headings = self.normal_sensors + [
            'light_raw_1', 'light_raw_2',
            'temp_raw_1', 'temp_raw_2',
            'humid_raw_1', 'humid_raw_2',
            'weight_raw_1', 'weight_raw_2',
            'smoist_raw_1', 'smoist_raw_2'
        ] + self.actuators
        file_name = f"./logs/day_{self.day}.csv"

        if data is None: # MONITOR __INIT__
            if not os.path.exists(file_name):
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                print(f"Created new log file: {file_name}")
        else:
            if not os.path.exists(file_name): # NEW DAY
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                    file.write(",".join(data) + '\n')
                print(f"Created new log file: {file_name}")
            else: # SAME DAY
                with open(file_name, "a") as file:
                    file.write(",".join(data) + '\n')
    
    def logPlantData(self, data=None):
        headings = ["Day", "Plant Height", "Greenery", "Message"]
        file_name = f"./logs/plants.csv"

        if data is None: # MONITOR __INIT__
            if not os.path.exists(file_name):
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                print(f"Created new log file: {file_name}")
        else:
            data = [
                str(self.day),
                str(data["height"]),
                str(data["greenery"]),
                str(data["message"])
            ]
            if not os.path.exists(file_name):
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                    file.write(",".join(data) + '\n')
                print(f"Created new log file: {file_name}")
            else:
                with open(file_name, "a") as file:
                    file.write(",".join(data) + '\n')
            print("Logged new plant data")
    
    def perceive(self):
        # BEGIN STUDENT CODE
        self.normal_sensor_data = {sensor:self.sensordata[sensor] for sensor in self.normal_sensors}
        self.array_sensor_data = {sensor:self.sensordata[sensor] for sensor in self.array_sensors}

        self.mtime = self.sensordata['midnight_time']
        # END STUDENT CODE
        pass

    def monitor(self):
        # Use self.sensorData and self.actuator_state to log the sensor and
        #  actuator data, preferably as a comma-separated line of values.
        #  Make sure to timestamp the line of data
        # BEGIN STUDENT CODE
        # print(f"Current Time: {clock_time(self.normal_sensor_data['unix_time'])}")
        if (self.mtime < time_since_midnight(self.last_time)):
            self.reset()

        sensor_log_data = [str(value) for value in self.normal_sensor_data.values()]
        for data in self.array_sensor_data.values():
            sensor_log_data.append(str(data[0]))
            sensor_log_data.append(str(data[1]))

        actuator_log_data = [str(self.actuator_state[actuator]) for actuator in self.actuators]

        # Write to existing log file
        data = sensor_log_data + actuator_log_data
        self.logGreenhouseData(data)
        # END STUDENT CODE
        pass

