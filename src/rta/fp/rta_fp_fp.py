"""
This module the calculations of the RTA fixpoints for Fully Preemptive Fixed Priority (FP-FP). 
"""
from utils import rt_utils
import rta.fp.fp as fp


class FullyPreemptiveFixedPriorityRTA:
    ####################################
    # Max Busy Interval
    ####################################

    def max_busy_interval(self, task_set, tsk):
        def f(delta):
            return fp.total_hep_rbf(task_set, tsk, delta)
        L = rt_utils.compute_fixpoint(f, 1)
        return L

    ####################################
    # Search space
    ####################################

    def search_space(self, task_set, L, tsk):
        return fp.search_space(L, tsk)

    ####################################
    # Search space solutions (Fs)
    ####################################

    def search_space_solution(self, task_set, tsk, A):
        def F_fixpoint(task_set, A, tsk, F):
            # A + F = task_rbf (A + ε) + bound_on_total_hep_workload A (A + F)
            task_rbf = tsk.task_request_bound_function(A + 1)
            bound_hep = fp.total_ohep_rbf(task_set, tsk, A + F)

            return max(task_rbf + bound_hep - A, 0)

        def fix_fun(f, A=A):
            return F_fixpoint(task_set, A, tsk, f)
        F = rt_utils.compute_fixpoint(fix_fun, 1)
        return F

    ####################################
    # Response-time
    ####################################

    def response_time(self, Fs, tsk):
        m = max(0, max(Fs))
        return m
