"""
This module contains the specification of task and a task set.
"""

from enum import Enum

from response_time_analysis import model

from . import pg


class TaskType(Enum):
    PERIODIC = 0
    SPORADIC = 1
    ARRIVAL_CURVE = 2


class Emax:
    "Simple representation of an arrival-curve prefix."

    def __init__(self, horizon, steps):
        self.h = horizon
        self.steps = steps
        self.check_validity()

    def __str__(self) -> str:
        return f"[{self.h},{self.steps}]"

    __repr__ = __str__

    def check_validity(self):
        assert len(self.steps) > 0

        assert self.h > self.steps[-1][0], (
            "The horizon must be greater than the last step"
        )

        assert self.steps[0][1] > 0, "The arrival curve must not contain zeros"

        # If this condition does not hold, there is no hope for the prefix
        # to be subadditive, as you can take the (1,1) decomposition which has
        # value 0, so their sum is 0 as well
        assert self.steps[0][0] == 1, "A window of size 1 must be specified"

        # Checking strict monotonicity of steps
        assert all(
            self.steps[i][0] < self.steps[i + 1][0] for i in range(len(self.steps) - 1)
        ), "steps must be monotonic"
        assert all(
            self.steps[i][1] < self.steps[i + 1][1] for i in range(len(self.steps) - 1)
        ), "steps must be monotonic"


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

    def to_rta_model(self, preemption_model: str) -> model.Task:
        "Convert to the model representation expected by the response-time analysis library."

        # currently limited to two preemption models due to a lack of parameters for the others
        assert preemption_model in [pg.FULLY_PREEMPTIVE, pg.NON_PREEMPTIVE]

        dl = model.Deadline(self.deadline)
        prio = model.Priority(self.priority) if self.priority is not None else None
        arrival = model.ArrivalCurvePrefix(
            horizon=self.arrival_curve.h, ac_steps=self.arrival_curve.steps
        )
        wcet = model.WCET(self.wcet)
        exec = (
            model.FullyPreemptive(wcet)
            if preemption_model == pg.FULLY_PREEMPTIVE
            else model.FullyNonPreemptive(wcet)
        )
        return model.Task(arrival, exec, deadline=dl, priority=prio)

    @staticmethod
    def task_with_period(id, deadline, period, wcet, is_sporadic):
        # Can be a periodic or sporadic task
        assert period > 0 and wcet > 0, (
            "Period and worst-case execution time must be positive numbers."
        )
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
        return self.arrival_curve.steps[-1][1] * self.wcet / self.arrival_curve.h
