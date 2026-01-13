from response_time_analysis import edf, fp, model

from . import pg


class TaskAnalysisResults:
    def __init__(self, rta_solution, L, search_space, search_space_solutions, R):
        self.rta_solution = rta_solution
        self.L = L
        self.SS = search_space
        self.Fs = search_space_solutions
        self.R = R

    def __str__(self) -> str:
        exact_search_space = set((point for point in self.SS if point < self.L))
        return f"L: {self.L} | R: {self.R} | SS size: {len(self.SS)} | exact size: {len(exact_search_space)}"


THREE_YEARS_IN_NANOSECONDS = 10**17


def analyze(scheduling_policy, all_tasks, task_under_analysis):
    # Computes R for the given task.
    # L and R are -1 if they cannot be bounded.

    # run the RTA
    if scheduling_policy == pg.FIXED_PRIORITY:
        sol = fp.rta(
            all_tasks,
            task_under_analysis,
            model.IdealProcessor(),
            use_poet_search_space=True,
            horizon=THREE_YEARS_IN_NANOSECONDS,
        )
    elif scheduling_policy == pg.EARLIEST_DEADLINE_FIRST:
        sol = edf.rta(
            all_tasks,
            task_under_analysis,
            model.IdealProcessor(),
            use_poet_search_space=True,
            horizon=THREE_YEARS_IN_NANOSECONDS,
        )
    else:
        assert False, "support for policies other than FP and EDF missing"

    if sol.busy_window_bound is None or sol.search_space is None:
        # Infinite busy-interval, not schedulable
        return TaskAnalysisResults(-1, [], [], -1)

    SS = [A for (A, _F, _R) in sol.search_space]
    Fs = [max(0, F - A) for (A, F, _R) in sol.search_space]
    R = sol.response_time_bound if sol.bound_found() else -1

    return TaskAnalysisResults(sol, sol.busy_window_bound, SS, Fs, R)


class AnalysisResults:
    def __init__(self, problem_instance):
        self.problem_instance = problem_instance
        task_set_for_rta = self.problem_instance.to_rta_model()
        self.results = {
            t: analyze(problem_instance.scheduling_policy, task_set_for_rta, tsk)
            for tsk, t in zip(task_set_for_rta, problem_instance.task_set)
        }

    def respose_time_is_bounded(self):
        ts = self.problem_instance.task_set
        return all(self.results[task].R > 0 for task in ts)

    def all_deadlines_respected(self):
        ts = self.problem_instance.task_set
        return all(
            self.results[task].R > 0 and self.results[task].R <= task.deadline
            for task in ts
        )

    def __str__(self) -> str:
        s = "\n#### Analysis Results #### \n"
        for tsk in self.problem_instance.task_set:
            s += f"{tsk.name()} : {self.results[tsk]} \n"
        s += "##########################\n"

        return s
