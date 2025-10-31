#!/usr/bin/env python
import argparse, dill, ortools
from ortools.sat.python import cp_model
import visualize_solution as vs
from job_scheduler import PartsTask, JobScheduler
from parse_orders import get, parse_orders
from greenhouse_scheduler import GreenhouseScheduler, BehaviorInfo
import schedule as sched

grader_files = "grader_files"
jobs_refsol_file = grader_files + "/JobsRefsol.pkl"
greenhouse_refsol_file = grader_files + "/GreenhouseRefsol.pkl"

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--part', default=-1, type=int,
                    help='Which part to test (defaults to all)')
parser.add_argument('-s', '--step', default=-1, type=int,
                    help='Which step to test (defaults to all)')
parser.add_argument('-t', '--test', default=None,
                    help='Which tests to perform - can be a single test or list, (defaults to all); use ? to see which are valid')
parser.add_argument('-g', '--graphics', action='store_true',
                    help="Visualize the schedules")
parser.add_argument('-v', '--verbose', action='store_true',
                    help="Verbose output")

args = parser.parse_args()

##########################################################
#   JOB SCHEDULING AUTOGRADER
##########################################################

class JS_Solution:
    def __init__(self, name, solution, use_costs, objective, value, cost):
        self.name = name
        self.solution = solution
        self.use_costs = use_costs
        self.objective = objective
        self.value = value
        self.cost = cost

    def __repr__(self):
        return "<JS_Solution %s: (%d %d %d) %s>" %(self.name, self.objective,
                                                   self.value, self.cost,
                                                   self.solution)
    def print_solution(self, type, jobs):
        print("%s solution:" %type)
        print(" Objective: %d" %self.objective)
        if (self.use_costs):
            print(" Value: %d, Cost: %d" %(self.value, self.cost))
        for job in jobs:
            jname = job.name
            if jname in self.solution:
                print("  %s: %s" %(jname, self.solution[jname]))
            else: print("  %s: Not scheduled" %jname)
        
# order: a JobScheduler instance
# max_constraint: which constraints to apply
class JS_Test:
    def __init__(self, order, max_constraint):
        self.name = order.name
        self.use_costs = order.use_costs
        self.solution = None
        self.order = order
        self.order.create_model(max_constraint)

    def solve(self, verbose=False, visualize=False):
        solution, solver = self.order.solve()
        is_solved = False
        if (verbose):
            print(" Branches: %d" %solver.NumBranches())
            print(" Wall time: %f" %solver.WallTime())
        if (solution == None):
            print("  Infeasible schedule!!")
        elif (len(solution) == 0):
            print("  Empty schedule!!")
        elif (not check_solution_syntax(solution, self.order)):
            print("  Your solution is not compatible with the required format;")
            print("    Use -v to see what your solution format looks like\n")
        else:
            is_solved = True

        if (is_solved):
            objective = solver.Value(self.order.objective)
            use_costs = self.order.use_costs
            if (use_costs):
                value = solver.Value(self.order.value)
                cost = solver.Value(self.order.cost)
            else:
                value = cost = 0
            self.solution = JS_Solution(self.name, solution, use_costs,
                                        objective, value, cost)
        return is_solved

    def print_solution(self, type):
        if self.solution == None: print("%s: No solution" %type)
        else: self.solution.print_solution(type, self.order.jobs)
            
# refsol is a list [schedule, objective, value, cost]
def is_schedule_correct(test, js_class, refsol, max_constraint, verbose=False):
    order = test.order
    tname = order.name
    solution = test.solution.solution

    ref_order = js_class(tname, order.deadline, order.jobs, order.tasks,
                         order.machines, order.parts, order.tools,
                         order.use_costs, order.use_parts)
    ref_test = JS_Test(ref_order, max_constraint)

    # Check whether solution is compatible with the refsol class constraints
    is_correct = True
    ref_model = ref_order.model
    try:
        for jname in solution:
            tasks = get(jname, test.order.jobs).tasks
            for idx, (mname, start, duration) in enumerate(solution[jname]):
                tname = tasks[idx].name
                end = start + duration
                ref_model.Add(ref_order.scheduleds[jname, tname, mname] == True)
                ref_model.Add(ref_order.starts[jname, tname, mname] == start)
                ref_model.Add(ref_order.ends[jname, tname, mname] == end)
        is_solved = ref_test.solve(False, False)
        #status = cp_model.CpSolver().Solve(ref_model)
    except Exception as inst:
        print("EXCEPTION", inst.args); status = cp_model.INFEASIBLE
        is_solved = False

    if (not is_solved):
        print("INCORRECT: Your solution is infeasible given the refsol constraints")
        is_correct = False
    elif (test.solution.objective != refsol.objective):
        print("INCORRECT: Your solution is NOT consistent with the refsol constraints")
        is_correct = False
    else:
        print("CORRECT: Your solution is consistent with the refsol!")

    if verbose or not is_correct:
        test.print_solution("Your")
        refsol.print_solution("Reference", test.order.jobs)

    return is_correct

def check_solution_syntax(solution, test):
    for jname in solution:
        if (not get(jname, test.jobs)): return False
        for mname, start, duration in solution[jname]:
            if (not get(mname, test.machines) or start < 0 or duration < 1):
                return False
    return True

def plot_schedule(test):
    order = test.order; solution = test.solution.solution
    assigned_jobs = {}
    for id, machine in enumerate(order.machines): machine.id = id
    for job_id, job in enumerate(order.jobs):
        if (job.name in solution):
            for machine, start, duration in solution[job.name]:
                assigned_jobs[get(machine, order.machines).id,
                              job_id] = (True, start, duration,
                                         start+duration)
    vs.plot_intervals([job.name for job in order.jobs],
                      order.deadline, True, assigned_jobs)

def do_scheduling_test(order, js_class, refsol, max_constraint,
                       visualize=False, verbose=False):
    print("Running test %s, constraints: %s"
          %(order.name, list(range(1, max_constraint+1))))
    if verbose: print(" Costs: %s, Parts: %s" %(order.use_costs, order.use_parts))
    test = JS_Test(order, max_constraint)
    status = test.solve(verbose, visualize)

    if (test.solution):
        correct = is_schedule_correct(test, js_class, refsol, max_constraint,
                                      verbose)
        if (visualize): plot_schedule(test)
        print('')
        return correct
    else: 
        refsol.print_solution("Reference", test.order.jobs)
        return False

def add_orders(filename):
    orders = {}
    for order in parse_orders(filename):
        if (orders.get(order.name)):
            raise Exception("Order %s already loaded" %order.name)
        orders[order.name] = order
    return orders

order_files = ["grader_files/orders_s1.txt", "grader_files/orders_s2.txt",
               "grader_files/orders_s3.txt", "grader_files/orders_s4.txt",
               "grader_files/orders_s5.txt", "grader_files/orders_s6.txt",
               "grader_files/orders_s7.txt", "grader_files/orders_s8.txt"]

def job_scheduling_autograder():
    global grand_tot_correct, grand_tot_num, grand_tot_points

    with open(jobs_refsol_file, "rb") as f:
        js_class, js_solutions = dill.load(f)

    step_points = [2, 2, 3, 3, 5, 5, 5, 2]
    tot_correct = tot_num = tot_points = 0
    for step in [args.step] if args.step > 0 else list(range(1,num_steps_jobs+1)):
        correct = 0
        orders = add_orders(order_files[step-1])
        all_tests = [order for order in orders]
        if (not args.test):
            tests = all_tests
        elif (args.test == '?'):
            print("Valid tests are %s" %all_tests); exit()
        else:
            tests = args.test.replace(",", " ").split(" ")
            for test in tests:
                if (not test in all_tests):
                    print("%s is not a valid test for this part" %test)
                    print("Valid tests are %s" %all_tests); exit()

        max_constraint = step
        for test_name in tests:
            order = orders[test_name]
            correct += do_scheduling_test(order, js_class,
                                          js_solutions[order.name], step,
                                          args.graphics, args.verbose)

        points = step_points[step-1]*correct/len(tests)
        print("Part 1, Step %d: %d correct out of %d (%.1f points)\n"
              %(step, correct, len(tests), points))
        tot_correct += correct; tot_num += len(tests); tot_points += points

    if (args.step < 0):
        print("Part 1: Total %d correct out of %d (%d points)\n"
              %(tot_correct, tot_num, tot_points))
    grand_tot_correct += tot_correct; grand_tot_num += tot_num
    grand_tot_points += tot_points

##########################################################
#   GREENHOUSE AUTOGRADER
##########################################################

def createStudentConstraints(problem, refsol):
    schedule = sched.readSchedule(problem.sched_file)
    for behavior in problem.behaviors_info.keys():
        behav = schedule[behavior+"Behavior"]
        for time in range(problem.horizon):
            refsol.model.Add(refsol.all_jobs[behavior, time] ==
                             isOn(behav, time, problem.minutes_per_chunk))

def isOn(times, time, minutes_per_chunk):
    for t in times:
        if (time>=t[0]//minutes_per_chunk and time<t[1]//minutes_per_chunk):
            return True
    return False

def greenhouse_test(test_num, testType, behaviors_info, minutes_per_chunk,
                    should_succeed=True):
    correct = 0
    print("Running test %s (constraints: %s) %s..."
          %(test_num, list(range(1,testType+1)),
            ("" if not args.graphics else
             "(expect a schedule image here) " if should_succeed else
             "(infeasible constraints - should not expect a schedule)" )))

    problem = GreenhouseScheduler(behaviors_info, minutes_per_chunk,
                                  max_constraint=testType)
    solution = problem.solveProblem(args.graphics)
    if (not solution):
        if should_succeed:
            print("FAILED: Your model found no solution where one exists")
        else:
            print("CORRECT: Your model found no solution for infeasible constraints")
            correct = 1
    else:
        if should_succeed:
            print("CORRECT: Your model found a solution")
            correct = 1
        else:
            print("FAILED: Your model found a solution where one should not exist")
    print("")
    return correct

def greenhouse_test_against_refsol(test_num, testType, behaviors_info,
                                   minutes_per_chunk, refsol_class):
    correct = 0
    print("Running test %s (constraints: %s) against the refsol %s..."
          %(test_num, list(range(1,testType+1)),
            ("" if not args.graphics else "(expect a schedule image here) ")))

    problem = GreenhouseScheduler(behaviors_info, minutes_per_chunk,
                                  "main_schedule.txt", max_constraint=testType)
    solution = problem.solveProblem(args.graphics, args.verbose)
    if (not solution):
        print("FAILED: Your model found no solution where one exists")
    else:
        greenhouse_refsol = refsol_class(behaviors_info, minutes_per_chunk,
                                         max_constraint=testType)
        createStudentConstraints(problem, greenhouse_refsol)
        refsol_solution = greenhouse_refsol.solveProblem(False, False)

        if (refsol_solution == None):
            print("FAILED: Your solution was INCONSISTENT with the refsol constraints")
        else:
            print("CORRECT: Your solution was consistent with the refsol constraints")
            correct = 1
    print("")
    return correct

def greenhouse_tests(testType, refsol_class, minutes_per_chunk):
    correct = num_tests = 0

    behaviors_info = {}
    behaviors_info["Light"] =      BehaviorInfo(20*30,  4*60,    0, 4*60)
    behaviors_info["LowerHumid"] = BehaviorInfo(16*30, 12*60,   30,   60)
    behaviors_info["LowerTemp"] =  BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info["RaiseTemp"] =  BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info["LowerMoist"] = BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info["RaiseMoist"] = BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info["TakeImage"] =  BehaviorInfo(2*30,      0, 3*60, 6*60)
    if testType <= 2:
        score = greenhouse_test(1, testType, behaviors_info, minutes_per_chunk)
        correct += score; num_tests += 1
    
    behaviors_info_inf = {}
    behaviors_info_inf["Light"] =      BehaviorInfo(32*30,  4*60,    0, 4*60)
    behaviors_info_inf["LowerHumid"] = BehaviorInfo(24*30, 12*60,   30,   60)
    behaviors_info_inf["LowerTemp"] =  BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info_inf["RaiseTemp"] =  BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info_inf["LowerMoist"] = BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info_inf["RaiseMoist"] = BehaviorInfo(4*30,  12*60, 2*60, 4*60)
    behaviors_info_inf["TakeImage"] =  BehaviorInfo(10*30,     0, 6*60, 6*60)

    # Feasible for duration constraints only, infeasible for mutex and beyond
    if testType <= 2:
        score = greenhouse_test(2, testType, behaviors_info_inf,
                                minutes_per_chunk, testType == 1)
        correct += score; num_tests += 1

    score = greenhouse_test_against_refsol(3, testType, behaviors_info,
                                           minutes_per_chunk, refsol_class)
    correct += score; num_tests += 1

    behaviors_info = {}
    behaviors_info["Light"] =      BehaviorInfo(9*30,      0,   0, 4*60)
    behaviors_info["LowerHumid"] = BehaviorInfo(24*30, 12*60,  30, 2*60)
    behaviors_info["LowerTemp"] =  BehaviorInfo(2*30, 12*60, 2*60, 4*60)
    behaviors_info["RaiseTemp"] =  BehaviorInfo(2*30, 12*60, 2*60, 4*60)
    behaviors_info["LowerMoist"] = BehaviorInfo(3*30, 12*60, 2*60, 4*60)
    behaviors_info["RaiseMoist"] = BehaviorInfo(2*30, 12*60, 2*60, 4*60)
    behaviors_info["TakeImage"] =  BehaviorInfo(1*30,     0, 6*60, 8*60)
    score = greenhouse_test_against_refsol(4, testType, behaviors_info,
                                           minutes_per_chunk, refsol_class)
    correct += score; num_tests += 1

    behaviors_info = {}
    # Light should be on for at least 12 hours, no more than 3 hours at night,
    #  and can be scheduled back-to-back
    behaviors_info["Light"] =      BehaviorInfo(24*30,  3*60,    0, 4*60)
    behaviors_info["LowerHumid"] = BehaviorInfo(16*30, 12*60,   30, 2*60)
    behaviors_info["LowerTemp"] =  BehaviorInfo (4*30,  4*60, 2*60, 4*60)
    behaviors_info["RaiseTemp"] =  BehaviorInfo (4*30,  4*60, 2*60, 14*60)
    behaviors_info["LowerMoist"] = BehaviorInfo (4*30,  4*60, 2*60, 8*60)
    behaviors_info["RaiseMoist"] = BehaviorInfo (3*30,  2*60, 3*60, 9*60)
    behaviors_info["TakeImage"] =  BehaviorInfo (3*30,     0, 3*60, 9*60)
    score = greenhouse_test_against_refsol(5, testType, behaviors_info,
                                           minutes_per_chunk, refsol_class)
    correct += score; num_tests += 1

    return correct, num_tests

def greenhouse_scheduling_autograder():
    global grand_tot_correct, grand_tot_num, grand_tot_points

    minutes_per_chunk = 30
    testType = 5 if (args.step < 0) else args.step
    step_points = [6, 6, 6, 9, 1]
    correct = num_tests = points = 0

    with open(greenhouse_refsol_file, "rb") as f:
        gh_class = dill.load(f)

    for testType in ([args.step] if args.step in [1,2,3,4] else
                     list(range(1,num_steps_greenhouse))):
        score, num = greenhouse_tests(testType, gh_class, minutes_per_chunk)
        correct += score; num_tests += num
        points += step_points[testType-1]*score/num
    if not args.step in [1,2,3,4]: points += step_points[4]
    print("Part 2: Total %d out of %d (%d points)" %(correct, num_tests, points))
    grand_tot_correct += correct; grand_tot_num += num_tests
    grand_tot_points += points

##########################################################
#   OVERALL AUTOGRADER
##########################################################

if (args.part in [-1, 1, 2]):
    pass
elif (args.part in [3, 4]):
    print("Part %d is not autograded" %args.part)
    exit()
else:
    print("Part %d is not part of this assignment" %args.part)
    exit()

num_steps_jobs = 8
num_steps_greenhouse = 5
grand_tot_correct = grand_tot_num = grand_tot_points = 0

if args.part in [-1, 1]:
    if args.step > num_steps_jobs or args.step == 0 or args.step < -1:
        print("Step %s out of range" %args.step)
        exit()
    else: job_scheduling_autograder()

if (args.part in [-1, 2]):
    if args.step > num_steps_greenhouse or args.step == 0 or args.step < -1:
        print("Step %s out of range" %args.step)
        exit()
    else: greenhouse_scheduling_autograder()

if (args.part == -1):
    print("\nGrand total: %d out of %d (%d points)\n"
          %(grand_tot_correct, grand_tot_num, grand_tot_points))
