import yaml
from utils import utils

class TaskStats(yaml.YAMLObject):
    yaml_tag = "!Task_stats"
    def __init__(self, task, results, stopwatch):
        # Task information
        self.name = task.name()
        self.utilization = task.utilization()
        self.numerical_magnitude = task.numerical_magnitude()
        self.L = results.L
        self.R = results.R
        self.search_space_size = utils.search_space_len(results.SS)

        # Time stats
        if stopwatch.has_time(f"{task.v_name()}_coq_time"):
            self.coq_time = stopwatch.get_time(f"{task.v_name()}_coq_time")
        if stopwatch.has_time(f"{task.vo_name()}_coqchk_time"):
            self.coqchk_time = stopwatch.get_time(f"{task.vo_name()}_coqchk_time")
    
    def __str__(self):
        val = f"{self.name:<8} | R : {self.R} | L : {self.L} | SS: {self.search_space_size}"
        
        if hasattr(self, 'coq_time'):
            val += f" | coq : {self.coq_time:2f}"
        if hasattr(self, 'coqchk_time'):
            val += f" | coqchk : {self.coqchk_time:2f}"
        val += "\n"
        return val
        
class Statistics(yaml.YAMLObject):
    yaml_tag = "!POET_statistics"
    def __init__(self, problem_instance, analysis_results, stopwatch):
        # Task set information
        num_tasks = len(problem_instance.task_set)
        avg_magnitude = 0
        utilization = 0
        for task in problem_instance.task_set:
            avg_magnitude += task.numerical_magnitude()
            utilization += task.utilization()
        avg_magnitude /= num_tasks

        self.number_of_tasks = num_tasks
        self.total_utilization = utilization
        self.average_numerical_magnitude = avg_magnitude
        self.total_poet_time = stopwatch.get_time("total_poet_time")
        self.total_coq_time = stopwatch.get_time("total_coq_time")
        if stopwatch.has_time(f"total_coqchk_time"):
            self.total_coqchk_time = stopwatch.get_time("total_coqchk_time")
        self.total_time = stopwatch.get_time("total_time")
        
        self.task_stats = [TaskStats(t, analysis_results.results[t], stopwatch) 
                           for t in problem_instance.task_set]
    
    def save(self, path):
        try:
            with open(path, "w") as f:
                f.write(yaml.dump(self))
        except Exception as e:
            print("Error while saving stats file '{path}'")
            print(e)
    
    @staticmethod
    def load(path):
        try:
            with open(path, "r") as f:
                return yaml.load(f.read(), Loader=yaml.Loader)
        except Exception as e:
            print("Error while loading stats file in '{path}'")
            print(e)

    def __str__(self):
        other_time = self.total_time - self.total_poet_time - self.total_coq_time - self.total_coqchk_time
        out = "\n####### PROBLEM INSTANCE STATS #######\n"
        out += f"Number of tasks   : {self.number_of_tasks}\n"
        out += f"Task set util.    : {self.total_utilization:.2f}\n"
        out += f"Avg numerical mag : {self.average_numerical_magnitude:.0f}\n"
        out += "\n#######      TIME STATS       #######\n"
        out += f"Poet              : {self.total_poet_time:.2f} s\n"
        out += f"coq               : {self.total_coq_time:.2f} s\n"
        if hasattr(self, 'total_coqchk_time'):
            out += f"coqchk            : {self.total_coqchk_time:.2f} s\n"
        out += f"Other             : {other_time:.2f} s\n"
        out += f"Total             : {self.total_time:.2f} s\n"
        out += "\n#######     TASKS STATS       #######\n"
        for task in self.task_stats:
            out += str(task)

        return out