# POET: A Foundational Response-Time Analysis Tool

POET is the first implementation of a _foundational response-time analysis_. Both the tool and the approach are discussed in detail in an [ECRTS 2022 paper](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf). 

In short, given a YAML-encoded description of a workload comprised of sporadic or periodic real-time tasks to be scheduled on a uniprocessor, POET will first perform a response-time analysis and then generate a [Rocq proof](https://[coq.inria.fr](https://rocq-prover.org)) for each task that shows the computed response-time bound to be correct, i.e., a machine-checkable *certificate of correctness*. In other words, POET produces *proof-carrying response-time bounds* that can be verified independently of the (unverified) tool that computed them.

There are two primary benefits to the foundational approach realized by POET:

1. *Trustworthy* results based on a small [TCB](https://en.wikipedia.org/wiki/Trusted_computing_base) containing only standard tools: Neither the underlying theory nor the implementation of the response-time analysis (i.e., POET itself) must be trusted. Only the Rocq toolchain and its dependencies form the TCB.

2. *Explainable* results: the generated certificates are designed for readability and can be explored by a human to any desired degree of scrutiny, up to the axioms of the underlying logic.

Please see [the paper](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf) for an in-depth explanation of these benefits. 

## Citation

When using POET for academic work, please cite the following paper:

- M. Maida, S. Bozhko, and B. Brandenburg, “[Foundational Response-Time Analysis as Explainable Evidence of Timeliness](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf)”, Proceedings of the 34th Euromicro Conference on Real-Time Systems (ECRTS 2022), pp. 19:1–19:25, July 2022.


## Installation

POET requires two sets of dependencies: 

1. A working Python installation with the [`uv` package manager](https://docs.astral.sh/uv/) in place, to run POET itself (it is a Python script launched via `uv`). 
2. A working Rocq toolchain with the [Prosa framework](https://prosa.mpi-sws.org) installed, to compile and check the generated certificates.

### Python Dependencies

POET has been tested with Python 3.14, but older versions down to 3.10 or so will likely work, too.

Additionally, the following two Python packages are required:

- [PyYAML](https://pypi.org/project/PyYAML/)
- [joblib](https://pypi.org/project/joblib/)

The Python dependencies will be installed automatically by `uv` and do not have to be managed manually.

### Rocq Toolchain

POET generates Rocq-based certificates using the [Prosa library](https://prosa.mpi-sws.org), which provides the underlying verified real-time scheduling theory. To check the generated certificates, a working Rocq toolchain and the Prosa library and its dependencies are hence required. 

The recommended way to install the Rocq environment is via the OCaml Package Manager [`opam`](https://opam.ocaml.org), which is readily packaged for most Linux distributions and macOS (see [the `opam` installation instructions](https://opam.ocaml.org/doc/Install.html) for details).

Assuming `opam` has been installed and initialized, a working Rocq environment suitable for POET can be set up as follows. 

First, create a new `opam` "switch" (i.e., a new environment). 

```
opam switch create Prosa-v0.6 4.14.2
```

After the switch has been created, be sure to activate it in the current shell.

```
eval $(opam env --switch=Prosa-v0.6)
```

Next, make `opam` aware of the official repository of stable Coq packages...

```
opam repo add rocq-released https://rocq-prover.org/opam/released
```

... and pull in the latest package list.

```
opam update
```

Finally, simply install Prosa version 0.6 and its refinements package, which will pull in all necessary dependencies.

```
opam install rocq-prosa-refinements.0.6
```

The compilation and installation of all packages will take some time.


## Usage

POET supports a number of different command-line arguments and system models. POET command-line arguments affect (only) how POET operates. Conversely, everything relevant to the scheduling problem is specified (only) in the input file. 

A typical invocation of POET looks like this:

```
./poet -c -s path/to/my/workload.yaml
```

This has the following effects: 

- POET will read the problem instance contained in `path/to/my/workload.yaml` and produces a  `certificates/` folder in the same directory. The files inside the folder are compiled using the Rocq toolchain found in the current `$PATH` (which should be installed with `opam` as described above).  
- The `-c` flag makes POET clean the `certificates/` folder (i.e., POET deletes any old files) before generating new certificates, which is helpful when running POET repeatedly. 
- The `-s` flag causes POET to report some simple statistics on its runtime and the generated certificates.

To create the certificates in a different location, pass the `-o` flag with the target directory. For example, 

```
./poet -c -v -s -o /tmp/certificates examples/paper.yaml
```

will generate and compile the certificates in the folder `/tmp/certificates`. If the path does not exist, it is created.

Notably, when specifying the `-v` flag, POET will invoke `coqchk` *only* on the generated certificates, but will not check the dependencies of the certificates. Omit this flag to check everything (recommended, but slower). 


Run `./poet -h` to see all supported command-line arguments and flags.

## Input File Format

POET operates on a straightforward [YAML](https://en.wikipedia.org/wiki/YAML) schema that defines the workload to be analyzed.

Consider the example given in Listing 1 of the paper:

```yaml
scheduling policy: FP   # fixed-priority
preemption model:  FP   # fully-preemptive
task set:

- id: 1
  worst-case execution time: 50
  arrival curve: [220,[[1,1],[105,2]]]
  deadline: 100
  priority: 2

- id: 2
  worst-case execution time: 10
  period: 30
  deadline: 100
  priority: 1
```

The format works as follows. There are three top-level keys:

- `scheduling policy`: this key defines which scheduling policy to assume. Currently supported policies:
    * `FP` — fixed-priority scheduling
    * `EDF` — earliest-deadline-first scheduling
- `preemption model`: this key specifies the preemption model of the workload. Currently supported preemption models:
    * `FP` — fully preemptive scheduling (i.e., jobs can be preempted at any time)
    * `NP` — fully non-preemptive scheduling (i.e., jobs run to completion after commencing execution)
- `task set`: this key holds the list of tasks that comprise the workload.

Each task is specified with the following keys:

- `id`: a unique ID that identifies the task in the output.
- `worst-case execution time`: The task's WCET, i.e., the maximum amount of processor service required to complete a single job.
- `arrival curve` or `period`: the arrival model (only one should be given).
    * `period`: specify the period of a periodic task, or the minimum inter-arrival time of a sporadic task.
    * `arrival curve`: specify an arrival-curve prefix that describes the maximum number of activations in any interval. The arrival-curve prefix is specified by a tuple `(HORIZON, LIST-OF-STEPS)`. For example, in the above listing, task 1 is specified with a horizon of 220 and steps at 1 and 105. See the paper for details.
- `deadline`: The relative deadline of the task.
- `priority`: The fixed priority of the task (irrelevant under EDF). The interpretation is that a numerically higher value indicates higher priority (e.g., as it is the case with Linux's `SCHED_FIFO` scheduler).


It is expected that future work will extend the input format as needed to accommodate more advanced RTAs.

## Output

A typical output of POET will look as follows. First, POET runs `coqc` on the input task set: 

```
Compiling task_set.v...
Compiling tsk01.v...
Closed under the global context
Compiling tsk02.v...
Closed under the global context
```

After `coqc` compiles all tasks, POET executes `coqchk` to validate the correctness of generates proof terms.  The expected output is the following:

```
Verifying task_set.vo...

CONTEXT SUMMARY
===============

* Theory: Set is predicative
  
* Theory: Rewrite rules are not allowed
  
* Axioms:
    mathcomp.ssreflect.finset.set1.unlock
    mathcomp.algebra.mxalgebra.diffmx.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.land_spec
    mathcomp.ssreflect.fintype.enum_rank_in.unlock
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.lor_spec
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.odd_bitwise
    Corelib.ssr.ssrunder.Under_rel.Under_rel_from_rel
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_bitwise_2
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_bitwise_1
    mathcomp.ssreflect.finset.finset.body
    mathcomp.algebra.mxalgebra.capmx.body
    mathcomp.ssreflect.finset.pred_of_set.unlock
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_odd_0
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_neg_r
    mathcomp.fingroup.perm.perm.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.shiftl_spec_high
    mathcomp.ssreflect.fintype.FiniteNES.Finite.enum.unlock
    mathcomp.ssreflect.finfun.finfun.unlock
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.shiftl_spec_low
    mathcomp.algebra.mxalgebra.addsmx.body
    mathcomp.algebra.mxalgebra.mxrank.body
    mathcomp.ssreflect.finset.imset.unlock
    mathcomp.fingroup.fingroup.generated.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.shiftr_spec
    mathcomp.algebra.matrix.matrix_of_fun.unlock
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_odd_succ
    mathcomp.ssreflect.finset.set1.body
    mathcomp.algebra.mxalgebra.Gaussian_elimination.unlock
    Corelib.ssr.ssrunder.Under_rel.over_rel
    mathcomp.ssreflect.fintype.enum_rank_in.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.div2_double
    mathcomp.algebra.mxalgebra.genmx.unlock
    mathcomp.ssreflect.finset.imset2.unlock
    mathcomp.algebra.mxalgebra.submx.unlock
    mathcomp.ssreflect.finset.pred_of_set.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.ldiff_spec
    Corelib.ssr.ssrunder.Under_rel.over_rel_done
    mathcomp.ssreflect.fintype.FiniteNES.Finite.enum.body
    mathcomp.ssreflect.finfun.finfun.body
    Corelib.ssr.ssrunder.Under_rel.Under_rel
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_even_succ
    Stdlib.Logic.ProofIrrelevance.proof_irrelevance
    mathcomp.ssreflect.finset.imset.body
    mathcomp.algebra.matrix.matrix_of_fun.body
    mathcomp.ssreflect.tuple.FinTuple.enumP
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.div2_succ_double
    mathcomp.ssreflect.tuple.FinTuple.enum
    Corelib.ssr.ssrunder.Under_rel.Under_relE
    mathcomp.ssreflect.tuple.FinTuple.size_enum
    mathcomp.algebra.mxalgebra.Gaussian_elimination.body
    mathcomp.ssreflect.fintype.subset.unlock
    mathcomp.fingroup.perm.porbit.unlock
    mathcomp.algebra.mxalgebra.genmx.body
    mathcomp.fingroup.perm.fun_of_perm.unlock
    mathcomp.ssreflect.finset.imset2.body
    mathcomp.ssreflect.fintype.card.unlock
    mathcomp.algebra.mxalgebra.submx.body
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.testbit_even_0
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.div2_bitwise
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.div2_spec
    mathcomp.ssreflect.bigop.bigop.unlock
    mathcomp.algebra.mxalgebra.diffmx.unlock
    Corelib.ssr.ssrunder.Under_rel.under_rel_done
    Stdlib.Arith.PeanoNat.Nat.PrivateImplementsBitwiseSpec.lxor_spec
    mathcomp.ssreflect.finset.finset.unlock
    mathcomp.algebra.mxalgebra.capmx.unlock
    mathcomp.fingroup.perm.perm.unlock
    mathcomp.ssreflect.fintype.subset.body
    mathcomp.fingroup.perm.porbit.body
    mathcomp.fingroup.perm.fun_of_perm.body
    mathcomp.ssreflect.fintype.card.body
    mathcomp.algebra.mxalgebra.addsmx.unlock
    mathcomp.algebra.mxalgebra.mxrank.unlock
    mathcomp.fingroup.fingroup.generated.unlock
    Corelib.ssr.ssrunder.Under_rel.Over_rel
    mathcomp.ssreflect.bigop.bigop.body
  
* Constants/Inductives relying on type-in-type: <none>
  
* Constants/Inductives relying on unsafe (co)fixpoints: <none>
  
* Inductives whose positivity is assumed: <none>

```

The above output is repeated for each task (omitted here).

Note that, in the output above, there are no references to admit or admitted proofs, but only to `Axioms`. There are two important points to note:

1. The "axioms" starting with `mathcomp.*`, `Corelib.*`, and `Stdlib.*` are part of the Mathematical Components and Rocq standard libraries. Most of these are not axioms in the usual sense, but interfaces of Module Types, a Rocq facility for generating generic modules (see [this tutorial](https://github.com/rocq-prover/rocq/wiki/ModuleSystemTutorial) for an introduction). The one notable exception is `Stdlib.Logic.ProofIrrelevance.proof_irrelevance`, which is truly an axiom used by CoqEAL. 

2. Most importantly, there are no entries starting with `prosa.*` (the logical base directory of Prosa and POET), which implies that there are no axioms or admitted proofs in the generated files.

Finally, POET produces some statistics on its runtime and the generated certificates. It includes: 

1. A short summary of the task set'ss characteristics, like the number of tasks and their utilization.
2. The time spent on Python computation (`poet`), `coqc` computation (`coq`), and `coqchk` computation (`coqchk`).
3. Individual stats for each task in the task set. Here, `R` denotes the response time of the task, `L` is an upper bound on the busy-window length, `SS` is the number of points in the search space, and `coq` and `coqchk` measure time spent by `coqc` and `coqchk` respectively compiling and verifying the task's certificate.


```
####### PROBLEM INSTANCE STATS #######
Number of tasks   : 2
Task set util.    : 0.79
Avg numerical mag : 85

#######      TIME STATS       #######
Poet              : 0.00 s
coq               : 7.28 s
coqchk            : 4.89 s
Other             : 0.00 s
Total             : 12.17 s

#######     TASKS STATS       #######
tsk01    | R : 50 | L : 50 | SS: 2 | coq : 2.304908 | coqchk : 1.586764
tsk02    | R : 60 | L : 80 | SS: 3 | coq : 2.302432 | coqchk : 1.597552
```

Please refer to the paper for an intuitive explanation of how to interpret the generated certificates.


## Credits and Contact

POET was originally developed by Marco Maida and Sergey Bozhko. It is now being maintained by the [Prosa project](https://prosa.mpi-sws.org). Please contact the Prosa maintainers for any questions, suggestions, or patches, or open an issue on GitLab. 

Merge requests welcome! 

## License

POET is free software and distributed under a BSD 2-Clause license.
