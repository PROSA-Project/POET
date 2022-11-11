# POET: A Foundational Response-Time Analysis Tool

POET is the first implementation of a _foundational response-time analysis_. Both the tool and the approach are discussed in detail in an [ECRTS 2022 paper](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf). 

In short, given a YAML-encoded description of a workload comprised of sporadic or periodic real-time tasks to be scheduled on a uniprocessor, POET will first perform a response-time analysis and then generate a [Coq proof](https://coq.inria.fr) for each task that shows the computed response-time bound to be correct, i.e., a machine-checkable *certificate of correctness*. In other words, POET produces *proof-carrying response-time bounds* that can be verified independently of the (unverified) tool that computed them.

There are two primary benefits to the foundational approach realized by POET:

1. *Trustworthy* results based on a small [TCB](https://en.wikipedia.org/wiki/Trusted_computing_base) containing only standard tools: Neither the underlying theory nor the implementation of the response-time analysis (i.e., POET itself) must be trusted. Only the Coq toolchain and its dependencies form the TCB.

2. *Explainable* results: the generated certificates are designed for readability and can be explored by a human to any desired degree of scrutiny, up to the axioms of the underlying logic.

Please see [the paper](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf) for an in-depth explanation of these benefits. 

## Citation

When using POET for academic work, please cite the following paper:

- M. Maida, S. Bozhko, and B. Brandenburg, “[Foundational Response-Time Analysis as Explainable Evidence of Timeliness](https://drops.dagstuhl.de/opus/volltexte/2022/16336/pdf/LIPIcs-ECRTS-2022-19.pdf)”, Proceedings of the 34th Euromicro Conference on Real-Time Systems (ECRTS 2022), pp. 19:1–19:25, July 2022.


## Installation

POET requires two sets of dependencies: 

1. A working Python installation, to run POET itself (it is a Python script). 
2. A working Coq toolchain with the [Prosa framework](https://prosa.mpi-sws.org) installed, to compile and check the generated certificates.

### Python Dependencies

POET will work with [Python 3.7](https://www.python.org/downloads/) or any later version. 

Additionally, the following two Python packages are required:

- [PyYAML](https://pypi.org/project/PyYAML/)
- [joblib](https://pypi.org/project/joblib/)

All Python dependencies can be easily installed with Python's `pip3` package manager:

```
pip3 install -r requirements.txt
```

### Coq Toolchain

POET generates Coq-based certificates using the [Prosa library](https://prosa.mpi-sws.org), which provides the underlying verified real-time scheduling theory. To check the generated certificates, a working Coq toolchain and the Prosa library and its dependencies are hence required. 

The easiest way to install the Coq environment is via the OCaml Package Manager [`opam`](https://opam.ocaml.org), which is readily packaged for most Linux distributions and macOS (see [the `opam` installation instructions](https://opam.ocaml.org/doc/Install.html) for details).

Assuming `opam` has been installed and initialized, a working Coq environment suitable for POET can be set up as follows. 

First, create a new `opam` "switch" (i.e., a new environment). 

```
opam switch create Prosa-v0.5 4.13.1
```

After the switch has been created, be sure to activate it in the current shell.

```
eval $(opam env --switch=Prosa-v0.5)
```

Next, make `opam` aware of the official repository of stable Coq packages...

```
opam repo add coq-released https://coq.inria.fr/opam/released
```

... and pull in the latest package list.

```
opam update
```

Finally, simply install Prosa version 0.5, which will pull in all necessary dependencies.

```
opam install coq-prosa.0.5
```

The compilation and installation of all packages will take some time.


## Usage

POET supports a number of different command-line arguments and system models. POET command-line arguments affect (only) how POET operates. Conversely, everything relevant to the scheduling problem is specified (only) in the input file. 

A typical invocation of POET looks like this:

```
./poet -c -s path/to/my/workload.yaml
```

This has the following effects: 

- POET will read the problem instance contained in `path/to/my/workload.yaml` and produces a  `certificates/` folder in the same directory. The files inside the folder are compiled using the Coq toolchain found in the current `$PATH` (which should be installed with `opam` as described above).  
- The `-c` flag makes POET clean the `certificates/` folder (i.e., POET deletes any old files) before generating new certificates, which is helpful when running POET repeatedly. 
- The `-s` flag causes POET to report some simple statistics on its runtime and the generated certificates.

To create the certificates in a different location, pass the `-o` flag with the target directory. For example, 

```
./poet -c -v -s -o /tmp/certificates path/to/my/workload.yaml
```

will generate and compile the certificates in the folder `/tmp/certificates`. If the path does not exists, it is created.

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
  
* Axioms:
    mathcomp.ssreflect.finset.Imset.imsetE
    mathcomp.ssreflect.finset.Imset.imset2
    mathcomp.fingroup.perm.PermDef.fun_of_perm
    Coq.ssr.ssrunder.Under_rel.Over_rel
    mathcomp.ssreflect.finfun.FinfunDef.finfunE
    mathcomp.ssreflect.fintype.SubsetDef.subsetEdef
    mathcomp.ssreflect.generic_quotient.MPi.f
    mathcomp.ssreflect.generic_quotient.MPi.E
    Coq.ssr.ssrunder.Under_rel.Under_rel_from_rel
    mathcomp.ssreflect.fintype.Finite.EnumDef.enumDef
    mathcomp.ssreflect.generic_quotient.Repr.f
    mathcomp.ssreflect.generic_quotient.Repr.E
    mathcomp.fingroup.perm.PermDef.fun_of_permE
    mathcomp.ssreflect.finset.Imset.imset
    Coq.Logic.ProofIrrelevance.proof_irrelevance
    mathcomp.ssreflect.finset.Imset.imset2E
    mathcomp.ssreflect.finset.SetDef.pred_of_set
    mathcomp.ssreflect.finset.SetDef.finset
    Coq.ssr.ssrunder.Under_rel.over_rel
    mathcomp.ssreflect.tuple.FinTuple.enumP
    mathcomp.ssreflect.tuple.FinTuple.enum
    mathcomp.ssreflect.bigop.BigOp.bigopE
    Coq.ssr.ssrunder.Under_rel.over_rel_done
    mathcomp.ssreflect.tuple.FinTuple.size_enum
    mathcomp.ssreflect.finfun.FinfunDef.finfun
    Coq.ssr.ssrunder.Under_rel.Under_rel
    mathcomp.ssreflect.fintype.CardDef.card
    mathcomp.ssreflect.fintype.CardDef.cardEdef
    mathcomp.ssreflect.finset.SetDef.pred_of_setE
    Coq.ssr.ssrunder.Under_rel.Under_relE
    mathcomp.fingroup.perm.PermDef.permE
    mathcomp.fingroup.perm.PermDef.perm
    mathcomp.ssreflect.bigop.BigOp.bigop
    mathcomp.ssreflect.fintype.SubsetDef.subset
    mathcomp.ssreflect.generic_quotient.Pi.f
    mathcomp.ssreflect.generic_quotient.Pi.E
    mathcomp.ssreflect.fintype.Finite.EnumDef.enum
    Coq.ssr.ssrunder.Under_rel.under_rel_done
    mathcomp.ssreflect.finset.SetDef.finsetE
  
* Constants/Inductives relying on type-in-type: <none>
  
* Constants/Inductives relying on unsafe (co)fixpoints: <none>
  
* Inductives whose positivity is assumed: <none>

```

The above output is repeated for each task (omitted here).

Note that, in the output above, there are no references to admit or admitted proofs, but only to `Axioms`. There are two important points to note:

1. The "axioms" starting with `mathcomp.*` and `Coq.*` are part of the Mathematical Components library and Coq standard library, respectively. Most of these are not axioms in the usual sense, but interfaces of Module Types, a Coq facility for generating generic modules (see [this tutorial](https://github.com/coq/coq/wiki/ModuleSystemTutorial) for an introduction). The one notable exception is `Coq.Logic.ProofIrrelevance.proof_irrelevance`, which is truly an axiom used by CoqEAL. 

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
coq               : 3.21 s
coqchk            : 3.54 s
Other             : 0.00 s
Total             : 6.75 s

#######     TASKS STATS       #######
tsk01    | R : 50 | L : 50 | SS: 2 | coq : 1.287811 | coqchk : 1.170234
tsk02    | R : 60 | L : 80 | SS: 3 | coq : 1.294425 | coqchk : 1.190660
```

Please refer to the paper for an intuitive explanation of how to interpret the generated certificates.


## Credits and Contact

POET was originally developed by Marco Maida and Sergey Bozhko. It is now being maintained by the [Prosa project](https://prosa.mpi-sws.org). Please contact the Prosa maintainers for any questions, suggestions, or patches, or open an issue on GitLab. 

Merge requests welcome! 

## License

POET is free software and distributed under a BSD 2-Clause license. 
