from __future__ import annotations

from typing import cast, override

import yaml

from poet.analysis import AnalysisResults, TaskAnalysisResults
from poet.model import Problem, Task
from poet.utils import timing


class TaskStats(yaml.YAMLObject):
    yaml_tag: str = "!Task_stats"

    def __init__(
        self,
        task: Task,
        results: TaskAnalysisResults,
        stopwatch: timing.Stopwatch,
    ) -> None:
        # Task information
        self.name: str = task.name()
        self.utilization: float = task.utilization()
        self.numerical_magnitude: float = task.numerical_magnitude()
        self.L: int = results.L
        self.R: int = results.R
        self.search_space_size: int = len(results.SS)

        # Time stats
        self.coq_time: float | None = None
        self.coqchk_time: float | None = None
        if stopwatch.has_time(f"{task.v_name()}_coq_time"):
            self.coq_time = stopwatch.get_time(f"{task.v_name()}_coq_time")
        if stopwatch.has_time(f"{task.vo_name()}_coqchk_time"):
            self.coqchk_time = stopwatch.get_time(f"{task.vo_name()}_coqchk_time")

    @override
    def __str__(self) -> str:
        val = f"{self.name:<8} | R : {self.R} | L : {self.L} | SS: {self.search_space_size}"

        if self.coq_time is not None:
            val += f" | coq : {self.coq_time:2f}"
        if self.coqchk_time is not None:
            val += f" | coqchk : {self.coqchk_time:2f}"
        val += "\n"
        return val


class Statistics(yaml.YAMLObject):
    yaml_tag: str = "!POET_statistics"

    def __init__(
        self,
        problem_instance: Problem,
        analysis_results: AnalysisResults,
        stopwatch: timing.Stopwatch,
    ) -> None:
        # Task set information
        num_tasks = len(problem_instance.task_set)
        avg_magnitude = 0.0
        utilization = 0.0
        for task in problem_instance.task_set:
            avg_magnitude += task.numerical_magnitude()
            utilization += task.utilization()
        avg_magnitude /= num_tasks

        self.number_of_tasks: int = num_tasks
        self.total_utilization: float = utilization
        self.average_numerical_magnitude: float = avg_magnitude
        self.total_poet_time: float = stopwatch.get_time("total_poet_time")
        self.total_coq_time: float = stopwatch.get_time("total_coq_time")
        self.total_coqchk_time: float = (
            stopwatch.get_time("total_coqchk_time")
            if stopwatch.has_time("total_coqchk_time")
            else 0.0
        )
        self.total_time: float = stopwatch.get_time("total_time")

        self.task_stats: list[TaskStats] = [
            TaskStats(t, analysis_results.results[t], stopwatch)
            for t in problem_instance.task_set
        ]

    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                _ = f.write(yaml.dump(self))
        except Exception as e:
            print(f"Error while saving stats file '{path}'")
            print(e)

    @staticmethod
    def load(path: str) -> object | None:
        try:
            with open(path, "r") as f:
                return cast(object, yaml.load(f.read(), Loader=yaml.Loader))
        except Exception as e:
            print(f"Error while loading stats file in '{path}'")
            print(e)
        return None

    @override
    def __str__(self) -> str:
        other_time = (
            self.total_time
            - self.total_poet_time
            - self.total_coq_time
            - self.total_coqchk_time
        )
        out = "\n####### PROBLEM INSTANCE STATS #######\n"
        out += f"Number of tasks   : {self.number_of_tasks}\n"
        out += f"Task set util.    : {self.total_utilization:.2f}\n"
        out += f"Avg numerical mag : {self.average_numerical_magnitude:.0f}\n"
        out += "\n#######      TIME STATS       #######\n"
        out += f"Poet              : {self.total_poet_time:.2f} s\n"
        out += f"coq               : {self.total_coq_time:.2f} s\n"
        if self.total_coqchk_time:
            out += f"coqchk            : {self.total_coqchk_time:.2f} s\n"
        out += f"Other             : {other_time:.2f} s\n"
        out += f"Total             : {self.total_time:.2f} s\n"
        out += "\n#######     TASKS STATS       #######\n"
        for task in self.task_stats:
            out += str(task)

        return out
