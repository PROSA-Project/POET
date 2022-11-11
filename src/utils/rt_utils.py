import traceback

"""
This module contains utility functions that regard real-time theory.
"""

def arrival_curve_to_rbf (curve, wcet):
# Transforms a given arrival curve + WCET into a RBF.
    return list(map (lambda x, wcet=wcet: (x[0], x[1]*wcet), curve))

def delta_min_to_arrival_curve (delta_min):
    raise NotImplementedError() #TODO implement

def check_valid_curve (curve):
# Assumes a well-formed curve (i.e. list of integer tuples). 
# Checks that the curve is strictly monotonic and starts from zero.
    prev = curve[0]
    if prev[0] == 0: 
        assert prev[1] == 0, f"{prev} : A window of zero must have zero generated workload."
    for elem in curve[1:]:
        if prev is not None:
            assert prev[0] < elem[0], f"{prev} - {elem} : The arrival times of the curve must be strictly monotonic."
            assert prev[0] < elem[0], f"{prev} - {elem} : The workload of the curve must increase at any point."
        prev = elem

def check_valid_delta_min (delta_min):
    assert isinstance(delta_min, list) and len(delta_min) > 0, "Min distance must be non-empty lists"

    #TODO do more checks (content of list, superadditivity)

debug = False
def compute_fixpoint (function, start, hard_limit=None):

    if hard_limit == None:
        hard_limit = 10**30 # No way this will ever be surpassed

    try: # Could overflow :(
        if debug: 
            print(f"Computing fixpoint of {function}")

        t = None
        tn = start
        while t != tn:
            t = tn
            tn = function(t)

            if debug:
                print(f"t: {t}")
                print(f"tn: {tn}")
            if hard_limit < t:
                print("Hard limit for the fixpoint computation reached.")
                return -1
    except:
        print("Computing fixpoint error.")
        traceback.print_exc()
        return -1

    return t
