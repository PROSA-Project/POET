"""
This is the main module of the project.
"""
DOCKERFILE_TEMPLATE_PATH = "templates/docker_certificates/Dockerfile"
CERTIFICATE_CHECKER_PATH = "templates/docker_certificates/check_certificates.sh"
GENERATED_FILE_TYPES = [".sh",".v",".vo",".vok",".vos",".glob", ".aux"] # Used to delete old results on each run
SKIP_VERIFICATION = False

import os, shutil, subprocess, argparse, sys
from re import TEMPLATE
import stat
from pipeline import parser, coq_generator, templates
from utils import statistics, timing
from structures.analysis_results import AnalysisResults
from joblib import Parallel, delayed

def run_poet():
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer("total_poet_time")
    stopwatch.start_timer("total_time")

    ######################################
    # Reading input, basic checks
    ######################################
    opts = parse_args()
    
    input_path = opts.input
    verify_only_id = opts.id
    certificates_path = opts.output
    prosa_path = opts.prosa
    clean_output_folder = opts.clean
    delete_certificates = opts.delete
    save_stats = opts.stats
    bounded_tardiness_allowed = opts.bounded_tardiness
    test_schedulability = opts.test_schedulability
    repeat_declaration = opts.repeat_declaration
    no_check = opts.no_check
    jobs = int(opts.jobs)
    verify_without_dependencies = opts.verify_without_dependencies

    if certificates_path is None: 
        certificates_path = os.path.join(os.path.dirname(input_path), "certificates")

    stats_folder = os.path.dirname(input_path) if opts.output is None else opts.output

    check_condition(os.path.exists(input_path), "Input file not found")
    check_condition(os.path.exists(input_path) 
                    and os.path.isfile(input_path), 
                    f"File not found: {input_path}")

    ######################################
    # Parsing input file, performing RTA
    ######################################
    
    problem_instance = parser.parse_file(input_path)
    assert problem_instance is not None
    check_condition(verify_only_id is None 
                    or verify_only_id in [t.id for t in problem_instance.task_set], 
                    f"Task id {verify_only_id} was specified, but there is no task with such id.")


    analysis_results = AnalysisResults(problem_instance)

    if test_schedulability:
        print(analysis_results)
        if analysis_results.all_deadlines_respected():
            print(f"Task set is schedulable")
        elif analysis_results.respose_time_is_bounded():
            print(f"Task set is not schedulable, but response time is bound.")
        else:
            print(f"At least a response time is unbound.")
        sys.exit(0)

    if not bounded_tardiness_allowed:
        assert analysis_results.all_deadlines_respected(), "There is a deadline violation, unable to generate certificates"
    else:
        assert analysis_results.respose_time_is_bounded(), "At least a response time is unbound, unable to generate certificates"

    ######################################
    # Certificates generation
    ######################################

    # Create certificate folder
    if clean_output_folder:
        clean_certificates_folder(certificates_path)
    if not os.path.exists(certificates_path): 
        os.makedirs(certificates_path)

    external_declaration = None
    # Generate and write certificates
    for task in problem_instance.task_set:
        results = analysis_results.results[task]

        # Task
        proof, proof_declaration = coq_generator.generate_proof(problem_instance, task, results, bounded_tardiness_allowed, not repeat_declaration)

        # Checking that all the declarations match
        if external_declaration == None: external_declaration = proof_declaration
        else: assert proof_declaration == external_declaration

        certificate_path = os.path.join(certificates_path, task.name()+".v")
        save_certificate(certificate_path, proof)
    
    
    declaration_v_name = f"{templates.TASK_SET_DECLARATION_FILE_NAME}.v"
    if not repeat_declaration: # Save declaration
        certificate_path = os.path.join(certificates_path, declaration_v_name)
        save_certificate(certificate_path, external_declaration)

    stopwatch.pause_timer("total_poet_time")

    if no_check:
        sys.exit(0)

    ######################################
    # Coq compilation
    ######################################

    stopwatch.start_timer("total_coq_time")

    # Getting certificates to compile and checking that everything went well
    expected_v_files = [t.v_name() for t in problem_instance.task_set]
    if not repeat_declaration: expected_v_files = [declaration_v_name] + expected_v_files
    v_files = [f.name for f in os.scandir(certificates_path) if f.name.endswith(".v")]
    assert sorted(expected_v_files) == sorted(v_files)
    # Compiling certificates

    coq_results = []
    if not repeat_declaration: # declaration should be compiled first
        dec_time = compile_certificate(prosa_path, certificates_path, declaration_v_name, False)
        coq_results += [dec_time]

    if verify_only_id is None:
        # verify all tasks

        coq_results += Parallel(n_jobs=jobs)(delayed(compile_certificate)
                                            (prosa_path, certificates_path, v, not repeat_declaration) 
                                            for v in expected_v_files if v != declaration_v_name)
        coq_success = all([r > 0 for r in coq_results])
        
        for i in range(len(coq_results)): 
            stopwatch.set_time(f"{expected_v_files[i]}_coq_time", coq_results[i])
    else:
        # verify specific task only
        task_to_verify_vec = [t for t in problem_instance.task_set
                                         if t.id == verify_only_id]
        assert task_to_verify_vec and len(task_to_verify_vec) == 1
        task_to_verify = task_to_verify_vec[0]
        v = task_to_verify.v_name()
        time = compile_certificate(prosa_path, certificates_path, v, not repeat_declaration)
        coq_success = time > 0
        stopwatch.set_time(f"{v}_coq_time", time)

    stopwatch.pause_timer("total_coq_time")

    ######################################
    # Coqchk verification
    ######################################

    coqchk_success = False
    if coq_success:
        stopwatch.start_timer("total_coqchk_time")
        declaration_vo_name = f"{templates.TASK_SET_DECLARATION_FILE_NAME}.vo"

        if verify_only_id is None:
            # verify all tasks
            # Getting certificates to verify and checking that everything went well
            expected_vo_files = [t.vo_name() for t in problem_instance.task_set]
            if not repeat_declaration: expected_vo_files = [declaration_vo_name] + expected_vo_files
            vo_files = [f.name for f in os.scandir(certificates_path) if f.name.endswith(".vo")]
            assert sorted(expected_vo_files) == sorted(vo_files)

            # verifying certificates
            coqchk_results = Parallel(n_jobs=jobs)(delayed(verify_certificate)(prosa_path, certificates_path, vo, verify_without_dependencies) for vo in expected_vo_files)
            coqchk_success = all([r > 0 for r in coqchk_results])

            for i in range(len(coqchk_results)): 
                stopwatch.set_time(f"{expected_vo_files[i]}_coqchk_time", coqchk_results[i])
        else:
            # verify specific task only
            assert task_to_verify is not None 
            vo = task_to_verify.vo_name()
            time = verify_certificate(prosa_path, certificates_path, vo, verify_without_dependencies)
            coqchk_success = time > 0

            stopwatch.set_time(f"{vo}_coqchk_time", time)


        stopwatch.pause_timer("total_coqchk_time")
        stopwatch.pause_timer("total_time")

    ######################################
    # Statistics
    ######################################

    success = coq_success and coqchk_success
    # if success:
    stats = statistics.Statistics(problem_instance, analysis_results, stopwatch)

    ######################################
    # Saving stats and closing actions
    ######################################

    if delete_certificates:
        clean_certificates_folder(certificates_path, True)

    if success:
        print("Stats for: ", certificates_path)
        print(stats)
    else:
        if coq_success:
            print(f"ERROR: Could not verify certificates (path: {certificates_path})")
        else:
            print(f"ERROR: Could not compile certificates (path: {certificates_path})")
    
    if save_stats:
        name = "stats.yaml" if success else "stats_error.yaml"
        stats_path = os.path.join(stats_folder, name)
        stats.save(stats_path)

def parse_args():
    parser = argparse.ArgumentParser(description="The Proof Generation Tool")

    parser.add_argument('input', help='Input file.')

    parser.add_argument('-c', '--clean', default=False, action="store_true",
                        help='Empty the folder before generating new certificates.')

    parser.add_argument('-o', '--output', default=None, action='store',
                        help='Folder in which proofs will be generated.')

    parser.add_argument('-p', '--prosa', default=None, action='store',
                        help='Prosa root folder (when using a development version).')

    parser.add_argument('-j', '--jobs', default=1, action='store',
                        help='Maximum number of jobs while compiling and verifying.')

    parser.add_argument('-i', '--id', default=None, action='store', type=int,
                        help='Only performs formal verification on one task')

    parser.add_argument('-s', '--stats', default=False, action="store_true",
                        help='Output a YAML file containing the statistics of the task set')

    parser.add_argument('-d', '--delete', default=False, action="store_true",
                        help='Delete certificates after checking them')

    parser.add_argument('-b', '--bounded-tardiness', default=False, action="store_true",
                        help='Allow deadline violations (i.e., soft deadlines)')

    parser.add_argument('-t', '--test-schedulability', default=False, action="store_true",
                        help='Test if the task-set is schedulable (no certificate generation).')

    parser.add_argument('-r', '--repeat-declaration', default=False, action="store_true",
                        help='Repeat the task set declaration in every certificate.')

    parser.add_argument('-v', '--verify-without-dependencies', default=False, action="store_true",
                        help='Ignore the dependencies (Prosa, ssreflect, ...) while verifying.')

    parser.add_argument('-n', '--no-check', default=False, action="store_true",
                        help='Only generate but do not actually check the certificates.')

    return parser.parse_args()

def check_condition(condition, error_message):
    if not condition:
        print(error_message)
        sys.exit(1)

def clean_certificates_folder(certificates_path, delete_all = False):
    if not os.path.exists(certificates_path): return

    if delete_all:
        shutil.rmtree(certificates_path)
    else:
        for file in os.scandir(certificates_path):
            ext = os.path.splitext(file)[1]
            if ext in GENERATED_FILE_TYPES:
                os.unlink(file.path)

        remainining_files = len(os.listdir(certificates_path))  
        if remainining_files > 0:
            print(f"Certificates path is not empty: {remainining_files} files detected. Continuing anyway...")

def save_certificate(path, certificate):
    try:
        with open(path, "w") as f:
            f.write(certificate)
    except Exception as e:
        print("Error while saving certificate to '{path}'")
        print(e)

def compile_certificate(prosa_path, certificates_path, certificate, external_dec):
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer(f"coq_time")
    print(f"Compiling {certificate}...")
    cmd = ["coqc", "-w", "-notation-overriden,-parsing,-projection-no-head-constant", certificate]
    if prosa_path: 
	    cmd += ["-Q", prosa_path, "prosa"]
    
    return_code = subprocess.call(cmd, cwd=certificates_path)
    success = return_code == 0
    if not success: 
        print(f"Compilation of {certificate} ended with return code {return_code}")
    
    time = stopwatch.stop_timer(f"coq_time")
    return time if success else -1

def verify_certificate(prosa_path, certificates_path, certificate, verify_without_dependencies):  
    if SKIP_VERIFICATION : return 0
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer(f"coqchk_time")
    print(f"Verifying {certificate}...")
    cmd = ["coqchk", "-o", "-silent"]
    if prosa_path: 
	    cmd += ["-R", prosa_path, "prosa"]
    if verify_without_dependencies:
        cmd += ["-norec"]
    cmd += [certificate]
    
    return_code = subprocess.call(cmd, cwd=certificates_path) 
    success = return_code == 0
    if not success: 
        print(f"Verifying of {certificate} ended with return code {return_code}")
    
    time = stopwatch.stop_timer(f"coqchk_time")
    return time if success else -1

