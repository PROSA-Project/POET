from rta import response_time_analysis
from structures.pg import FIXED_PRIORITY
from utils import utils


class TaskAnalysisResults:
    def __init__(self, L, search_space, search_space_solutions, R):
        self.L = L
        self.SS = search_space
        self.Fs = search_space_solutions
        self.R = R

    def __str__(self) -> str:
        exact_search_space = set(
            (point for point in utils.search_space(self.SS) if point < self.L)
        )
        return f"L: {self.L} | R: {self.R} | SS size: {utils.search_space_len(self.SS)} | exact size: {len(exact_search_space)}"


class AnalysisResults:
    def __init__(self, problem_instance):
        self.problem_instance = problem_instance

        rta = response_time_analysis.pick_rta(problem_instance)
        self.results = {t: self._analyze(rta, t) for t in problem_instance.task_set}

    def _analyze(self, rta, task):
        # Computes R for the given task.
        # L and R are -1 if they cannot be bounded.

        task_set = self.problem_instance.task_set
        assert task in task_set

        L = rta.max_busy_interval(task_set, task)
        if L <= 0:  # Infinite busy-interval, not schedulable
            return TaskAnalysisResults(L, [], [], -1)

        SS = rta.search_space(task_set, L, task)

        every_F_solved = True
        Fs = []

        if self.problem_instance.scheduling_policy == FIXED_PRIORITY:
            Fs = [rta.search_space_solution(task_set, task, A) for A in SS]
            if not all([F >= 0 for F in Fs]):
                every_F_solved = False
        else:  # EARLIEST_DEADLINE_FIRST
            for tsk_ss in SS:
                tsk_Fs = [rta.search_space_solution(task_set, task, A) for A in tsk_ss]
                if not all([F >= 0 for F in tsk_Fs]):
                    every_F_solved = False
                Fs += [tsk_Fs]

        R = rta.response_time(Fs, task) if every_F_solved else -1

        return TaskAnalysisResults(L, SS, Fs, R)

    def respose_time_is_bounded(self):
        ts = self.problem_instance.task_set
        return all([self.results[task].R > 0 for task in ts])

    def all_deadlines_respected(self):
        ts = self.problem_instance.task_set
        return all(
            [
                self.results[task].R > 0 and self.results[task].R <= task.deadline
                for task in ts
            ]
        )

    def __str__(self) -> str:
        s = "\n#### Analysis Results #### \n"
        for tsk in self.problem_instance.task_set:
            s += f"{tsk.name()} : {self.results[tsk]} \n"
        s += "##########################\n"

        return s
