from __future__ import annotations

from dataclasses import dataclass
from typing import override

from response_time_analysis import edf, fp
from response_time_analysis import model as rta_model
from response_time_analysis.analysis import Solution as RTASolution

from .model import Problem, SchedulingPolicy, Task


@dataclass
class AnalysisResults:
    problem: Problem
    results: dict[Task, TaskAnalysisResults]

    def respose_time_is_bounded(self) -> bool:
        return all(self.results[task].R > 0 for task in self.problem.task_set)

    def all_deadlines_respected(self) -> bool:
        return all(
            self.results[task].R > 0 and self.results[task].R <= task.deadline
            for task in self.problem.task_set
        )


@dataclass
class TaskAnalysisResults:
    rta_solution: RTASolution
    L: int
    SS: list[int]
    Fs: list[int]
    R: int

    @override
    def __str__(self) -> str:
        exact_search_space = set((point for point in self.SS if point < self.L))
        return f"L: {self.L} | R: {self.R} | SS size: {len(self.SS)} | exact size: {len(exact_search_space)}"


def analyze_task_set(problem: Problem) -> AnalysisResults:
    task_set_for_rta = problem.to_rta_model().with_arrival_curves()
    return AnalysisResults(
        problem,
        {
            t: analyze(problem.scheduling_policy, task_set_for_rta, tsk)
            for tsk, t in zip(task_set_for_rta, problem.task_set)
        },
    )


THREE_YEARS_IN_NANOSECONDS = 10**17


def analyze(
    scheduling_policy: SchedulingPolicy,
    all_tasks: rta_model.TaskSet,
    task_under_analysis: rta_model.Task,
    horizon: int = THREE_YEARS_IN_NANOSECONDS,
):
    # Computes R for the given task.
    # L and R are -1 if they cannot be bounded.

    # run the RTA
    if scheduling_policy.is_fp():
        sol = fp.rta(
            all_tasks,
            task_under_analysis,
            rta_model.IdealProcessor(),
            use_poet_search_space=True,
            horizon=horizon,
        )
    elif scheduling_policy.is_edf():
        sol = edf.rta(
            all_tasks,
            task_under_analysis,
            rta_model.IdealProcessor(),
            use_poet_search_space=True,
            horizon=THREE_YEARS_IN_NANOSECONDS,
        )
    else:
        assert False, "support for policies other than FP and EDF not yet implemented"

    if sol.busy_window_bound is None or sol.search_space is None:
        # Infinite busy-interval, not schedulable
        return TaskAnalysisResults(sol, -1, [], [], -1)

    SS = [A for (A, _F, _R) in sol.search_space]
    Fs: list[int] = [max(0, (F or 0) - A) for (A, F, _R) in sol.search_space]
    R = sol.response_time_bound if sol.response_time_bound is not None else -1

    return TaskAnalysisResults(sol, sol.busy_window_bound, SS, Fs, R)
