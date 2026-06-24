from __future__ import annotations

from benchmarks.cases.jsplib.scheduling.jobshop._common import JobShopCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE

CASE_MODULE = __name__

DMU01 = JobShopCase(
    benchmark_id='jsplib_dmu01',
    source='JSPLIB via ScheduleOpt',
    problem_type='scheduling',
    instance_type='jobshop',
    instance='dmu01',
    family='interval_job_shop',
    tier='full',
    compare_key='jsplib/scheduling/jobshop/dmu01',
    series_key='jsplib/scheduling/jobshop/dmu01/interval_var_sequence_no_overlap_precedence',
    size={'jobs': 20, 'machines': 15, 'operations': 300},
    data={'documentation_url': 'https://scheduleopt.github.io/benchmarks/jsplib/',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu01.json',
 'solution_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json'},
    reference={'lower_bound': 2563,
 'objective': 2563,
 'reported_machine': 'i7-1185G7 @ 3.00GHz',
 'reported_solver': 'OptalCP',
 'reported_time_seconds': 60,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json',
 'status': 'closed',
 'upper_bound': 2563,
 'value_kind': 'optimal'},
    problem_description=('JSPLIB job-shop instance dmu01: schedule 20 jobs across 15 machines. Each job has a fixed '
 'machine route and fixed operation durations; each machine can process at most one operation at a '
 'time. The benchmark objective is minimum makespan.'),
    case_module=CASE_MODULE,
    modeling_notes={'model_style': 'interval_var_sequence_no_overlap_precedence',
 'objective_sense': 'minimize',
 'public_api_primitives': ['interval_var', 'sequence_var', 'no_overlap', 'precedence', 'max']},
    extra={'modeling_form': 'interval scheduling with machine sequences and job precedences',
 'objective_sense': 'minimize',
 'optagent_modeling': {'constraints': ['builder.no_overlap(machine_order[m], '
                                       '*operations_on_machine[m]) for every machine',
                                       'builder.precedence(operation[j,k], operation[j,k+1]) for '
                                       'every consecutive operation in each job'],
                       'data_mapping': 'Read ScheduleOpt JSPLIB JSON rows as operations with job, '
                                       'operation index, machine, and duration.',
                       'decision_variables': ['300 interval_var operation[j,k] with fixed duration '
                                              'and bounded start',
                                              '15 sequence_var machine_order[m], each ordering '
                                              'operations assigned to one machine'],
                       'objective': 'builder.minimize(builder.max(*(builder.interval_end(last_operation[j]) '
                                    "for each job)), name='makespan')",
                       'solver_routes': ['solve with AlnsConfig', 'solve with GaConfig']},
 'optagent_primitives': ['interval_var', 'sequence_var', 'no_overlap', 'precedence', 'max'],
 'recommended_evaluation': {'budgets_seconds': {'calibration': 60, 'full': 600, 'smoke': 10},
                            'primary_route': 'solve(..., strategy=AlnsConfig/GaConfig) for search',
                            'strategy_candidates': ['alns', 'ga'],
                            'target_metrics': ['gap_to_reference',
                                               'time_to_first_feasible',
                                               'time_to_best',
                                               'feasible_rate']}},
)

CASES = (DMU01,)
