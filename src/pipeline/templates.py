import os
from structures import pg

TASK_SET_DECLARATION_FILE_NAME = "task_set"

# ********** Template files **********

TEMPLATES_MAIN_FOLDER = os.path.join(
    (os.path.dirname(os.path.realpath(__file__))), "..", "..", "templates"
)
TEMPLATES_CERTIFICATES_FOLDER = os.path.join(TEMPLATES_MAIN_FOLDER, "certificates")
TEMPLATE_MAIN_FP_EDF = os.path.join(TEMPLATES_CERTIFICATES_FOLDER, "fp_edf.v")
TEMPLATE_MAIN_NP_EDF = os.path.join(TEMPLATES_CERTIFICATES_FOLDER, "np_edf.v")
TEMPLATE_MAIN_FP_FP = os.path.join(TEMPLATES_CERTIFICATES_FOLDER, "fp_fp.v")
TEMPLATE_MAIN_NP_FP = os.path.join(TEMPLATES_CERTIFICATES_FOLDER, "np_fp.v")

# ********** Standard wildcards names **********

WC_TASK_SET_LIST = "$TASK_SET_LIST$"
WC_TASK_UNDER_ANALYSIS = "$TASK_UNDER_ANALYSIS$"
WC_TASK_UNDER_ANALYSIS_PERIOD = "$TASK_UNDER_ANALYSIS_PERIOD$"
WC_RESPONSE_TIME_BOUND = "$RESPONSE_TIME_BOUND$"
WC_MAX_BUSY_INTERVAL = "$MAX_BUSY_INTERVAL$"
WC_SEARCH_SPACE = "$SEARCH_SPACE$"
WC_SEARCH_SPACE_SIZE = "$SEARCH_SPACE_SIZE$"
WC_DEADLINE_IS_RESPECTED_START = "$DEADLINE_IS_RESPECTED_START$"
WC_DEADLINE_IS_RESPECTED_END = "$DEADLINE_IS_RESPECTED_END$"
WC_DEADLINE_IS_RESPECTED_PRINT_START = "$DEADLINE_IS_RESPECTED_PRINT_START$"
WC_DEADLINE_IS_RESPECTED_PRINT_END = "$DEADLINE_IS_RESPECTED_PRINT_END$"
WC_TARDINESS_IS_BOUNDED_START = "$TARDINESS_IS_BOUNDED_START$"
WC_TARDINESS_IS_BOUNDED_END = "$TARDINESS_IS_BOUNDED_END$"
WC_TARDINESS_IS_BOUNDED_PRINT_START = "$TARDINESS_IS_BOUNDED_PRINT_START$"
WC_TARDINESS_IS_BOUNDED_PRINT_END = "$TARDINESS_IS_BOUNDED_PRINT_END$"
WC_DECLARATION_START = "$DECLARATION_START$"
WC_CERTIFICATE_START = "$CERTIFICATE_START$"

WC_TARDINESS_BOUND_DECLARATION = "$TARDINESS_BOUND_DECLARATION$"
WC_TASK_SET_DECLARATION = "$TASK_SET_DECLARATION$"
WC_TASK_NAME = "$TASK_NAME$"
WC_TASK_ID = "$TASK_ID$"
WC_TASK_COST = "$TASK_COST$"
WC_TASK_DEADLINE = "$TASK_DEADLINE$"
WC_TASK_PRIORITY = "$TASK_PRIORITY$"
WC_TASK_PERIOD = "$TASK_PERIOD$"
WC_TASK_ARRIVAL = "$TASK_ARRIVAL$"

WC_F_SOLUTIONS = "$F_SOLUTIONS$"

WC_TASK_MAX_ARRIVALS_DECLARATION = "$TASK_MAX_ARRIVALS_DECLARATION$"
WC_TASK_MAX_ARRIVALS_IF = "$TASK_MAX_ARRIVALS_IF$"

WC_PROSA_PATH = "$PROSA_PATH$"

# **********************************************


def get_main_certificate(problem_instance):
    """
    Picks a template file, basing on the problem instance.
    Returns the entire file as a string.
    """
    pm = problem_instance.preemption_model
    sp = problem_instance.scheduling_policy

    if pm == pg.FULLY_PREEMPTIVE and sp == pg.FIXED_PRIORITY:
        template_file_path = TEMPLATE_MAIN_FP_FP
    elif pm == pg.FULLY_PREEMPTIVE and sp == pg.EARLIEST_DEADLINE_FIRST:
        template_file_path = TEMPLATE_MAIN_FP_EDF
    elif pm == pg.NON_PREEMPTIVE and sp == pg.FIXED_PRIORITY:
        template_file_path = TEMPLATE_MAIN_NP_FP
    elif pm == pg.NON_PREEMPTIVE and sp == pg.EARLIEST_DEADLINE_FIRST:
        template_file_path = TEMPLATE_MAIN_NP_EDF
    else:
        raise Exception(
            f"Invalid scheduling policy: {problem_instance.scheduling_policy}"
        )

    return open(template_file_path, "r").read()


def get_task_declaration(problem_instance):
    if problem_instance.scheduling_policy == pg.EARLIEST_DEADLINE_FIRST:
        return TEMPLATE_TASK_DECLARATION_NO_PRIORITY
    else:
        return TEMPLATE_TASK_DECLARATION_PRIORITY


########## Patches
TEMPLATE_TASK_DECLARATION_PRIORITY = """Definition $TASK_NAME$ := {| 
    id: $TASK_ID$ 
    cost: $TASK_COST$ 
    deadline: $TASK_DEADLINE$ 
    arrival: $TASK_ARRIVAL$ 
    priority: $TASK_PRIORITY$ }."""
TEMPLATE_TASK_DECLARATION_NO_PRIORITY = """Definition $TASK_NAME$ := {| 
    id: $TASK_ID$ 
    cost: $TASK_COST$ 
    deadline: $TASK_DEADLINE$ 
    arrival: $TASK_ARRIVAL$ }."""
