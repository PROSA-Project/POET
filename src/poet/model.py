from __future__ import annotations

# pyright: reportIncompatibleVariableOverride=false
from enum import StrEnum
from pathlib import Path
from typing import Self, override

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    model_validator,
)
from response_time_analysis import model as rta_model


class InputModel(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", validate_by_name=True)


class ArrivalCurve(InputModel):
    horizon: PositiveInt
    steps: list[tuple[PositiveInt, PositiveInt]] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_steps(self) -> Self:
        def strictly_monotonic(values: list[int]) -> bool:
            return all(a < b for a, b in zip(values, values[1:]))

        if not strictly_monotonic([s[0] for s in self.steps]):
            raise ValueError("arrival-curve steps must be strictly monotonic")
        if not strictly_monotonic([s[1] for s in self.steps]):
            raise ValueError("arrival-curve job counts must be strictly monotonic")
        if self.steps[0][0] != 1:
            raise ValueError("the first arrival-curve step must occur at 1")
        if self.steps[-1][0] >= self.horizon:
            raise ValueError("all steps must occur before the horizon")
        return self


class Task(InputModel):
    id: int
    wcet: PositiveInt = Field(alias="worst-case execution time")
    deadline: PositiveInt
    period: PositiveInt | None = None
    mit: PositiveInt | None = Field(default=None, alias="min interarrival", gt=0)
    arrival_curve: ArrivalCurve | None = Field(default=None)
    arrival_curve_spec: (
        tuple[PositiveInt, list[tuple[PositiveInt, PositiveInt]]] | None
    ) = Field(default=None, alias="arrival curve")
    priority: int | None = None

    @model_validator(mode="after")
    def _validate_arrival_model(self) -> Task:
        if self.arrival_curve_spec is not None:
            h = self.arrival_curve_spec[0]
            steps = self.arrival_curve_spec[1]
            self.arrival_curve = ArrivalCurve(horizon=h, steps=steps)

        arrival_fields = [
            self.period is not None,
            self.mit is not None,
            self.arrival_curve is not None,
        ]
        if sum(arrival_fields) != 1:
            raise ValueError(
                "exactly one of period, min interarrival, or arrival curve is required"
            )
        return self

    def name(self) -> str:
        return f"tsk{self.id:02d}"

    def v_name(self) -> str:
        return f"{self.name()}.v"

    def vo_name(self) -> str:
        return f"{self.name()}.vo"

    def numerical_magnitude(self) -> float:
        if self.period is not None:
            return (self.wcet + self.period + self.deadline) / 3
        elif self.mit is not None:
            return (self.wcet + self.mit + self.deadline) / 3
        elif self.arrival_curve is not None:
            h = self.arrival_curve.horizon
            return (self.wcet + h + self.deadline) / 3
        else:
            assert False

    def to_rta_model(self, preemption_model: PreemptionModel) -> rta_model.Task:
        "Convert to the model representation expected by the response-time analysis library."

        # currently limited to two preemption models
        assert preemption_model.is_fp() or preemption_model.is_np()

        dl = rta_model.Deadline(self.deadline)
        prio = rta_model.Priority(self.priority) if self.priority is not None else None
        if self.period is not None:
            arrival = rta_model.Periodic(self.period)
        elif self.mit is not None:
            arrival = rta_model.Sporadic(self.mit)
        elif self.arrival_curve is not None:
            arrival = rta_model.ArrivalCurvePrefix(
                horizon=self.arrival_curve.horizon, ac_steps=self.arrival_curve.steps
            )
        else:
            assert False  # unreachable
        wcet = rta_model.WCET(self.wcet)
        exec = (
            rta_model.FullyPreemptive(wcet)
            if preemption_model.is_fp()
            else rta_model.FullyNonPreemptive(wcet)
        )
        return rta_model.Task(arrival, exec, deadline=dl, priority=prio)

    @override
    def __hash__(self) -> int:
        return hash(self.id)

    def utilization(self) -> float:
        if self.period is not None:
            return self.wcet / self.period
        elif self.mit is not None:
            return self.wcet / self.mit
        elif self.arrival_curve is not None:
            return (
                self.arrival_curve.steps[-1][1] * self.wcet / self.arrival_curve.horizon
            )
        else:
            assert False  # unreachable


class SchedulingPolicy(StrEnum):
    FP = "FP"
    FIXED_PRIORITY = "fixed-priority"
    EDF = "EDF"
    EARLIEST_DEADLINE_FIRST = "earliest-deadline-first"

    def is_fp(self) -> bool:
        return self == SchedulingPolicy.FP or self == SchedulingPolicy.FIXED_PRIORITY

    def is_edf(self) -> bool:
        return (
            self == SchedulingPolicy.EDF
            or self == SchedulingPolicy.EARLIEST_DEADLINE_FIRST
        )


class PreemptionModel(StrEnum):
    FP = "FP"
    NP = "NP"
    FULLY_PREEMPTIVE = "fully-preemptive"
    NON_PREEMPTIVE = "non-preemptive"

    def is_fp(self) -> bool:
        return self == PreemptionModel.FP or self == PreemptionModel.FULLY_PREEMPTIVE

    def is_np(self) -> bool:
        return self == PreemptionModel.NP or self == PreemptionModel.NON_PREEMPTIVE


class Problem(InputModel):
    scheduling_policy: SchedulingPolicy = Field(alias="scheduling policy")
    preemption_model: PreemptionModel = Field(alias="preemption model")
    task_set: list[Task] = Field(alias="task set")

    @model_validator(mode="after")
    def _validate_problem_model(self) -> Problem:
        if not len(set((t.id for t in self.task_set))) == len(self.task_set):
            raise ValueError("task IDs must be unique")
        return self

    @staticmethod
    def from_yaml_file(path: str | Path) -> Problem:
        if not isinstance(path, Path):
            path = Path(path)
        data = yaml.safe_load(path.read_text())  # pyright: ignore[reportAny]
        if data is None:
            raise ValueError("input YAML file is empty")
        if not isinstance(data, dict):
            raise ValueError("input YAML file must contain a mapping at the root level")
        return Problem.model_validate(data)

    def total_utilization(self):
        return sum([t.utilization() for t in self.task_set])

    def to_rta_model(self) -> rta_model.TaskSet:
        "Convert to the model representation expected by the response-time analysis library."
        return rta_model.taskset(
            tsk.to_rta_model(preemption_model=self.preemption_model)
            for tsk in self.task_set
        )
