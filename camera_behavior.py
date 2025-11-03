from behavior import *
from greenhouse_behaviors import Greenhouse_Behavior
from transitions import Machine
import os, os.path as op

'''
The behavior should adjust the lights to a reasonable level (say 400-600),
wait a bit for the light to stabilize, and then request an image.
It should check to be sure the image has been recorded and, if so, process
the image; if not, try again for up to 3 times before giving up
'''
class TakeImage(Greenhouse_Behavior):
    def __init__(self, agent):
        super(TakeImage, self).__init__(agent, "TakeImageBehavior")
        # Your code here
	    # Initialize the FSM and add transitions
        # BEGIN STUDENT CODE
        self.retries = 0
        self.images = 0 
        self.pathroot = "/home/robotanist/User/images/"
        if not os.path.exists(self.pathroot): os.makedirs(self.pathroot)
        self.last_time = 24*60*60
        self.led = 0
        
        self.initial = 'Halt'
        self.states = [self.initial, "idle", "change_light", "get_image", "wait_for_file"]
        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        self.fsm.add_transition('enable', self.initial, 'idle')
        self.fsm.add_transition('doStep', 'idle', 'idle', conditions='next_day', after='reset_day')
        self.fsm.add_transition('doStep', 'idle', 'change_light', conditions=['can_take_image'], unless=['light_is_optimal'], after='change_light')
        self.fsm.add_transition('doStep', 'change_light', 'change_light', conditions=['can_take_image'], unless=['light_is_optimal'], after='change_light')
        self.fsm.add_transition('doStep', 'idle', 'get_image', conditions=['can_take_image', 'light_is_optimal'], after=['setTimer5'])
        self.fsm.add_transition('doStep', 'change_light', 'get_image', conditions=['can_take_image', 'light_is_optimal'], after=['setTimer5'])
        self.fsm.add_transition('doStep', 'get_image', 'wait_for_file', conditions=['time_up'], before=['get_image'], after=['setTimer10'])
        self.fsm.add_transition('doStep', 'wait_for_file', 'idle', conditions=['time_up', 'file_exists'], before=['finish_image'])
        self.fsm.add_transition('doStep', 'wait_for_file', 'wait_for_file', conditions=['time_up', 'no_file_exists', 'retry_allowed'], after=['setTimer20', 'update_retry'])
        self.fsm.add_transition('doStep', 'wait_for_file', 'idle', conditions=['time_up', 'no_file_exists', 'no_retry_allowed'], before=['warning'])
        self.fsm.add_transition('disable', 'idle', self.initial, after='setLastTime')
        self.fsm.add_transition('disable', 'change_light', self.initial, after='setLastTime')
        self.fsm.add_transition('disable', 'get_image', self.initial, after='setLastTime')
        self.fsm.add_transition('disable', 'wait_for_file', self.initial, after='setLastTime')
        # END STUDENT CODE

    # Add the condition and action functions
    #  Remember: if statements only in the condition functions;
    #            modify state information only in the action functions
    # BEGIN STUDENT CODE
    def next_day(self):
        return self.last_time > self.mtime
    def light_is_optimal(self):
        return 400 <= self.light < 600
    def can_take_image(self):
        return self.images < 3
    def file_exists(self):
        return op.exists(self.pathname)
    def no_file_exists(self):
        return not op.exists(self.pathname)
    def retry_allowed(self):
        return self.retries < 3
    def no_retry_allowed(self):
        return self.retries >= 3
    def time_up(self):
        return self.time >= self.waittime

    def setTimer(self, wait):
        self.waittime = self.time + wait
    def setTimer5(self):
        self.setTimer(5)
    def setTimer10(self):
        self.setTimer(10)
    def setTimer20(self):
        self.setTimer(20)
    def change_light(self):
        if self.light < 600:
            self.setLED(self.led+20)
        elif self.light >= 400:
            self.setLED(self.led-20)
    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": self.led}))
    def get_image(self):
        filename = f"image_{self.time}.jpg"
        self.pathname = op.join(self.pathroot, filename)
        self.actuators.doActions((self.name, self.sensors.getTime(), {"camera": self.pathname}))
    def update_retry(self):
        self.retries += 1
    def finish_image(self):
        self.images += 1
        self.retries = 0
    def warning(self):
        self.retries = 0
    def reset_day(self):
        self.images = 0
        self.setLastTime()
    def setLastTime(self):
        self.last_time = self.mtime
    # END STUDENT CODE

    def perceive(self):
        self.mtime = self.sensordata["midnight_time"]
        self.time = self.sensordata["unix_time"]
        self.light = self.sensordata["light"]

    def act(self):
        self.trigger("doStep")
