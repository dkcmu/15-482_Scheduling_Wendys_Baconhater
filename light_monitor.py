from monitor import *
from terrabot_utils import clock_time, time_since_midnight

class LightMonitor(Monitor):
    ambient_data = []
    lighting_intervals = []
    insolation = 0 # Per hour
    target = 8500 # Default value

    def __init__(self, period=100):
        super(LightMonitor, self).__init__("LightMonitor", period)
        self.insolation = None
        self.reset()

    def reset(self):
        if self.insolation is None:
            self.previous_insolation = 0
        else:
            self.previous_insolation = self.insolation
        self.insolation = 0

    def setTarget(self, target):
        self.target = target
    
    def getPrevInsolation(self):
        return self.previous_insolation

    def read_log_file(self, filename):
        self.ambient_data = []
        with open(filename) as log_file:
            for line in log_file:
                sline = line.split(" ")
                time = float(sline[0])
                data = float(sline[1].strip(' \n'))
                self.ambient_data.append((time, data))

    def activate(self):
        self.read_log_file("grader_files/ambient.log")
        self.lightBehavior = self.getExecutive().agent.getBehavioralLayer().getBehavior("LightBehavior")
        schedule = self.getExecutive().schedule
        self.lighting_intervals = [(start*60, end*60)
                                   for start, end in schedule['LightBehavior']]
        self.current_optimal = 900 # Arbitrary value - will be reset once the monitor begins

    def perceive(self):
        # BEGIN STUDENT CODE
        self.mtime = self.sensordata['midnight_time']
        self.light = self.sensordata['light']
        self.utime = self.sensordata['unix_time']
        # END STUDENT CODE
        pass

    def monitor(self):
        #print("INSOLATION: %.1f %d" %(self.mtime/3600.0, self.insolation))
        if (self.mtime < time_since_midnight(self.last_time)):
            print("INSOLATION TODAY: %.1f" %self.insolation)
            self.reset()
        else:
            # Calculate the optimal light level to reach the target value,
            #  given the amount of time the LightBehavior will be running and
            #  the amount of ambient light expected to be received when
            #  the LightBehavior is not running.  Set the optimal limits
            #  for the LightBehavior based on this calculation

            # BEGIN STUDENT CODE
            curr_t = self.mtime
            future_t = (3600.0 * 24)

            # print(f"Time Passed: {self.dt}")
            # print(f"Current Time: {clock_time(curr_t)}")
            
            # Additional insolation
            insolation_dt = (self.dt * self.light) / 3600.0
            self.insolation += insolation_dt

            # print(f"Perceived Light: {self.light}")
            # print(f"Insolation Change: {insolation_dt}")

            # LightBehavior time remaining and Expected future ambient insolation
            future_behavior_time = self.lighting_time_left(curr_t) / 3600.0
            future_ambient_insolation = self.non_lighting_ambient_insolation(curr_t, future_t)

            # print(f"Behavior Time Left: {future_behavior_time}")
            # print(f"Future Ambient Insolation: {future_ambient_insolation}")

            if future_behavior_time:
                self.current_optimal = (self.target - self.insolation - future_ambient_insolation) / future_behavior_time
            else:
                self.current_optimal = 0
            
            # print(f"Insolation: ({self.insolation} / {self.target})")
            # print(f"Optimal Value: {self.optimal_value}\n")
            # END STUDENT CODE
            pass

    def integrate_ambient(self, ts, te):
        ambient_insolation = 0
        t1, v1 = self.ambient_data[0]
        for index in range(1, len(self.ambient_data)):
            t2, v2 = self.ambient_data[index]
            if (ts < t2 and te > t1):
                if (ts > t1): # Starts within an interval
                    v1 = v1 + ((v2 - v1)*(ts - t1)/(t2 - t1))
                    t1 = ts
                if (te < t2): # Ends within an interval
                    v2 = v1 + ((v2 - v1)*(te - t1)/(t2 - t1))
                    t2 = te
                mval = (v1 + v2)/2.0
                ambient_insolation += mval*(t2 - t1)/3600.0
            t1, v1 = self.ambient_data[index]
        return ambient_insolation

    # Helper function:
    # How much ambient light will there be when LightBehavior is not running
    #  between start time (ts) and end time (te)
    def non_lighting_ambient_insolation(self, ts, te):
        ambient_light = 0
        t, t_last = (ts, 0)
        for interval in self.lighting_intervals:
            if (te <= interval[0]): break
            elif (t < interval[0]):
                t = max(t, t_last)
                ambient_light += self.integrate_ambient(t, min(te, interval[0]))
                t = interval[1]
            t_last = interval[1]

        if (te > t):
            ambient_light += self.integrate_ambient(t, te)
        #print("AMBIENT INSOLATION: (%d, %d) %.1f" %(ts/3600, te/3600, ambient_light))
        return ambient_light

    # Helper function:
    # How much time is left in the schedule for LightBehavior to run
    def lighting_time_left(self, time):
        time_left = 0
        for interval in self.lighting_intervals:
            if (interval[0] <= time and time < interval[1]):
                time_left = interval[1] - time
            elif (time < interval[0]):
                time_left += interval[1] - interval[0]

        return time_left

