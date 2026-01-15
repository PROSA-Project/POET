"""
This is the main module of the project.
"""

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

from joblib import Parallel, delayed
from pydantic import ValidationError

from poet.analysis import AnalysisResults, analyze_task_set
from poet.certificates import coq_generator, templates
from poet.model import Problem, Task
from poet.utils import statistics, timing

DOCKERFILE_TEMPLATE_PATH = "templates/docker_certificates/Dockerfile"
CERTIFICATE_CHECKER_PATH = "templates/docker_certificates/check_certificates.sh"
GENERATED_FILE_TYPES = [
    ".sh",
    ".v",
    ".vo",
    ".vok",
    ".vos",
    ".glob",
    ".aux",
]  # Used to delete old results on each run


@dataclass(frozen=True)
class CoqCompileResult:
    success: bool
    task_to_verify: Task | None
    expected_v_files: list[str]
    declaration_v_name: str


class POETArgs(argparse.Namespace):
    input_path: str = ""
    verify_only_id: int | None = None
    output_path: str | None = None
    prosa_path: str | None = None
    clean_output_folder: bool = False
    delete_certificates: bool = False
    save_stats: bool = False
    bounded_tardiness_allowed: bool = False
    test_schedulability: bool = False
    repeat_declaration: bool = False
    no_check: bool = False
    jobs: int = 1
    verify_without_dependencies: bool = False


def run_poet() -> None:
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer("total_poet_time")
    stopwatch.start_timer("total_time")

    ######################################
    # Reading input, basic checks
    ######################################
    opts = parse_args()
    certificates_path, stats_folder = resolve_paths(opts)

    validate_input_path(opts)

    ######################################
    # Parsing input file, performing RTA
    ######################################

    problem_instance = load_problem(opts)
    analysis_results = analyze_task_set(problem_instance)
    check_schedulability(problem_instance, analysis_results, opts)

    ######################################
    # Certificates generation
    ######################################

    prepare_certificates_folder(certificates_path, opts)
    declaration_v_name = generate_certificates(
        problem_instance,
        analysis_results,
        certificates_path,
        opts,
    )

    _ = stopwatch.pause_timer("total_poet_time")

    if opts.no_check:
        sys.exit(0)

    ######################################
    # Coq compilation
    ######################################

    stopwatch.start_timer("total_coq_time")

    compile_result = compile_certificates(
        problem_instance,
        certificates_path,
        opts,
        stopwatch,
        declaration_v_name,
    )

    _ = stopwatch.pause_timer("total_coq_time")

    ######################################
    # Coqchk verification
    ######################################

    coqchk_success = False
    if compile_result.success:
        stopwatch.start_timer("total_coqchk_time")
        coqchk_success = verify_certificates(
            problem_instance,
            certificates_path,
            compile_result.task_to_verify,
            opts,
            stopwatch,
        )

        _ = stopwatch.pause_timer("total_coqchk_time")
        _ = stopwatch.pause_timer("total_time")

    ######################################
    # Statistics
    ######################################

    stats = statistics.Statistics(problem_instance, analysis_results, stopwatch)

    ######################################
    # Saving stats and closing actions
    ######################################

    finalize_run(
        certificates_path,
        stats_folder,
        stats,
        compile_result.success,
        compile_result.success and coqchk_success,
        opts,
    )


def resolve_paths(opts: POETArgs) -> tuple[str, str]:
    certificates_path = (
        os.path.join(os.path.dirname(opts.input_path), "certificates")
        if opts.output_path is None
        else opts.output_path
    )
    stats_folder = (
        os.path.dirname(opts.input_path)
        if opts.output_path is None
        else opts.output_path
    )
    return certificates_path, stats_folder


def validate_input_path(opts: POETArgs) -> None:
    ensure(os.path.exists(opts.input_path), "Input file not found")
    ensure(
        os.path.exists(opts.input_path) and os.path.isfile(opts.input_path),
        f"File not found: {opts.input_path}",
    )


def load_problem(opts: POETArgs) -> Problem:
    try:
        problem_instance = Problem.from_yaml_file(opts.input_path)
    except ValidationError as err:
        print("Failed to parse input:")
        for e in err.errors(include_url=False, include_input=True):
            print(f"- [{'.'.join(str(x) for x in e['loc'])}] {e['msg']}")
        sys.exit(80)
    ensure(
        opts.verify_only_id is None
        or opts.verify_only_id in [t.id for t in problem_instance.task_set],
        f"Task id {opts.verify_only_id} was specified, but there is no task with such id.",
    )
    return problem_instance


def check_schedulability(
    problem_instance: Problem,
    analysis_results: AnalysisResults,
    opts: POETArgs,
) -> None:
    if opts.test_schedulability:
        print(analysis_results)
        if analysis_results.all_deadlines_respected():
            print("Task set is schedulable")
        elif analysis_results.respose_time_is_bounded():
            print(
                "Task set is not schedulable (deadlines may be missed),",
                "but response times are bounded.",
            )
        else:
            print("At least one task has an unbounded response time.")
        sys.exit(0)

    if (
        not opts.bounded_tardiness_allowed
        and not analysis_results.all_deadlines_respected()
    ):
        print("There is a deadline violation; unable to generate certificates.")
        sys.exit(1)
    if (
        opts.bounded_tardiness_allowed
        and not analysis_results.respose_time_is_bounded()
    ):
        print(
            "At least one response time is unbounded; unable to generate certificates.",
            f"\nTotal utilization: {problem_instance.total_utilization() * 100:.2f}%",
        )
        for t in problem_instance.task_set:
            print(f"- Task {t.id}: {t.utilization() * 100:.2f}%")
        sys.exit(1)


def prepare_certificates_folder(certificates_path: str, opts: POETArgs) -> None:
    if opts.clean_output_folder:
        clean_certificates_folder(certificates_path)
    if not os.path.exists(certificates_path):
        os.makedirs(certificates_path)


def generate_certificates(
    problem_instance: Problem,
    analysis_results: AnalysisResults,
    certificates_path: str,
    opts: POETArgs,
) -> str:
    external_declaration: str | None = None
    for task in problem_instance.task_set:
        results = analysis_results.results[task]
        proof, proof_declaration = coq_generator.generate_proof(
            problem_instance,
            task,
            results,
            opts.bounded_tardiness_allowed,
            not opts.repeat_declaration,
        )
        if external_declaration is None:
            external_declaration = proof_declaration
        else:
            assert proof_declaration == external_declaration

        certificate_path = os.path.join(certificates_path, task.name() + ".v")
        save_certificate(certificate_path, proof)

    declaration_v_name = f"{templates.TASK_SET_DECLARATION_FILE_NAME}.v"
    if not opts.repeat_declaration:  # Save declaration
        assert external_declaration is not None
        certificate_path = os.path.join(certificates_path, declaration_v_name)
        save_certificate(certificate_path, external_declaration)
    return declaration_v_name


def compile_certificates(
    problem_instance: Problem,
    certificates_path: str,
    opts: POETArgs,
    stopwatch: timing.Stopwatch,
    declaration_v_name: str,
) -> CoqCompileResult:
    expected_v_files = [t.v_name() for t in problem_instance.task_set]
    if not opts.repeat_declaration:
        expected_v_files = [declaration_v_name] + expected_v_files
    v_files = [f.name for f in os.scandir(certificates_path) if f.name.endswith(".v")]
    assert sorted(expected_v_files) == sorted(v_files)

    coq_results: list[float] = []
    task_to_verify: Task | None = None
    if not opts.repeat_declaration:  # declaration should be compiled first
        dec_time = compile_certificate(
            opts.prosa_path, certificates_path, declaration_v_name, False
        )
        coq_results.append(dec_time)

    if opts.verify_only_id is None:
        parallel_results = Parallel(n_jobs=opts.jobs)(
            delayed(compile_certificate)(
                opts.prosa_path, certificates_path, v, not opts.repeat_declaration
            )
            for v in expected_v_files
            if v != declaration_v_name
        )
        coq_results.extend(parallel_results)
        coq_success = all(r > 0 for r in coq_results)

        for i in range(len(coq_results)):
            stopwatch.set_time(f"{expected_v_files[i]}_coq_time", coq_results[i])
    else:
        task_to_verify_vec = [
            t for t in problem_instance.task_set if t.id == opts.verify_only_id
        ]
        assert task_to_verify_vec and len(task_to_verify_vec) == 1
        task_to_verify = task_to_verify_vec[0]
        v = task_to_verify.v_name()
        time = compile_certificate(
            opts.prosa_path, certificates_path, v, not opts.repeat_declaration
        )
        coq_success = time > 0
        stopwatch.set_time(f"{v}_coq_time", time)

    return CoqCompileResult(
        success=coq_success,
        task_to_verify=task_to_verify,
        expected_v_files=expected_v_files,
        declaration_v_name=declaration_v_name,
    )


def verify_certificates(
    problem_instance: Problem,
    certificates_path: str,
    task_to_verify: Task | None,
    opts: POETArgs,
    stopwatch: timing.Stopwatch,
) -> bool:
    declaration_vo_name = f"{templates.TASK_SET_DECLARATION_FILE_NAME}.vo"

    if opts.verify_only_id is None:
        expected_vo_files = [t.vo_name() for t in problem_instance.task_set]
        if not opts.repeat_declaration:
            expected_vo_files = [declaration_vo_name] + expected_vo_files
        vo_files = [
            f.name for f in os.scandir(certificates_path) if f.name.endswith(".vo")
        ]
        assert sorted(expected_vo_files) == sorted(vo_files)

        parallel_results = Parallel(n_jobs=opts.jobs)(
            delayed(verify_certificate)(
                opts.prosa_path,
                certificates_path,
                vo,
                opts.verify_without_dependencies,
            )
            for vo in expected_vo_files
        )
        coqchk_results = parallel_results
        coqchk_success = all(r > 0 for r in coqchk_results)

        for i in range(len(coqchk_results)):
            stopwatch.set_time(f"{expected_vo_files[i]}_coqchk_time", coqchk_results[i])
        return coqchk_success

    assert task_to_verify is not None
    vo = task_to_verify.vo_name()
    time = verify_certificate(
        opts.prosa_path,
        certificates_path,
        vo,
        opts.verify_without_dependencies,
    )
    stopwatch.set_time(f"{vo}_coqchk_time", time)
    return time > 0


def finalize_run(
    certificates_path: str,
    stats_folder: str,
    stats: statistics.Statistics,
    coq_success: bool,
    success: bool,
    opts: POETArgs,
) -> None:
    if opts.delete_certificates:
        clean_certificates_folder(certificates_path, True)

    if success:
        print("Stats for: ", certificates_path)
        print(stats)
    else:
        if coq_success:
            print(f"ERROR: Could not verify certificates (path: {certificates_path})")
        else:
            print(f"ERROR: Could not compile certificates (path: {certificates_path})")

    if opts.save_stats:
        name = "stats.yaml" if success else "stats_error.yaml"
        stats_path = os.path.join(stats_folder, name)
        stats.save(stats_path)


def parse_args() -> POETArgs:
    parser = argparse.ArgumentParser(
        prog="poet", description="POET: A foundational response-time analysis tool"
    )

    _ = parser.add_argument("input_path", help="Input file.")

    _ = parser.add_argument(
        "-c",
        "--clean",
        dest="clean_output_folder",
        default=False,
        action="store_true",
        help="Empty the folder before generating new certificates.",
    )

    _ = parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        default=None,
        action="store",
        help="Folder in which proofs will be generated.",
    )

    _ = parser.add_argument(
        "-p",
        "--prosa",
        dest="prosa_path",
        default=None,
        action="store",
        help="Prosa root folder (when using a development version).",
    )

    _ = parser.add_argument(
        "-j",
        "--jobs",
        dest="jobs",
        default=1,
        type=int,
        action="store",
        help="Maximum number of jobs while compiling and verifying.",
    )

    _ = parser.add_argument(
        "-i",
        "--id",
        dest="verify_only_id",
        default=None,
        action="store",
        type=int,
        help="Only performs formal verification on one task",
    )

    _ = parser.add_argument(
        "-s",
        "--stats",
        dest="save_stats",
        default=False,
        action="store_true",
        help="Output a YAML file containing the statistics of the task set",
    )

    _ = parser.add_argument(
        "-d",
        "--delete",
        dest="delete_certificates",
        default=False,
        action="store_true",
        help="Delete certificates after checking them",
    )

    _ = parser.add_argument(
        "-b",
        "--bounded-tardiness",
        dest="bounded_tardiness_allowed",
        default=False,
        action="store_true",
        help="Allow deadline violations (i.e., soft deadlines)",
    )

    _ = parser.add_argument(
        "-t",
        "--test-schedulability",
        dest="test_schedulability",
        default=False,
        action="store_true",
        help="Test if the task-set is schedulable (no certificate generation).",
    )

    _ = parser.add_argument(
        "-r",
        "--repeat-declaration",
        dest="repeat_declaration",
        default=False,
        action="store_true",
        help="Repeat the task set declaration in every certificate.",
    )

    _ = parser.add_argument(
        "-v",
        "--verify-without-dependencies",
        dest="verify_without_dependencies",
        default=False,
        action="store_true",
        help="Ignore the dependencies (Prosa, ssreflect, ...) while verifying.",
    )

    _ = parser.add_argument(
        "-n",
        "--no-check",
        dest="no_check",
        default=False,
        action="store_true",
        help="Only generate but do not actually check the certificates.",
    )

    return parser.parse_args(namespace=POETArgs())


def ensure(condition: bool, error_message: str) -> None:
    if not condition:
        print(error_message)
        sys.exit(1)


def clean_certificates_folder(certificates_path: str, delete_all: bool = False) -> None:
    if not os.path.exists(certificates_path):
        return

    if delete_all:
        shutil.rmtree(certificates_path)
    else:
        for file in os.scandir(certificates_path):
            ext = os.path.splitext(file)[1]
            if ext in GENERATED_FILE_TYPES:
                os.unlink(file.path)

        remainining_files = len(os.listdir(certificates_path))
        if remainining_files > 0:
            print(
                f"Certificates path is not empty: {remainining_files} files detected. Continuing anyway..."
            )


def save_certificate(path: str, certificate: str) -> None:
    try:
        with open(path, "w") as f:
            _ = f.write(certificate)
    except Exception as e:
        print(f"Error while saving certificate to '{path}'")
        print(e)


def compile_certificate(
    prosa_path: str | None,
    certificates_path: str,
    certificate: str,
    _external_dec: bool,
) -> float:
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer("coq_time")
    print(f"Compiling {certificate}...")
    cmd = [
        "coqc",
        "-w",
        "-notation-overriden,-parsing,-projection-no-head-constant",
        certificate,
    ]
    if prosa_path:
        cmd += ["-Q", prosa_path, "prosa"]

    return_code = subprocess.call(cmd, cwd=certificates_path)
    success = return_code == 0
    if not success:
        print(f"Compilation of {certificate} ended with return code {return_code}")
        sys.exit(return_code)

    time = stopwatch.stop_timer("coq_time")
    return time if success else -1


def verify_certificate(
    prosa_path: str | None,
    certificates_path: str,
    certificate: str,
    verify_without_dependencies: bool,
) -> float:
    stopwatch = timing.Stopwatch()
    stopwatch.start_timer("coqchk_time")
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
        sys.exit(return_code)

    time = stopwatch.stop_timer("coqchk_time")
    return time if success else -1


if __name__ == "__main__":
    run_poet()
