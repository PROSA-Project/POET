"""
This module the calculations of the RTA fixpoints for Fully Preemptive Fixed Priority (FP-FP).
"""

import rta.fp.fp as fp
from utils import rt_utils


class NonPreemptiveFixedPriorityRTA:
    def __init__(self, task_set):
        # Calculating blocking bound
        self.blocking_bound = {}
        for t in task_set:
            bound = max(
                [tt.wcet - 1 for tt in task_set if tt.priority < t.priority], default=0
            )
            assert bound >= 0
            self.blocking_bound[t.id] = bound

    ####################################
    # Max Busy Interval
    ####################################

    def max_busy_interval(self, task_set, tsk):
        def f(delta):
            return self.blocking_bound[tsk.id] + fp.total_hep_rbf(task_set, tsk, delta)

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
            # A + F = blocking_bound
            #    + (task_rbf (A + ε) - (task_cost tsk - ε))
            #    + total_ohep_rbf (A + F)
            blocking_bound = self.blocking_bound[tsk.id]
            task_rbf = tsk.task_request_bound_function(A + 1)
            task_cost = tsk.wcet - 1
            bound_hep = fp.total_ohep_rbf(task_set, tsk, A + F)

            result = blocking_bound + task_rbf - task_cost + bound_hep - A

            return max(result, 0)

        def fix_fun(F, A=A):
            return F_fixpoint(task_set, A, tsk, F)

        F = rt_utils.compute_fixpoint(fix_fun, 1)
        return F

    ####################################
    # Response-time
    ####################################

    def response_time(self, Fs, tsk):
        m = max(0, max(Fs))
        return m + tsk.wcet - 1
