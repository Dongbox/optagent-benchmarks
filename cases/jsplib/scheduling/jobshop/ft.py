from __future__ import annotations

from benchmarks.cases.jsplib.scheduling.jobshop._common import JobShopCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE

CASE_MODULE = __name__

FT06 = JobShopCase(
    benchmark_id='jsplib_ft06',
    source='JSPLIB via ScheduleOpt',
    problem_type='scheduling',
    instance_type='jobshop',
    instance='ft06',
    family='interval_job_shop',
    tier='smoke',
    compare_key='jsplib/scheduling/jobshop/ft06',
    series_key='jsplib/scheduling/jobshop/ft06/interval_var_sequence_no_overlap_precedence',
    size={'jobs': 6, 'machines': 6, 'operations': 36},
    data={'documentation_url': 'https://scheduleopt.github.io/benchmarks/jsplib/',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ft06.json',
 'solution_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json'},
    reference={'lower_bound': 55,
 'objective': 55,
 'reported_machine': 'i7-1185G7 @ 3.00GHz',
 'reported_solver': 'OptalCP',
 'reported_time_seconds': 1,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json',
 'status': 'closed',
 'upper_bound': 55,
 'value_kind': 'optimal'},
    problem_description=('JSPLIB job-shop instance ft06: schedule 6 jobs across 6 machines. Each job has a fixed machine '
 'route and fixed operation durations; each machine can process at most one operation at a time. '
 'The benchmark objective is minimum makespan.'),
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
                       'decision_variables': ['36 interval_var operation[j,k] with fixed duration '
                                              'and bounded start',
                                              '6 sequence_var machine_order[m], each ordering '
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

FT10 = JobShopCase(
    benchmark_id='jsplib_ft10',
    source='JSPLIB via ScheduleOpt',
    problem_type='scheduling',
    instance_type='jobshop',
    instance='ft10',
    family='interval_job_shop',
    tier='smoke',
    compare_key='jsplib/scheduling/jobshop/ft10',
    series_key='jsplib/scheduling/jobshop/ft10/interval_var_sequence_no_overlap_precedence',
    size={'jobs': 10, 'machines': 10, 'operations': 100},
    data={'documentation_url': 'https://scheduleopt.github.io/benchmarks/jsplib/',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ft10.json',
 'solution_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json'},
    reference={'lower_bound': 930,
 'objective': 930,
 'reported_machine': 'i7-1185G7 @ 3.00GHz',
 'reported_solver': 'OptalCP',
 'reported_time_seconds': 1,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json',
 'status': 'closed',
 'upper_bound': 930,
 'value_kind': 'optimal'},
    problem_description=('JSPLIB job-shop instance ft10: schedule 10 jobs across 10 machines. Each job has a fixed machine '
 'route and fixed operation durations; each machine can process at most one operation at a time. '
 'The benchmark objective is minimum makespan.'),
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
                       'decision_variables': ['100 interval_var operation[j,k] with fixed duration '
                                              'and bounded start',
                                              '10 sequence_var machine_order[m], each ordering '
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

CASES = (FT06, FT10)
