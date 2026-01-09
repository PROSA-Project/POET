"""
This module the calculations of the RTA fixpoints for Fully Preemptive Earliest-Deadline First (FP-EDF). 
"""
from utils import rt_utils
import rta.edf.edf as edf


class NonPreemptiveEarliestDeadlineFirstRTA:
    def __init__(self, task_set):
        # Calculating blocking bound
        self.blocking_bound = {}
        for t in task_set:
            bound = max(
                [to.wcet - 1 for to in task_set if to.deadline > t.deadline], default=0
            )
            assert bound >= 0
            self.blocking_bound[t.id] = bound

    ####################################
    # Max Busy Interval
    ####################################

    def max_busy_interval(self, task_set, tsk):
        return edf.max_busy_interval(task_set, tsk)

    ####################################
    # Search space
    ####################################

    def search_space(self, task_set, L, tsk):
        return edf.search_space(task_set, L, tsk)

    ####################################
    # Search space solutions (Fs)
    ####################################

    def search_space_solution(self, task_set, tsk, A):
        def F_fixpoint(task_set, A, tsk, F):
            # A + F = blocking_bound + (task_rbf (A + ε) - (task_cost tsk - ε))
            #    + bound_on_total_hep_workload A (A + F)
            blocking_bound = self.blocking_bound[tsk.id]
            task_rbf = tsk.task_request_bound_function(A + 1)
            task_cost = tsk.wcet - 1
            bound_hep = edf.bound_on_total_hep_workload(task_set, tsk, A, A + F)

            F = blocking_bound + max(0, task_rbf - task_cost) + bound_hep - A
            return max(0, F)

        def fix_fun(f, A=A):
            return F_fixpoint(task_set, A, tsk, f)
        F = rt_utils.compute_fixpoint(fix_fun, 1)
        return F

    ####################################
    # Response-time
    ####################################

    def response_time(self, Fs, tsk):
        # R = max F + (task_cost tsk - ε).
        m = 0
        for tsk_ss in Fs:
            m = max(m, max(tsk_ss, default=0))
        return m + tsk.wcet - 1
