import math

####################################
# Search space
####################################

def search_space(L, tsk):

    def offset_to_steps(tsk, offset): 
        emax_offset = tsk.arrival_curve.time_steps_with_offset(offset)
        return [max(0, o - 1) for o in emax_offset]

    h = tsk.arrival_curve.h
    r = L // h + 1
    SS = [A for r in range(r) for A in offset_to_steps(tsk, h * r)]

    return SS

####################################
# Workload calculations
####################################

def total_ohep_rbf (task_set, tsk, delta):
    sum = 0
    for t in task_set:
        if t.priority >= tsk.priority and t != tsk:
            sum += t.task_request_bound_function(delta)
    return sum

def total_hep_rbf (task_set, tsk, delta):
    return total_ohep_rbf (task_set, tsk, delta) + tsk.task_request_bound_function(delta)
