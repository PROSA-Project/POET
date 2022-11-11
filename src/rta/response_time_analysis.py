"""
This module picks the correct rta to apply to the problem instance
"""

from structures import pg
from rta.fp import rta_fp_fp, rta_np_fp
from rta.edf import rta_fp_edf, rta_np_edf

def pick_rta (problem_instance):
    pm = problem_instance.preemption_model
    if pm == pg.FULLY_PREEMPTIVE:                 return _pick_fp_rta(problem_instance)
    if pm == pg.NON_PREEMPTIVE:                   return _pick_np_rta(problem_instance)
    if pm == pg.LIMITED_PREEMPTIVE:               return _pick_lp_rta(problem_instance)
    if pm == pg.FLOATING_NON_PREEMPTIVE_SEGMENTS: return _pick_fnps_rta(problem_instance)

def _pick_fp_rta (problem_instance):
    p = problem_instance.scheduling_policy
    if p == pg.FIXED_PRIORITY:          
        return rta_fp_fp.FullyPreemptiveFixedPriorityRTA()
    if p == pg.EARLIEST_DEADLINE_FIRST: 
        return rta_fp_edf.FullyPreemptiveEarliestDeadlineFirstRTA()
    assert False, "Scheduling policy not valid."
     
def _pick_np_rta (problem_instance):
    ts = problem_instance.task_set
    p = problem_instance.scheduling_policy

    if p == pg.FIXED_PRIORITY: 
        return rta_np_fp.NonPreemptiveFixedPriorityRTA(ts)
    if p == pg.EARLIEST_DEADLINE_FIRST:
        return rta_np_edf.NonPreemptiveEarliestDeadlineFirstRTA(ts)
    assert False, "Scheduling policy not valid."

def _pick_lp_rta (problem_instance):
    p = problem_instance.scheduling_policy
    if p == pg.FIXED_PRIORITY:          return None
    if p == pg.EARLIEST_DEADLINE_FIRST: return None
    assert False, "Scheduling policy not valid."

def _pick_fnps_rta (problem_instance):
    p = problem_instance.scheduling_policy
    if p == pg.FIXED_PRIORITY:          return None
    if p == pg.EARLIEST_DEADLINE_FIRST: return None
    assert False, "Scheduling policy not valid."