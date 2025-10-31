# Import Python wrapper for or-tools CP-SAT solver.
from ortools.sat.python import cp_model
import visualize_solution
import dill
from greenhouse_scheduler import BehaviorInfo

grader_files = "grader_files/"
greenhouse_refsol = grader_files + "/GreenhouseRefsol.pkl"

class GreenhouseScheduler:

    # The GreenhouseScheduler class takes the following parameters:
    # name: the name of the schedule to be written to
    # behaviors_info: a dictionary whose keys are behavior names and whose
    #  values are tuples (t, s, m), where:
    #  t: the least cumulative amount of time in minutes that the behavior
    #     needs to be run
    #  s: the spacing between the behaviors in minutes (min, max)
    #     s.t. <= 1 run in min time and >= 1 in max time
    #     This is used only for some behaviors: (LowerTemp, LowerHumid,
    #     LowerMoist, TakeImage, RaiseTemp, RaiseMoist) and not for any other
    #  m: the maximum amount of time the behavior should run at night
    #     between [20,24) U [0,8)
    # minutes_per_chunk: the number of minutes that the day is broken into

    def __init__(self, behaviors_info, minutes_per_chunk, sched_file=None):

        with open(greenhouse_refsol, "rb") as f:
            refsol_class = dill.load(f)
        self.refsol = refsol_class(behaviors_info, minutes_per_chunk,
                                   sched_file)

    # This is the function that tests the problem being solved.
    # It takes the requirements from init and whether to visualize the schedule
    def solveProblem(self, visualize=False, verbose=False):
        return self.refsol.solveProblem(visualize, verbose)

if __name__ == "__main__":
    #This is an example Schedule generation problem

    #schedule 30 minute chunks
    minutes = 30

    # Light should be on for at least 8 hours during the day (not on at night)
    #   Instances can be scheduled back-to-back (0 min time) but
    #   at least every 4 hours during the day
    behaviors_info = {}
    behaviors_info["Light"] =      BehaviorInfo(8*60,     0,    0, 4*60)
    behaviors_info["LowerHumid"] = BehaviorInfo(8*60, 12*60,   30, 2*60)
    behaviors_info["LowerTemp"] =  BehaviorInfo(4*60, 12*60, 2*60, 4*60)
    behaviors_info["RaiseTemp"] =  BehaviorInfo(2*60, 12*60, 2*60, 4*60)
    behaviors_info["LowerMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
    behaviors_info["RaiseMoist"] = BehaviorInfo(2*60, 12*60, 2*60, 4*60)
    # camera should not be on at all at night
    behaviors_info["TakeImage"] =  BehaviorInfo(1*60, 0,     3*60, 6*60)

    problem = GreenhouseScheduler(behaviors_info, minutes, "main_schedule.txt")
    problem.solveProblem(verbose=True) #visualize=True)
