from greenhouse_scheduler import BehaviorInfo, GreenhouseScheduler

# Default behaviors:
behaviors_info = {}
behaviors_info["Light"] =      BehaviorInfo(8*60,     0,    0, 4*60)
behaviors_info["LowerHumid"] = BehaviorInfo(8*60, 12*60,   30, 2*60)
behaviors_info["LowerTemp"] =  BehaviorInfo(4*60, 12*60, 2*60, 4*60)
behaviors_info["RaiseTemp"] =  BehaviorInfo(2*60, 12*60, 2*60, 4*60)
behaviors_info["LowerMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
behaviors_info["RaiseMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
behaviors_info["TakeImage"] =  BehaviorInfo(1*60, 0,     3*60, 6*60)

def plot(schedule_file):
    pass