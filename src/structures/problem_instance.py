from response_time_analysis import model

from structures import pg


class ProblemInstance:
    def __init__(self, scheduling_policy, preemption_model, task_set):
        assert scheduling_policy in pg.scheduling_policies
        assert preemption_model in pg.preemption_models
        assert task_set is not None
        ids = list(map(lambda t: t.id, task_set))
        assert len(set(ids)) == len(ids), "The task ids must be unique!"

        self.scheduling_policy = scheduling_policy
        self.preemption_model = preemption_model
        self.task_set = task_set

    def __str__(self):
        res = "\n------- Problem instance -------\n"
        res += f"scheduling policy: {self.scheduling_policy}\n"
        res += f"preemption model:  {self.preemption_model}\n"
        res += "Tasks:\n"
        for t in self.task_set:
            res += f"{str(t)}\n"
        res += "\n"
        return res

    __repr__ = __str__

    def total_utilization(self):
        return sum([task.utilization() for task in self.task_set])

    def to_rta_model(self) -> model.TaskSet:
        "Convert to the model representation expected by the response-time analysis library."
        return model.taskset(
            tsk.to_rta_model(preemption_model=self.preemption_model)
            for tsk in self.task_set
        )
