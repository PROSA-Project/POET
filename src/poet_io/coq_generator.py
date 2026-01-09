"""
This module handles the generation of the Coq proof file.
"""

from posixpath import split

from poet_io import templates
from structures import pg
from structures.task import TaskType
from utils.utils import conditional_cut_patch, patch


def generate_proof(
    problem_instance, tsk, results, bounded_tardiness_allowed, split_declaration
):
    ts = problem_instance.task_set
    proof = templates.get_main_certificate(problem_instance)
    proof = patch(
        proof, templates.WC_TASK_SET_DECLARATION, task_set_declaration(problem_instance)
    )
    proof = patch(proof, templates.WC_TASK_SET_LIST, task_set_list(ts))
    proof = patch(proof, templates.WC_TASK_UNDER_ANALYSIS, tsk.name())
    proof = patch(proof, templates.WC_MAX_BUSY_INTERVAL, f"{results.L}%N")
    proof = patch(proof, templates.WC_RESPONSE_TIME_BOUND, f"{results.R}%N")
    proof = patch(proof, templates.WC_SEARCH_SPACE, coq_list(results.SS))
    proof = patch(proof, templates.WC_SEARCH_SPACE_SIZE, len(results.SS))
    proof = patch(
        proof, templates.WC_F_SOLUTIONS, get_F_solutions(problem_instance, results.Fs)
    )

    use_tardiness_bound = bounded_tardiness_allowed and tsk.deadline < results.R
    if use_tardiness_bound:
        tbdec = f"Definition B := {results.R - tsk.deadline}%N\n."
    else:
        tbdec = ""
    proof = patch(proof, templates.WC_TARDINESS_BOUND_DECLARATION, tbdec)
    proof, _ = conditional_cut_patch(
        proof,
        templates.WC_DEADLINE_IS_RESPECTED_START,
        templates.WC_DEADLINE_IS_RESPECTED_END,
        use_tardiness_bound,
    )
    proof, _ = conditional_cut_patch(
        proof,
        templates.WC_TARDINESS_IS_BOUNDED_START,
        templates.WC_TARDINESS_IS_BOUNDED_END,
        not use_tardiness_bound,
    )
    proof, _ = conditional_cut_patch(
        proof,
        templates.WC_DEADLINE_IS_RESPECTED_PRINT_START,
        templates.WC_DEADLINE_IS_RESPECTED_PRINT_END,
        use_tardiness_bound,
    )
    proof, _ = conditional_cut_patch(
        proof,
        templates.WC_TARDINESS_IS_BOUNDED_PRINT_START,
        templates.WC_TARDINESS_IS_BOUNDED_PRINT_END,
        not use_tardiness_bound,
    )

    proof, declaration = conditional_cut_patch(
        proof,
        templates.WC_DECLARATION_START,
        templates.WC_CERTIFICATE_START,
        split_declaration,
    )
    if split_declaration:
        proof = f"Require Import {templates.TASK_SET_DECLARATION_FILE_NAME}.\n" + proof

    return proof, declaration


def get_F_solutions(problem_instance, Fs):
    dec = ""
    if problem_instance.scheduling_policy == pg.FIXED_PRIORITY:
        fs_list = coq_list(Fs)
        dec += f"Let Fs : seq N := {fs_list}%N.\n"
    else:  # EARLIEST_DEADLINE_FIRST
        Fs_merged = [F for Fs_task in Fs for F in Fs_task]
        fs_list = coq_list(Fs_merged)
        dec += f"Let Fs : seq N := {fs_list}%N.\n"

    return dec[:-1]


def task_set_declaration(problem_instance):
    # Generates Coq records from the given task set.
    # Syntax: `Let tsk1 := {| task_id := 1; task_deadline := 3; ... |}.`
    def task_declaration(t):
        task_dec = templates.get_task_declaration(problem_instance, t)
        task_dec = patch(task_dec, templates.WC_TASK_NAME, t.name())
        task_dec = patch(task_dec, templates.WC_TASK_ID, f"{t.id}")
        task_dec = patch(task_dec, templates.WC_TASK_COST, f"{t.wcet}")
        task_dec = patch(task_dec, templates.WC_TASK_DEADLINE, f"{t.deadline}")

        if problem_instance.scheduling_policy == pg.FIXED_PRIORITY:
            assert t.priority is not None
            task_dec = patch(task_dec, templates.WC_TASK_PRIORITY, f"{t.priority}")

        if t.task_type in [TaskType.PERIODIC, TaskType.SPORADIC]:
            task_dec = patch(task_dec, templates.WC_TASK_ARRIVAL, f"{t.period}")
        elif t.task_type == TaskType.ARRIVAL_CURVE:
            curve = templates.TEMPLATE_CURVE
            curve = patch(curve, templates.WC_CURVE_HORIZON, f"{t.arrival_curve.h}")
            curve = patch(
                curve, templates.WC_CURVE_STEPS, f"{coq_list(t.arrival_curve.steps)}"
            )
            task_dec = patch(task_dec, templates.WC_TASK_ARRIVAL, curve)
        else:
            assert False
        return task_dec

    task_declarations = [task_declaration(t) for t in problem_instance.task_set]
    return "\n".join(task_declarations)


def coq_list(list):
    # Generates a Coq list declaration from the given list.
    # Syntax: `[:: el1; el2; ...]`.
    xs = "[:: " + "; ".join(map(str, list)) + "]"
    return xs


def emax_declaration(emax):
    dec = f"ArrivalPrefix_T ({emax.h}, "
    dec += coq_list(emax.steps) + ") %N"
    return dec


def task_set_list(task_set):
    # Generates a Coq list from the given task set.
    # Syntax: `[:: tsk1; tsk2; ...]`.
    return coq_list([t.name() for t in task_set])
