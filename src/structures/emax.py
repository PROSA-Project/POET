"""
This module a step-based implementation of an eta-max curve (i.e., arrival curve).
"""

import math
from enum import Enum
from utils import rt_utils

class Emax:
    def __init__(self, horizon, steps):
        self.h = horizon
        self.steps = steps

        self.check_validity()

        assert horizon >= (steps[-1][0])

    def __str__(self) -> str:
        return f"[{self.h},{self.steps}]"
    __repr__ = __str__

    def _step_at(self, t):
        assert t < self.h 

        steps = [s[1] for s in self.steps if s[0] <= t]
        if len(steps) > 0:
            return steps[-1]
        else:
            return 0

    def check_validity(self):

        assert len(self.steps) > 0

        assert self.h > self.steps[-1][0], "The horizon must be greater than the last step"

        assert self.steps[0][1] > 0, "The arrival curve must not contain zeros"

        # If this condition does not hold, there is no hope for the prefix 
        # to be subadditive, as you can take the (1,1) decomposition which has 
        # value 0, so their sum is 0 as well
        assert self.steps[0][0] == 1, "A window of size 1 must be specified"

        # Checking strict monotonicity of steps
        assert all(self.steps[i][0] < self.steps[i+1][0] \
                   for i in range(len(self.steps)-1)), \
                   "steps must be monotonic"
        assert all(self.steps[i][1] < self.steps[i+1][1] \
                for i in range(len(self.steps)-1)), \
                "steps must be monotonic"
                

    # fast extension 
    # t %/ h * prefix h + prefix (t %% h).
    def at(self, t):
        h = self.h
        eh = self.steps[-1][1]

        return (t // h) * eh + self._step_at(t % h) 

    def time_step_after(self, t):
        # Given a time t, returns the next time at which the emax function steps
        offset = (t // self.h) * self.h
        t = t % self.h
        steps = [s[0] for s in self.steps if s[0] > t + 1]
        if len(steps) > 0:
            t = steps[0]
        else: # t is between the last step and the horizon => use horizon + the first step 
            t = self.h + self.steps[0][0]
        
        return offset + t - 1

    def step_size(self, step_index):
        assert step_index < len(self.steps)
        step = self.steps[step_index]
        
        if step_index == len(self.steps)-1:
            return self.h - step[0]
        else:
            next_step = self.steps[step_index+1]
            return next_step[0] - step[0]


    def time_steps_with_offset(self, o):
        return [s[0] + o for s in self.steps]

    def repeat_steps_with_offset(self, os):
        return [t for o in os for t in self.time_steps_with_offset(o)]