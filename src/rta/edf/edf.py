from utils import rt_utils

####################################
# Max Busy Interval
####################################

def max_busy_interval(task_set, tsk):
    f = lambda delta : total_request_bound_function(task_set, delta)
    L = rt_utils.compute_fixpoint (f, 1)
    return L

####################################
# Search space
####################################

def search_space(task_set, L, tsk):

    def offset_to_steps(tsk, tsko, offset): 
        emax_offset = tsko.arrival_curve.time_steps_with_offset(offset)
        return [max(0, o + tsko.deadline - tsk.deadline - 1)
                    for o in emax_offset if o + tsko.deadline >= tsk.deadline]


    SS = [] 
    for tsko in task_set:
        h = tsko.arrival_curve.h
        r = (L + max(0,tsk.deadline - tsko.deadline)) // h + 1

        def binary_search(r):
            l, r = 0, r
            while r - l > 10: 
                m = int((r + l) / 2)
                if offset_to_steps(tsk, tsko, h * m) == []: 
                    l = m
                else:
                    r = m
            return l

        l = binary_search(r)
        SS += [[A for r in range(l, r) for A in offset_to_steps(tsk, tsko, h * r)]]

    return SS

####################################
# Workload 
####################################

def total_request_bound_function(task_set, dt):
    return sum ([t.task_request_bound_function(dt) for t in task_set])

def bound_on_total_hep_workload (task_set, tsk, A, delta):
    sum = 0
    for to in task_set:
        if to != tsk:
            min_int = min(A+1 + tsk.deadline - to.deadline, delta)
            min_int = max(min_int, 0) # Clamp at 0
            sum += to.task_request_bound_function(min_int)
    
    return sum