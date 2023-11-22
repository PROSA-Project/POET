$DECLARATION_START$
Require Export prosa.implementation.refinements.FP.fast_search_space.
Require Export prosa.implementation.refinements.FP.refinements.
Require Export prosa.implementation.facts.job_constructor.
Require Export prosa.results.fixed_priority.rta.fully_nonpreemptive.
Require Export prosa.implementation.refinements.FP.nonpreemptive_sched.
Require Export NArith.

(** Recent versions of PROSA enable strict bullet checking, but
    the POET certificates don't yet comply with this (purely
    cosmetic) preference. So we disable the check here again. *)
#[global] Set Bullet Behavior "None".
#[global] Set Default Goal Selector "1".

Section TaskSetDeclaration.
  (** In the following, all numeric constants should be interpreted as *binary*
      numbers.  This is accomplished by opening the notation scope provided by
      the [NArith] module. *)
  Open Scope N_scope.

  $TASK_SET_DECLARATION$
  (** The above-declared tasks form the task set under analysis, which we denote
      [ts] in the following. *)
  Definition ts := $TASK_SET_LIST$.

  Lemma arrival_curve_is_valid :
    valid_taskset_arrival_curve (map taskT_to_task ts) max_arrivals.
  Proof.
    move => task IN.
    split.
    { repeat (move: IN; rewrite in_cons => /orP [/eqP -> | IN]); apply/eqP; last by done.
      all: rewrite /max_arrivals /MaxArrivals /concrete_max_arrivals.
      all: by clear; rewrite [_ == _]refines_eq; vm_compute. }
    { repeat (move: IN; rewrite in_cons => /orP [/eqP -> | IN]); last by done.
      all: rewrite /max_arrivals /MaxArrivals /concrete_max_arrivals /task_arrival.
      have TR1 := leq_steps_is_transitive.
      all: apply extrapolated_arrival_curve_is_monotone;
        [ by apply/eqP/eqP; clear; rewrite [_ == _]refines_eq; vm_compute
        | by rewrite /sorted_leq_steps -[sorted _  _]eqb_id; clear;
          rewrite [_ == _]refines_eq; vm_compute ]. }
  Qed.

  Lemma task_set_has_valid_arrivals:
    task_set_with_valid_arrivals (map taskT_to_task ts).
  Proof.
    intros task IN.
    repeat (move: IN; rewrite in_cons => /orP [/eqP EQtsk | IN]); subst; last by done.
    all: try by clear; rewrite [_ == _]refines_eq; vm_compute.
    all: by rewrite [valid_arrivals _]refines_eq; vm_compute.
  Qed.

End TaskSetDeclaration.

$CERTIFICATE_START$
Section Certificate.

  #[local] Existing Instance ideal.processor_state.
  #[local] Existing Instance fully_nonpreemptive_job_model.
  #[local] Existing Instance NumericFPAscending.

  Definition tsk := $TASK_UNDER_ANALYSIS$.
  Definition L := $MAX_BUSY_INTERVAL$.
  Definition R := $RESPONSE_TIME_BOUND$.
  $TARDINESS_BOUND_DECLARATION$
  Lemma L_fixed_point:
    blocking_bound_NP (map taskT_to_task ts) (taskT_to_task tsk) + total_hep_rbf (map taskT_to_task ts) (taskT_to_task tsk) L = L.
  Proof.
    rewrite /tsk; apply /eqP.
    by clear; rewrite [_ == _]refines_eq; vm_compute.
  Qed.

  Variable arr_seq : arrival_sequence Job.
  Hypothesis H_arr_seq_is_a_set : arrival_sequence_uniq arr_seq.
  Hypothesis H_all_jobs_from_taskset : all_jobs_from_taskset arr_seq (map taskT_to_task ts).
  Hypothesis H_arrival_times_are_consistent : consistent_arrival_times arr_seq.
  Hypothesis H_valid_job_cost: arrivals_have_valid_job_costs arr_seq.
  Hypothesis H_is_arrival_curve : taskset_respects_max_arrivals arr_seq (map taskT_to_task ts).

  Instance sequential_ready_instance : JobReady Job (ideal.processor_state Job) :=
      sequential_ready_instance arr_seq.

  Definition sched := nonpreemptive_sched.sched arr_seq.

  Lemma A_in_search_space:
    forall (A : duration),
      is_in_search_space (taskT_to_task tsk) L A ->
      A \in search_space_emax_FP (taskT_to_task tsk) L.
  Proof.
    move => A IN.
    eapply search_space_subset_FP.
    - by apply task_set_has_valid_arrivals.
    - by clear;apply/eqP/eqP; clear; rewrite [_ == _]refines_eq; vm_compute.
    - by clear;rewrite !in_cons /tsk eq_refl.
    - rewrite mem_filter.
      apply /andP; split; first by done.
      by rewrite mem_iota; move: IN => /andP[LT _].
  Qed.

  $F_SOLUTIONS$

  Lemma R_is_maximum:
    forall (A : duration),
      is_in_search_space (taskT_to_task tsk) L A ->
      exists (F : duration),
        blocking_bound_NP (map taskT_to_task ts) (taskT_to_task tsk)
        + (task_rbf (taskT_to_task tsk) (A + ε) - (concept.task_cost (taskT_to_task tsk) - ε))
        + total_ohep_rbf (map taskT_to_task ts) (taskT_to_task tsk) (A + F) <= A + F
        /\ F + (concept.task_cost (taskT_to_task tsk) - ε) <= R.
  Proof.
    move => A SS; move: (A_in_search_space A SS) => IN; clear SS.
    move: A IN; apply forall_exists_implied_by_forall_in_zip with
      (P_bool := check_point_NP (map taskT_to_task ts) (taskT_to_task tsk) R).
    by intros; split; intros; apply/andP.
    exists (map nat_of_bin Fs); split.
    - by apply/eqP; clear; rewrite [_ == _]refines_eq; vm_compute.
    - by clear; rewrite [_ == _]refines_eq; vm_compute.
  Qed.

  Ltac find_refl :=
  match goal with
  | [  |-  (is_true (?X == ?X) ) \/ _ ] => left; apply eq_refl
  | _ => right
  end.

  Theorem uniprocessor_response_time_bound_fully_nonpreemptive_fp_inst:
    task_response_time_bound arr_seq sched (taskT_to_task tsk) R.
  Proof.
    move: (sched_valid arr_seq) => [ARR READY].
    specialize (sequential_readiness_nonclairvoyance arr_seq) => NON_CL.
    eapply uniprocessor_response_time_bound_fully_nonpreemptive_fp
      with (ts := (map taskT_to_task ts)) (L := L).
    - by done.
    - by done.
    - by done.
    - by apply arrival_curve_is_valid.
    - by done.
    - by rewrite !in_cons /tsk; repeat(apply/orP; find_refl).
    - by done.
    - by apply sched_nonpreemptive.
    - by apply NFPA_is_reflexive.
    - by apply NFPA_is_transitive.
    - by apply uni_schedule_work_conserving.
    - by apply respects_policy_at_preemption_point_np.
    - by clear; rewrite [_ < _]refines_eq; vm_compute.
    - by symmetry; apply L_fixed_point.
    - by apply R_is_maximum.
  Qed.
  
  $DEADLINE_IS_RESPECTED_START$
  Corollary deadline_is_respected:
    task_response_time_bound arr_seq sched (taskT_to_task tsk) R /\ R <= task_deadline (taskT_to_task tsk).
  Proof.
    split.
    - by apply uniprocessor_response_time_bound_fully_nonpreemptive_fp_inst.
    - by clear; rewrite [_ <= _]refines_eq; vm_compute.
  Qed.
  $DEADLINE_IS_RESPECTED_END$ $TARDINESS_IS_BOUNDED_START$
  Corollary tardiness_is_bounded:
    task_tardiness_is_bounded arr_seq sched (taskT_to_task tsk) B.
  Proof.
    rewrite /task_tardiness_is_bounded.
    have-> :task_deadline (taskT_to_task tsk) + B = R by apply /eqP; rewrite [_ == _] refines_eq.
    by apply uniprocessor_response_time_bound_fully_nonpreemptive_fp_inst.
  Qed.
  $TARDINESS_IS_BOUNDED_END$
End Certificate.

(** 3 - We repeat the result for a specific arrival sequence to show the absence of
    contradictions. *)
Section AssumptionLessExample.

  Definition arr_seq_AL := concrete_arrival_sequence generate_jobs_at (map taskT_to_task ts).

  Instance sequential_ready_instance_AL : JobReady Job (ideal.processor_state Job) :=
    sequential_ready_instance arr_seq_AL.

  Definition sched_AL :=  sched arr_seq_AL.

  Theorem uniprocessor_response_time_bound_fully_nonpreemptive_fp_inst_AL:
    task_response_time_bound arr_seq_AL sched_AL (taskT_to_task tsk) R.
  Proof.
    apply uniprocessor_response_time_bound_fully_nonpreemptive_fp_inst => //.
    - by apply arr_seq_is_a_set, arrivals_between_unique.
    - by apply concrete_all_jobs_from_taskset, job_generation_valid_jobs.
    - by apply arrival_times_are_consistent, job_generation_valid_jobs.
    - by apply concrete_valid_job_cost, job_generation_valid_jobs.
    - apply concrete_is_arrival_curve; first by done.
      + by apply arrival_curve_is_valid.
      + by apply job_generation_valid_number.
      + by apply job_generation_valid_jobs.
  Qed.

End AssumptionLessExample.

$DEADLINE_IS_RESPECTED_PRINT_START$
Print Assumptions deadline_is_respected.
$DEADLINE_IS_RESPECTED_PRINT_END$ $TARDINESS_IS_BOUNDED_PRINT_START$
Print Assumptions tardiness_is_bounded.
$TARDINESS_IS_BOUNDED_PRINT_END$

