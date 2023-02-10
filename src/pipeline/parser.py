""" 
This module handles the parsing of the specification file.

Basic specification errors (type checking, absence of information)
are handled here, but specific validity checks (e.g. RBF monotone)
are left to other modules. 
"""

import yaml
import traceback
from structures import pg
from structures.task import Task
from structures.emax import Emax
from structures.problem_instance import ProblemInstance
from utils import utils

DEBUG_PARSER = True  # If true, prints tracebacks

# ********** Standard tag names **********

SCHEDULING_POLICY_TAG = "scheduling policy"
PREEMPTION_MODEL_TAG = "preemption model"

TASK_SET_TAG = "task set"
TASK_ID_TAG = "id"
TASK_WCET_TAG = "worst-case execution time"
TASK_DEADLINE_TAG = "deadline"

TASK_PERIOD_TAG = "period"
TASK_MIN_INTERARRIVAL_TAG = "min interarrival"
TASK_PRIORITY_TAG = "priority"
TASK_ARRIVAL_CURVE_TAG = "arrival curve"
task_request_models = [
    TASK_PERIOD_TAG,
    TASK_MIN_INTERARRIVAL_TAG,
    TASK_PRIORITY_TAG,
    TASK_ARRIVAL_CURVE_TAG,
]

allowed_tags_at_root_level = [SCHEDULING_POLICY_TAG, PREEMPTION_MODEL_TAG, TASK_SET_TAG]
allowed_tags_at_task_level = [
    TASK_ID_TAG,
    TASK_WCET_TAG,
    TASK_DEADLINE_TAG,
] + task_request_models

# ****************************************

parser_status = ""  # Used to print meaningful error messages


def parse_file(file):
    # Parses the given file according to the PG specifications.
    global parser_status
    parser_status = "opening the file"

    try:
        with open(file, "r") as stream:
            root = yaml.safe_load(stream)

            parser_status = "parsing the root file"
            check_for_allowed_tags(root, allowed_tags_at_root_level)
            scheduling_policy = parse_alternatives(
                root, SCHEDULING_POLICY_TAG, pg.scheduling_policies
            )
            scheduling_policy = pg.process_synonyms(scheduling_policy)
            preemption_model = parse_alternatives(
                root, PREEMPTION_MODEL_TAG, pg.preemption_models
            )
            preemption_model = pg.process_synonyms(preemption_model)
            task_set_object = parse_required(root, TASK_SET_TAG)

            parser_status = "parsing the task set information"
            expect_priority = scheduling_policy == pg.FIXED_PRIORITY
            parse_fun = lambda t: parse_task(t, expect_priority)
            task_set = list(map(parse_fun, task_set_object))

            parser_status = "finishing the task set creation"
            return ProblemInstance(scheduling_policy, preemption_model, task_set)

    except Exception as e:
        print(f"\nError while {parser_status}:")
        print(e)
        if DEBUG_PARSER:
            print(traceback.format_exc())


def check_for_allowed_tags(father, allowed_tags):
    # Checks that the tag of every object contained in `father` is
    # contained in the allowed-objects list.
    for key, _ in father.items():
        assert (
            key in allowed_tags
        ), f"'{key}' is an unrecognized tag. Allowed tags are: {utils.pretty_list(allowed_tags)}."


def parse_required(father, tag):
    # Given a father dictionary, fetches the given tag object.
    # Raises errors if the object is not present, or if it's empty.
    assert tag in father, f"The information is required: {tag}."
    value = father[tag]
    assert value is not None, f"The information cannot be empty: {tag}."
    return father[tag]


def parse_alternatives(father, tag, admitted_values):
    # Parses the value of a given tag in a given iterable father dictionary.
    # Checks and raises exceptions if the tag is missing, or if its value is
    # not one of the valid alternatives.
    value = parse_required(father, tag)

    if value not in admitted_values:
        raise Exception(
            f"'{tag}' has value '{value}', which is not valid.\nUse one of these: {utils.pretty_list(admitted_values)}."
        )
    else:
        return value


def parse_positive_number(father, tag):
    # Parses the value of a given tag in a given iterable father dictionary.
    # Checks and raises exceptions if the tag is missing, or if its value is
    # not a positive number.
    value = parse_required(father, tag)

    try:
        return int(value)
    except:
        raise Exception(f"'{tag}' has value '{value}', which is not a positive number.")


def parse_arrival_curve(father, curve_tag):
    # Given a father dictionary and a curve tag name, parses an arrival curve
    def parse_tuple(tuple):
        assert isinstance(
            tuple, list
        ), "Each element of the curve must be a tuple of positive integers"
        assert len(tuple) == 2, "Each tuple in a curve must contain two elements."
        try:
            time = int(tuple[0])
            amount = int(tuple[1])
            assert time >= 0
            assert amount >= 0
        except:
            raise Exception(
                "Each tuple in a curve must only contain positive integers."
            )

        return (time, amount)

    curve = parse_required(father, curve_tag)

    assert (
        isinstance(curve, list) and len(curve) == 2
    ), "Curves must be of the form (h, [(t1,d1)] )."
    horizon = curve[0]
    steps = curve[1]

    assert isinstance(horizon, int), "Curves must be of the form (h, [(t1,d1)] )."
    assert (
        isinstance(curve, list) and len(curve) > 0
    ), "Curves must be of the form (h, [(t1,d1)] )."

    steps = list(map(parse_tuple, steps))
    return Emax(horizon, steps)


def parse_task(task, expect_priority):
    # Given a dictionary, it parses a task.
    # A valid task needs to be specified in one of these forms:
    # 1) id, deadline, period, WCET
    # 2) id, deadline, arrival curve, WCET
    global parser_status
    parser_status = "parsing a task"

    assert task is not None, "the task cannot be empty."
    id = parse_positive_number(task, TASK_ID_TAG)
    parser_status = f"parsing a task with id {id}"
    deadline = parse_positive_number(task, TASK_DEADLINE_TAG)

    check_for_allowed_tags(task, allowed_tags_at_task_level)

    has_period = TASK_PERIOD_TAG in task
    has_min_interarrival = TASK_MIN_INTERARRIVAL_TAG in task
    has_priority = TASK_PRIORITY_TAG in task
    has_arrival_curve = TASK_ARRIVAL_CURVE_TAG in task
    has_wcet = TASK_WCET_TAG in task

    assert (
        has_period + has_min_interarrival + has_arrival_curve == 1
    ), f"One of these should be specified: {utils.pretty_list(task_request_models)}."

    yes_no = " " if expect_priority else " not "
    assert (
        has_priority == expect_priority
    ), f"You should{yes_no}provide a priority for task with id {id}"

    if has_period or has_min_interarrival:
        assert (
            has_wcet
        ), "If a period or min interarrival is specified, a worst-case execution time is needed."

        period = parse_positive_number(
            task, TASK_PERIOD_TAG if has_period else TASK_MIN_INTERARRIVAL_TAG
        )
        wcet = parse_positive_number(task, TASK_WCET_TAG)
        t = Task.task_with_period(id, deadline, period, wcet, has_min_interarrival)
    elif has_arrival_curve:
        assert (
            has_wcet
        ), "If an arrival curve is specified, a worst-case execution time or a request-bound function is needed."

        arrival_curve = parse_arrival_curve(task, TASK_ARRIVAL_CURVE_TAG)
        wcet = parse_positive_number(task, TASK_WCET_TAG)
        t = Task.task_with_arrival_curve(id, deadline, arrival_curve, wcet)

    if has_priority:
        t.set_priority(parse_positive_number(task, TASK_PRIORITY_TAG))

    return t
