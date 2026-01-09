"""
This module contains the specification of task and a task set.
"""

import math
from enum import Enum
from structures.emax import Emax


class TaskType(Enum):
    PERIODIC = 0
    SPORADIC = 1
    ARRIVAL_CURVE = 2


class Task:
    def __init__(self, id, deadline, task_type):
        self.task_type = task_type
        self.id = id
        self.deadline = deadline
        self.priority = None

    def __str__(self):
        task = f"(T{self.id}: deadline={self.deadline}, "
        if self.task_type == TaskType.PERIODIC:
            task += f"period={self.period}, WCET={self.wcet}"
        if self.task_type == TaskType.SPORADIC:
            task += f"min_interarrival={self.period}, WCET={self.wcet}"
        elif self.task_type == TaskType.ARRIVAL_CURVE:
            task += f"arr. curve with {len(self.arrival_curve.steps)} steps, WCET={self.wcet}"

        if self.priority is not None:
            task += f", priority={self.priority}"

        task += ")"

        return task

    __repr__ = __str__

    @staticmethod
    def task_with_period(id, deadline, period, wcet, is_sporadic):
        # Can be a periodic or sporadic task
        assert (
            period > 0 and wcet > 0
        ), "Period and worst-case execution time must be positive numbers."
        t = Task(id, deadline, TaskType.SPORADIC if is_sporadic else TaskType.PERIODIC)
        t.period = period
        t.arrival_curve = Emax(period, [(1, 1)])
        t.wcet = wcet
        return t

    @staticmethod
    def task_with_arrival_curve(id, deadline, arrival_curve, wcet):
        assert wcet > 0, "The worst-case execution time must be positive numbers."

        t = Task(id, deadline, TaskType.ARRIVAL_CURVE)
        t.arrival_curve = arrival_curve
        t.wcet = wcet
        return t

    def name(self):
        return "tsk%02d" % self.id

    def v_name(self):
        return f"{self.name()}.v"

    def vo_name(self):
        return f"{self.name()}.vo"

    def task_request_bound_function(self, dt):
        assert dt >= 0, "the interval dt must be non-negative"
        if dt == 0:
            return 0

        if self.task_type == TaskType.ARRIVAL_CURVE:
            return self.arrival_curve.at(dt) * self.wcet
        elif self.task_type in [TaskType.PERIODIC, TaskType.SPORADIC]:
            return int(math.ceil(dt / self.period)) * self.wcet
        else:
            raise NotImplementedError()

    def set_priority(self, priority):
        assert priority >= 0
        self.priority = priority

    def numerical_magnitude(self):
        if self.task_type == TaskType.ARRIVAL_CURVE:
            arrival = self.arrival_curve.h  # TODO implement other arrivals
            return (self.wcet + arrival + self.deadline) / 3
        elif self.task_type in [TaskType.PERIODIC, TaskType.SPORADIC]:
            return (self.wcet + self.period + self.deadline) / 3
        else:
            raise NotImplementedError()

    def utilization(self):
        if self.task_type == TaskType.ARRIVAL_CURVE:
            # Take the limit to infinity
            h = self.arrival_curve.h * 10 ^ 20
            return self.arrival_curve.at(h) * self.wcet / h
        elif self.task_type in [TaskType.PERIODIC, TaskType.SPORADIC]:
            return self.wcet / self.period
        else:
            raise NotImplementedError()
