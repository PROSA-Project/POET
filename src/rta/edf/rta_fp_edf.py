"""
This module the calculations of the RTA fixpoints for Fully Preemptive Earliest-Deadline First (FP-EDF). 
"""
from utils import rt_utils
import rta.edf.edf as edf

class FullyPreemptiveEarliestDeadlineFirstRTA:
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

    def search_space_solution (self, task_set, tsk, A):
        def F_fixpoint (task_set, A, tsk, F):
            # Computes f for the fixpoint:
            # A + F = task_rbf (A + ε) + bound_on_total_hep_workload A (A + F)
            task_rbf = tsk.task_request_bound_function(A+1)
            bound_hep = edf.bound_on_total_hep_workload(task_set, tsk, A, A+F)
            return max(task_rbf + bound_hep - A, 0)

        fix_fun = lambda f, A=A: F_fixpoint (task_set, A, tsk, f)
        F = rt_utils.compute_fixpoint (fix_fun, 1)
        return F

    ####################################
    # Response-time 
    ####################################

    def response_time(self, Fs, tsk):
        m = 0
        for tsk_ss in Fs:
            m = max(m, max(tsk_ss, default=0))
        return m