""" 
This module contains basic global constants. 
"""

# The tool currently supports the following scheduling policies:
EARLIEST_DEADLINE_FIRST = "EDF"
EARLIEST_DEADLINE_FIRST_LONG = "earliest-deadline-first"
FIXED_PRIORITY = "FP"
FIXED_PRIORITY_LONG = "fixed-priority"
scheduling_policies = [
    EARLIEST_DEADLINE_FIRST,
    EARLIEST_DEADLINE_FIRST_LONG,
    FIXED_PRIORITY,
    FIXED_PRIORITY_LONG,
]

# Below are the supported preemption models:
FULLY_PREEMPTIVE = "FP"
FULLY_PREEMPTIVE_LONG = "fully-preemptive"
NON_PREEMPTIVE = "NP"
NON_PREEMPTIVE_LONG = "non-preemptive"
LIMITED_PREEMPTIVE = "LP"
LIMITED_PREEMPTIVE_LONG = "limited-preemptive"
FLOATING_NON_PREEMPTIVE_SEGMENTS = "FNPS"
FLOATING_NON_PREEMPTIVE_SEGMENTS_LONG = "floating-non-preemptive-segments"

preemption_models = [
    FULLY_PREEMPTIVE,
    FULLY_PREEMPTIVE_LONG,
    NON_PREEMPTIVE,
    NON_PREEMPTIVE_LONG,
    LIMITED_PREEMPTIVE,
    LIMITED_PREEMPTIVE_LONG,
    FLOATING_NON_PREEMPTIVE_SEGMENTS,
    FLOATING_NON_PREEMPTIVE_SEGMENTS_LONG,
]


def process_synonyms(s):
    if s == FIXED_PRIORITY_LONG:
        return FIXED_PRIORITY
    if s == EARLIEST_DEADLINE_FIRST_LONG:
        return EARLIEST_DEADLINE_FIRST
    if s == FULLY_PREEMPTIVE_LONG:
        return FULLY_PREEMPTIVE
    if s == NON_PREEMPTIVE_LONG:
        return NON_PREEMPTIVE
    if s == LIMITED_PREEMPTIVE_LONG:
        return LIMITED_PREEMPTIVE
    if s == FLOATING_NON_PREEMPTIVE_SEGMENTS_LONG:
        return FLOATING_NON_PREEMPTIVE_SEGMENTS
    return s
