# Import Python wrapper for or-tools CP-SAT solver.
from ortools.sat.python import cp_model
import visualize_solution

class BehaviorInfo:
    def __init__(self, min_extent, night_extent, min_spacing, max_spacing):
        self.min_extent = min_extent
        self.night_extent = night_extent
        self.min_spacing = min_spacing
        self.max_spacing = max_spacing

    def __repr__(self):
        return f"<{self.min_extent}, {self.night_extent}, {self.min_spacing}, {self.max_spacing}>"

class GreenhouseScheduler:

    # The GreenhouseScheduler class takes the following parameters:
    # behaviors_info: a dictionary whose keys are behavior names and whose
    #    values of instances of class BehaviorInfo:
    #    min_extent: the least cumulative amount of time in minutes that the 
    #       behavior needs to be run
    #    night_extent: the maximum amount of time the behavior should run at
    #       night between [20,24) U [0,8)
    #    min_spacing: the minimum amount of time between two instances of the behavior
    #    max_spacing: the maximum amount of time between two instances of the behavior
    # minutes_per_chunk: the number of minutes in each time block of the schedule
    # sched_file: the name of the file the schedule is to be written to, if not None

    def __init__(self, behaviors_info, minutes_per_chunk, sched_file=None,
                 max_constraint=4):
        self.behaviors_info = behaviors_info
        self.minutes_per_chunk = minutes_per_chunk #all are the same length
        self.horizon = 24*60//self.minutes_per_chunk
        self.sched_file = sched_file
        self.createModel(max_constraint)

    def createVariables (self):
        # Create behavior/time dictionary mapping to binary variables.
        self.all_jobs = {}
        for behavior in self.behaviors_info:
            for time in range(self.horizon):
                suffix = '%s_%i' % (behavior, time)
                # Boolean variable for whether behavior is enabled at that time
                self.all_jobs[behavior,time] = self.model.NewBoolVar(suffix)

    def createModel (self, max_constraint=4):
        # Create the model.
        self.model = cp_model.CpModel()
        self.createVariables()
        if (max_constraint >= 1): self.createDurationConstraints(self.model)
        if (max_constraint >= 2): self.createMutualExclusiveConstraints(self.model)
        if (max_constraint >= 3): self.createNightConstraints(self.model)
        if (max_constraint >= 4): self.createSpacingConstraints(self.model)

    # This is the function to call to test the problem being solved.
    # It takes the requirements from the class constructor
    # DO NOT ALTER THIS FUNCTION!
    def solveProblem(self, visualize=False, verbose=False):
        return self.solve(self.model, visualize, verbose)

    # CREATE and add constraints for the minimum duration each behavior
    #     should be run (see self.behaviors_info)
    def createDurationConstraints(self, model):
        for behavior in self.behaviors_info:
            duration = self.behaviors_info[behavior].min_extent # in minutes
            # BEGIN STUDENT CODE
            required_chunks = duration // self.minutes_per_chunk
            curr_chunks = sum(self.all_jobs[behavior, t] for t in range(self.horizon))
            model.Add(curr_chunks >= required_chunks)
            # END STUDENT CODE
            pass

    # CREATE and add constraints for behaviors that cannot be run
    #   simultaneously for each time
    # 1. All raising and lowering behaviors for the same value (temperature,
    #    humidity, moisture) must be mutually exclusive
    # 2. Any two behaviors in this list that need to use the same
    #    actuator on (e.g., LowerHumid, LowerMoist) or in which one wants the
    #    actuator on and one wants it off (e.g., LowerHumid and RaiseTemp)
    #    must be mutually exclusive (note: they are not exclusive if they
    #    both need the actuator off)
    #      LowerTemp: fan on, lights off
    #      RaiseTemp: lights on, fan off
    #      LowerHumid: fan on, wpump off
    #      LowerMoist: fan on, wpump off
    #      RaiseMoist: fan off, wpump on
    #      Lights: lights on
    #      TakeImage: lights on
    def createMutualExclusiveConstraints(self,model):
        from itertools import product
        for time in range(self.horizon):
            # BEGIN STUDENT CODE
            mutexes_simple = [
                ('LowerTemp', 'RaiseTemp'),
                ('LowerMoist', 'RaiseMoist'),
                ('RaiseMoist', 'LowerHumid')
            ]

            actuators = {
                            #  Fan,   Light, Wpump
                "LowerTemp":  (True,  False, None),
                "RaiseTemp":  (False, True,  None),
                "LowerHumid": (True,  None,  False),
                "LowerMoist": (True,  None,  False),
                "RaiseMoist": (False, None,  True),
                "Light":      (None,  True,  None),
                "TakeImage":  (None,  True,  None)
            }

            fan_on = []
            fan_off = []
            light_on = []
            light_off = []
            wpump_on = []
            wpump_off = []

            for behavior in actuators:
                fan, light, wpump = actuators[behavior]
    
                if fan == True:
                    fan_on.append(behavior)
                elif fan == False:
                    fan_off.append(behavior)
    
                if light == True:
                    light_on.append(behavior)
                elif light == False:
                    light_off.append(behavior)
    
                if wpump == True:
                    wpump_on.append(behavior)
                elif wpump == False:
                    wpump_off.append(behavior)

            mutex_candidates = []
            mutex_candidates.extend(product(fan_on, fan_off))
            mutex_candidates.extend(product(light_on, light_off))
            mutex_candidates.extend(product(wpump_on, wpump_off))
            mutex_candidates.extend(product(fan_on, fan_on))
            mutex_candidates.extend(product(light_on, light_on))
            mutex_candidates.extend(product(wpump_on, wpump_on))
            mutex_candidates += mutexes_simple

            filtered_mutex_candidates = []
            for mutex_candidate in mutex_candidates:
                local_l = [mutex_candidate[0], mutex_candidate[1]]
                if len(set(local_l)) > 1:
                    filtered_mutex_candidates.append(tuple(sorted(local_l)))

            filtered_mutex_candidates = set(filtered_mutex_candidates)

            for behavior1, behavior2 in filtered_mutex_candidates:
                if behavior1 in self.behaviors_info and behavior2 in self.behaviors_info:
                    model.Add(self.all_jobs[behavior1, time] + self.all_jobs[behavior2, time] <= 1)
            # END STUDENT CODE
            pass

    # CREATE and add constraints for maximum amount of time behaviors should
    # be run at night between [20,24) U [0,8)
    def createNightConstraints(self, model):
        for behavior in self.behaviors_info:
            max_night = self.behaviors_info[behavior].night_extent # in minutes
            # BEGIN STUDENT CODE
            m = self.minutes_per_chunk
            model.Add(sum(self.all_jobs[behavior, t] for t in range(self.horizon)
                        if (h:=((t*m)//60)%24) < 8 or h >= 20) <= max_night//m)
            # END STUDENT CODE
            pass

    # Create and add constraints so that the minimum spacing between behaviors
    #   is the minimum time (given in minutes - convert to chunks), and at least
    #   one behavior is scheduled to run before the maximum time is up
    # If the maximum night-time running is zero, apply these constraints only
    #   during the day (8am to 8pm).
    # Also, the maximum constraint does not hold if there is not enough time
    #   before the end time (either midnight or 8pm)
    def createSpacingConstraints(self,model):
        for behavior in self.behaviors_info:
            chunk = self.minutes_per_chunk
            min_spacing = self.behaviors_info[behavior].min_spacing
            max_spacing = self.behaviors_info[behavior].max_spacing
            # BEGIN STUDENT CODE
            min_b = min_spacing // chunk
            max_b = max_spacing // chunk

            night = (self.behaviors_info[behavior].night_extent > 0)

            start = 0 if night else (8 * 60) // chunk
            end = self.horizon if night else (20 * 60) // chunk
            
            window_len = min_b + 1
            for left in range(start, end - window_len + 1):
                model.Add(sum(self.all_jobs[behavior, t] for t in range(left, left + window_len)) <= 1)
            
            for left in range(start, end - max_b + 1):
                model.Add(sum(self.all_jobs[behavior, t] for t in range(left, left + max_b)) >= 1)
            # END STUDENT CODE

    # Solve model.
    def solve(self,model, visualize, verbose):
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.INFEASIBLE:
            if verbose: print("infeasible")
            return None
        else:
            save = self.sched_file != None
            if verbose: print("feasible")
            assigned_jobs_list = {}
            i =0
            blist = self.behaviors_info.keys()

            if save: f = open(self.sched_file,"w")

            # (optionally) print and write out the schedule
            for behavior in blist:
                if verbose: print("Behavior:",behavior)
                s = "  Times: "
                for t in range(self.horizon):
                    if solver.Value(self.all_jobs[behavior,t]) > 0:
                        assigned_jobs_list[i,i,t/2.] = 1
                        s += str(t/2.)+" "
                        if save: 
                            f.write(behavior+"Behavior"+" ")
                            f.write(("0" if t/2 < 10 else "")+str(int(t//2))+
                                    (":00" if t/2 == t//2 else ":30")+"-")
                        x = t + 1
                        if save:
                            f.write(("0" if x/2 < 10 else "")+str(int(x//2))+
                                    (":00" if x/2 == x//2 else ":30")+"\n")
                if verbose: print(s)
                if save: f.write("\n")
                i += 1

            # Finally print the solution found.
            if status == cp_model.OPTIMAL:
               if verbose: print('Student Optimal Schedule Length: %i' % solver.ObjectiveValue())
            if visualize:
                visualize_solution.plot_binary(blist, self.horizon/2, False, 0.5, assigned_jobs_list)
            return assigned_jobs_list

if __name__ == "__main__":
    # This is an example Schedule generation problem
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

