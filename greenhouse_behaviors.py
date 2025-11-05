from behavior import *
from limits import *
from transitions import Machine

#sensor data passed into greenhouse behaviors:
#  [time, lightlevel, temperature, humidity, soilmoisture, waterlevel]
#actuators are looking for a dictionary with any/all of these keywords:
#  {"led":val, "fan":True/False, "pump": True/False}

# A very basic class, so we don't have to declare enable and disable every time
class Greenhouse_Behavior(Behavior):
    def __init__(self, agent, name):
        super(Greenhouse_Behavior, self).__init__(agent, name)    
        
    def enable(self):  self.trigger('enable')
    def disable(self): self.trigger('disable')

'''
The combined ambient and LED light level between 8am and 10pm should be 
in the optimal['light_level'] range;
Between 10pm and 8am, the LEDs should be off (set to 0).
'''
class Light(Greenhouse_Behavior):

    def __init__(self, agent):
        super(Light, self).__init__(agent, "LightBehavior")
        self.optimal_level = optimal['light_level']

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'change_light', 'keep_light', 'dark']

        self.agent = agent
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='turn_off_led')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='turn_off_led')
        self.fsm.add_transition('disable', 'change_light', self.initial, after='turn_off_led')
        self.fsm.add_transition('disable', 'keep_light', self.initial, after='turn_off_led')
        self.fsm.add_transition('disable', 'dark', self.initial, after='turn_off_led')

        # _ -> dark
        self.fsm.add_transition('doStep', 'init', 'dark', unless=['is_light'], after='turn_off_led')
        self.fsm.add_transition('doStep', 'change_light', 'dark', unless=['is_light'], after='turn_off_led')
        self.fsm.add_transition('doStep', 'keep_light', 'dark', unless=['is_light'], after='turn_off_led')
        
        # _ -> change_light
        self.fsm.add_transition('doStep', 'init', 'change_light',
                                conditions=['is_light'],
                                unless=['light_is_optimal'],
                                after='change_light')
        self.fsm.add_transition('doStep', 'keep_light', 'change_light',
                                conditions=['is_light'],
                                unless=['light_is_optimal'],
                                after='change_light')
        self.fsm.add_transition('doStep', 'dark', 'change_light',
                                conditions=['is_light'],
                                unless=['light_is_optimal'],
                                after='change_light')
        self.fsm.add_transition('doStep', 'change_light', 'change_light',
                                conditions=['is_light'],
                                unless=['light_is_optimal'],
                                after='change_light')
        
        # _ -> keep_light
        self.fsm.add_transition('doStep', 'init', 'keep_light',
                                conditions=['is_light', 'light_is_optimal'])
        self.fsm.add_transition('doStep', 'change_light', 'keep_light',
                                conditions=['is_light', 'light_is_optimal'])
        self.fsm.add_transition('doStep', 'dark', 'keep_light',
                                conditions=['is_light', 'light_is_optimal'])
        # END STUDENT CODE

    def setInitial(self):
        self.led = 0
        self.setLED(self.led)
        
    def perceive(self):
        self.mtime = self.sensordata["midnight_time"]
        self.time = self.sensordata["unix_time"]
        self.light = self.sensordata["light"]
        self.adjust_optimal_level()
    
    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")
        
    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def is_light(self):
        hour = (self.mtime//3600)%24
        return hour >= 8 and hour < 22
    
    def light_is_optimal(self):
        return self.optimal_level[0] <= self.light < self.optimal_level[1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def change_light(self):
        if self.light < self.optimal_level[0]:
            self.setLED(self.led+20)
        elif self.light >= self.optimal_level[1]:
            self.setLED(self.led-20)

    def turn_off_led(self):
        self.setLED(0)
    
    def adjust_optimal_level(self):
        monitor = self.agent.getExecutiveLayer().getMonitor('LightMonitor')
        
        # Avoid over-insolation
        new_optimal_level = [(monitor.current_optimal // 1) - 45, (monitor.current_optimal // 1) + 5]
        if self.optimal_level != new_optimal_level:
            self.optimal_level = new_optimal_level

            # print(f"Adjusted Optimal Light Level: {self.optimal_level}")
        # Future consideration: RaiseTemp behavior

    # END STUDENT CODE

    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": self.led}))
                                  

"""
The temperature should be greater than the lower limit
"""
class RaiseTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseTemp, self).__init__(agent, "RaiseTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'okay', 'raising']
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='setInitial')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'okay', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'raising', self.initial, after='setInitial')

        # _ -> okay
        self.fsm.add_transition('doStep', 'init', 'okay', conditions='temp_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'raising', 'okay', conditions='temp_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'okay', 'okay', conditions='temp_okay', after='setInitial')

        # _ -> raising
        self.fsm.add_transition('doStep', 'init', 'raising', conditions='temp_low', after='raise_temp')
        self.fsm.add_transition('doStep', 'okay', 'raising', conditions='temp_low', after='raise_temp')
        self.fsm.add_transition('doStep', 'raising', 'raising', conditions='temp_low', after='raise_temp')
        # END STUDENT CODE

    def setInitial(self):
        self.setLED(0)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def temp_low(self):
        return self.temp <= limits['temperature'][0]
    
    def temp_okay(self):
        return self.temp >= optimal['temperature'][0]
    # END STUDENT CODE

    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def raise_temp(self):
        self.setLED(200)
    # END STUDENT CODE
            
    def setLED(self, level):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": level}))
        
"""
The temperature should be less than the upper limit
"""
class LowerTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerTemp, self).__init__(agent, "LowerTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'okay', 'lowering']
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='setInitial')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'okay', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'lowering', self.initial, after='setInitial')

        # _ -> okay
        self.fsm.add_transition('doStep', 'init', 'okay', conditions='temp_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'lowering', 'okay', conditions='temp_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'okay', 'okay', conditions='temp_okay', after='setInitial')

        # _ -> raising
        self.fsm.add_transition('doStep', 'init', 'lowering', conditions='temp_high', after='lower_temp')
        self.fsm.add_transition('doStep', 'okay', 'lowering', conditions='temp_high', after='lower_temp')
        self.fsm.add_transition('doStep', 'lowering', 'lowering', conditions='temp_high', after='lower_temp')
        # END STUDENT CODE

    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def temp_high(self):
        return self.temp >= limits['temperature'][1]
    
    def temp_okay(self):
        return self.temp <= optimal['temperature'][1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def lower_temp(self):
        self.setFan(True) 
    # END STUDENT CODE
            
    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
    
"""
Humidity should be less than the limit
"""
class LowerHumid(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerHumid, self).__init__(agent, "LowerHumidBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'okay', 'lowering']
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='setInitial')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'okay', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'lowering', self.initial, after='setInitial')

        # _ -> okay
        self.fsm.add_transition('doStep', 'init', 'okay', conditions='humid_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'lowering', 'okay', conditions='humid_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'okay', 'okay', conditions='humid_okay', after='setInitial')

        # _ -> raising
        self.fsm.add_transition('doStep', 'init', 'lowering', conditions='humid_high', after='lower_humid')
        self.fsm.add_transition('doStep', 'okay', 'lowering', conditions='humid_high', after='lower_humid')
        self.fsm.add_transition('doStep', 'lowering', 'lowering', conditions='humid_high', after='lower_humid')
        # END STUDENT CODE
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.humid = self.sensordata["humid"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def humid_high(self):
        return self.humid >= limits['humidity'][1]
    
    def humid_okay(self):
        return self.humid <= optimal['humidity'][1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def lower_humid(self):
        self.setFan(True) 
    # END STUDENT CODE

    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
            
"""
Soil moisture should be greater than the lower limit
"""
class RaiseSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseSMoist, self).__init__(agent, "RaiseMoistBehavior")
        self.weight = 0
        self.weight_window = []
        self.smoist_window = []
        self.total_water = 0
        self.water_level = 0
        self.start_weight = 0
        self.last_time = 24*60*60 # Start with the prior day
        self.daily_limit = 80 # New default instead of 100
        self.wet = limits["moisture"][1]

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'waiting', 'watering', 'measuring', 'done']
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='doEnable')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='doDisable')
        self.fsm.add_transition('disable', 'waiting', self.initial, after='doDisable')
        self.fsm.add_transition('disable', 'watering', self.initial, after='doDisable')
        self.fsm.add_transition('disable', 'measuring', self.initial, after='doDisable')
        self.fsm.add_transition('disable', 'done', self.initial, after='doDisable')

        # init -> _
        self.fsm.add_transition('doStep', 'init', 'init',
                                conditions='is_next_day',
                                after=['resetTotalWater', 'updateDailyLimit'])
        self.fsm.add_transition('doStep', 'init', 'waiting', conditions='time_up')

        # waiting -> _
        self.fsm.add_transition('doStep', 'waiting', 'watering',
                                unless=['cant_water'],
                                after=['setTimer10', 'startWatering'])
        self.fsm.add_transition('doStep', 'waiting', 'done',
                                conditions='watered_enough', after='startDone')
        self.fsm.add_transition('doStep', 'waiting', 'done',
                                conditions='reservoir_empty', after='startDone')
        self.fsm.add_transition('doStep', 'waiting', 'done',
                                conditions='moist_enough', after='startDone')

        # watering -> _
        self.fsm.add_transition('doStep', 'watering', 'measuring',
                                conditions='time_up', after=['setTimer300', 'startMeasuring'])

        # measuring -> _
        self.fsm.add_transition('doStep', 'measuring', 'waiting',
                                conditions='time_up', after='calcWaterAdded')

        # done -> _
        self.fsm.add_transition('doStep', 'done', 'init',
                                conditions='is_next_day', after='resetTotalWater')
        # END STUDENT CODE

        self.agent = agent
        
    def setInitial(self):
        pass

    def cant_water(self):
        w, r, m = self.watered_enough(), self.reservoir_empty(), self.moist_enough()
        loggingMonitor = self.agent.getExecutiveLayer().getMonitor('LoggingMonitor')
        loggingMonitor.logWaterAttempts(self.time, w, r, m)
        return w or r or m
        
    def sliding_window(self, window, item, length=4):
        if (len(window) == length): window = window[1:]
        window.append(item)
        return window, sum(window)/float(len(window))
    
    def perceive(self):
        self.time = self.sensordata["unix_time"]
        self.mtime = self.sensordata["midnight_time"]
        self.water_level = self.sensordata["level"]
        self.weight = self.sensordata["weight"]
        self.weight_window, self.weight_est = self.sliding_window(self.weight_window, self.weight)
        self.smoist = self.sensordata["smoist"]
        self.smoist_window, self.smoist_est = self.sliding_window(self.smoist_window, self.smoist)

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def is_next_day(self):
        return self.last_time > self.mtime
    
    def time_up(self):
        return self.time >= self.waittime
    
    def watered_enough(self):
        print(f"Watered Enough Check: {self.total_water}/{self.daily_limit}")
        return self.total_water >= self.daily_limit
    
    def reservoir_empty(self):
        print(f"Reservoir Empty Check: {self.water_level}/30")
        return self.water_level < 30
    
    def moist_enough(self):
        print(f"Moist Enough Check: {self.smoist_est}/{self.wet}")
        return self.smoist_est >= self.wet
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def setTimer(self, wait):
        self.waittime = self.time + wait
        #print("setTimer: %s (%d)" %(clock_time(self.waittime), wait))
    def setTimer10(self):
        self.setTimer(10)
    def setTimer300(self):
        self.setTimer(300)
    def setLastTime(self):
        self.last_time = self.mtime
    def calcWaterAdded(self):
        dwater = self.weight_est - self.start_weight # ml of water weighs a gram
        # Sometimes scales are off - cannot lose weight after watering
        dwater = max(0, dwater)

        self.total_water += dwater

        loggingMonitor = self.agent.getExecutiveLayer().getMonitor('LoggingMonitor')
        loggingMonitor.logWaterData(self.time, dwater)

        print("calcWaterAdded: %.1f (%.1f = %.1f - %.1f)"
              %(self.total_water, dwater, self.weight_est, self.start_weight))

    def doEnable(self):
        self.setPump(False)
        self.setTimer(10)
    
    def doDisable(self):
        self.setPump(False)
        self.setLastTime()

    def startDone(self):
        self.setLastTime()
    def resetTotalWater(self): # Reset total water each day
        print("Resetting total water")
        self.total_water = 0
        self.setLastTime()
    def startWatering(self):
        print("Starting watering")
        self.start_weight = self.weight_est
        self.setPump(True)
    def startMeasuring(self):
        print("Starting measuring")
        self.setPump(False)
    # END STUDENT CODE

    def setPump(self,state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"wpump": state}))
    
    def updateDailyLimit(self):
        scheduleMonitor = self.agent.getExecutiveLayer().getMonitor('ScheduleMonitor')
        new_limit = scheduleMonitor.getDailyWaterLimit()
        print(f"Daily watering limit updated from {self.daily_limit} mL to {new_limit} mL.")
        self.daily_limit = new_limit

"""
Soil moisture below the upper limit
"""
class LowerSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerSMoist, self).__init__(agent, "LowerMoistBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states += ['init', 'okay', 'lowering']
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        # enable
        self.fsm.add_transition('enable', self.initial, 'init', after='setInitial')

        # disable
        self.fsm.add_transition('disable', 'init', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'okay', self.initial, after='setInitial')
        self.fsm.add_transition('disable', 'lowering', self.initial, after='setInitial')

        # _ -> okay
        self.fsm.add_transition('doStep', 'init', 'okay', conditions='moisture_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'lowering', 'okay', conditions='moisture_okay', after='setInitial')
        self.fsm.add_transition('doStep', 'okay', 'okay', conditions='moisture_okay', after='setInitial')

        # _ -> raising
        self.fsm.add_transition('doStep', 'init', 'lowering', conditions='moisture_high', after='lower_moisture')
        self.fsm.add_transition('doStep', 'okay', 'lowering', conditions='moisture_high', after='lower_moisture')
        self.fsm.add_transition('doStep', 'lowering', 'lowering', conditions='moisture_high', after='lower_moisture')
        # END STUDENT CODE
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.smoist = self.sensordata["smoist"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def moisture_high(self):
        return self.smoist >= limits["moisture"][1]

    def moisture_okay(self):
        return self.smoist <= optimal['moisture'][1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def lower_moisture(self):
        self.setFan(True)
    # END STUDENT CODE
            
    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))

