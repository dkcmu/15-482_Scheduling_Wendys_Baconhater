from monitor import *
from terrabot_utils import clock_time, time_since_midnight
import os

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

        # Water & Weight data from past 24 hours:
        self.recent_water_data = []
        self.recent_water_attempts = []
    
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
                print(f"Created new log file: {file_name}\n")
        else:
            if not os.path.exists(file_name): # NEW DAY
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                    file.write(",".join(data) + '\n')
                print(f"Created new log file: {file_name}\n")
            else: # SAME DAY
                with open(file_name, "a") as file:
                    file.write(",".join(data) + '\n')
    
    def logPlantData(self, data=None): # EXTERNALLY ACCESSED
        headings = ["Day", "Plant Height", "Greenery", "Message"]
        file_name = f"./logs/plants.csv"

        if data is None: # MONITOR __INIT__
            if not os.path.exists(file_name):
                with open(file_name, "w") as file:
                    file.write(",".join(headings) + '\n')
                print(f"Created new log file: {file_name}\n")
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
            print(f"Logged new plant data\n")
    
    def prune_water_data(self, time):
        cutoff_time = time - (24*60*60) # 24 hours ago

        # Cutoff Water & Weight data
        while (len(self.recent_water_data) > 0
               and self.recent_water_data[0][0] < cutoff_time):
            self.recent_water_data = self.recent_water_data[1:]
        
        # Cutoff Water Attempts data
        while (len(self.recent_water_attempts) > 0
               and self.recent_water_attempts[0][0] < cutoff_time):
            self.recent_water_attempts = self.recent_water_attempts[1:]
    
    def logWaterData(self, time, dwater): # EXTERNALLY ACCESSED
        log_string = f"Day {self.day}: +{dwater} mL\n"
        print(log_string)
        self.recent_water_data.append((time, dwater))
    
    def logWaterAttempts( # EXTERNALLY ACCESSED
            self,
            time,
            watered_enough,
            reservoir_empty,
            moist_enough):
        log_string = (
            f"Day {self.day}: attempted watering\n"
            f"- Water Limit: {watered_enough}\n"
            f"- Reservoir Empty: {reservoir_empty}\n"
            f"- Soil Too Moist: {moist_enough}\n"
        )
        print(log_string)
        self.recent_water_attempts.append((
            time, (watered_enough, reservoir_empty, moist_enough)))
    
    def getWaterWeightData(self, time):
        self.prune_water_data(time)

        total_water = 0
        contributed_weight = 0
        succ = 0
        fails = [0, 0, 0]
        tries = len(self.recent_water_attempts)

        for (t, dwater) in self.recent_water_data:
            total_water += dwater
            if time - t < 1 and t >= 0: # Within the past hour
                contributed_weight += ((1.0 / 4) ** t) * dwater
        
        for (t, tup) in self.recent_water_attempts:
            if True not in tup:
                succ += 1
            fails[0] += int(tup[0])
            fails[1] += int(tup[1])
            fails[2] += int(tup[2])
        
        log_string = (
            f"24 Hour Water & Weight Summary ({clock_time(time)}):\n"
            f"- {total_water} mL added\n"
            f"- Estimated contribution of {contributed_weight} g\n"
            f"- {succ}/{tries} successful attempts\n"
            f"- {fails[0]}/{tries} watered enough\n"
            f"- {fails[1]}/{tries} reservoir empty\n"
            f"- {fails[2]}/{tries} soil too moist\n"
        )
        print(log_string)

        return total_water, contributed_weight, succ, fails, tries
 
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

