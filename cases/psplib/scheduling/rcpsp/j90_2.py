from __future__ import annotations

from benchmarks.cases.psplib.scheduling.rcpsp._common import RcpspCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE

CASE_MODULE = __name__

J90_2_4 = RcpspCase(
    benchmark_id='psplib_j90_2_4',
    source='PSPLIB j90 via ScheduleOpt',
    problem_type='scheduling',
    instance_type='rcpsp',
    instance='j90_2_4',
    family='cumulative_resource_scheduling',
    tier='calibration',
    compare_key='psplib/scheduling/rcpsp/j90_2_4',
    series_key='psplib/scheduling/rcpsp/j90_2_4/interval_var_cumulative_precedence',
    size={'activities': 90, 'renewable_resources': 4},
    data={'bounds_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'instance_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_2_4.rcp'},
    reference={'lower_bound': 70,
 'notes': 'Rows marked with * in j90lb.sm have verified LB=UB optimal makespan.',
 'objective': 70,
 'source_url': 'https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90lb.sm',
 'status': 'closed',
 'upper_bound': 70,
 'value_kind': 'optimal'},
    problem_description=('PSPLIB RCPSP instance j90_2_4: schedule 90 project activities with precedence constraints and '
 'four renewable resources. The objective is minimum project makespan; this selected case has a '
 'verified optimum.'),
    case_module=CASE_MODULE,
    modeling_notes={'model_style': 'interval_var_cumulative_precedence',
 'objective_sense': 'minimize',
 'public_api_primitives': ['interval_var', 'precedence', 'cumulative', 'max']},
    extra={'modeling_form': 'interval project scheduling with renewable resource cumulative constraints',
 'objective_sense': 'minimize',
 'optagent_modeling': {'constraints': ['builder.precedence(activity[i], activity[j]) for every '
                                       'project precedence arc',
                                       'builder.cumulative(intervals, demands_for_resource[r], '
                                       'capacity[r]) for each renewable resource'],
                       'data_mapping': 'Read PSPLIB .rcp activity durations, renewable-resource '
                                       'demands, capacities, and successor lists.',
                       'decision_variables': ['one interval_var activity[i] per non-dummy activity '
                                              'with fixed duration and bounded start'],
                       'objective': 'builder.minimize(builder.max(*(builder.interval_end(activity[i]) '
                                    "for terminal activities)), name='makespan')",
                       'solver_routes': ['solve with AlnsConfig', 'solve with GaConfig']},
 'optagent_primitives': ['interval_var', 'precedence', 'cumulative', 'max'],
 'recommended_evaluation': {'budgets_seconds': {'calibration': 180, 'full': 900, 'smoke': 30},
                            'primary_route': 'solve(..., strategy=AlnsConfig/GaConfig) for search',
                            'strategy_candidates': ['alns', 'ga'],
                            'target_metrics': ['gap_to_upper_bound',
                                               'gap_to_lower_bound',
                                               'time_to_first_feasible',
                                               'feasible_rate']}},
)

CASES = (J90_2_4,)
