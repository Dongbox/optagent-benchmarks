from __future__ import annotations

from benchmarks.cases.qaplib.assignment.quadratic_assignment._common import QapCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE

CASE_MODULE = __name__

LIPA40A = QapCase(
    benchmark_id='qaplib_lipa40a',
    source='QAPLIB',
    problem_type='assignment',
    instance_type='quadratic_assignment',
    instance='lipa40a',
    family='sequence_quadratic_assignment',
    tier='full',
    compare_key='qaplib/assignment/quadratic_assignment/lipa40a',
    series_key='qaplib/assignment/quadratic_assignment/lipa40a/sequence_var_external_call',
    size={'facilities': 40, 'locations': 40},
    data={'instance_page_url': 'https://qaplib.mgi.polymtl.ca/',
 'instance_url': 'https://qaplib.mgi.polymtl.ca/data.d/lipa40a.dat',
 'solution_page_url': 'https://qaplib.mgi.polymtl.ca/',
 'solution_url': 'https://qaplib.mgi.polymtl.ca/soln.d/lipa40a.sln'},
    reference={'objective': 31538,
 'source_label': 'Lipa40a',
 'source_url': 'https://qaplib.mgi.polymtl.ca/',
 'status': 'optimal',
 'value_kind': 'optimal'},
    problem_description=('QAPLIB quadratic assignment instance lipa40a: assign 40 facilities to 40 locations. The cost is '
 'the sum of flow between facility pairs multiplied by distance between assigned locations. This '
 'is a permutation blackbox benchmark with a published optimum.'),
    case_module=CASE_MODULE,
    modeling_notes={'model_style': 'sequence_var_external_call',
 'objective_sense': 'minimize',
 'public_api_primitives': ['sequence_var', 'external_call']},
    extra={'modeling_form': 'sequence_var assignment permutation with external_call quadratic cost evaluator',
 'objective_sense': 'minimize',
 'optagent_modeling': {'constraints': ['sequence_var enforces a one-to-one facility-location '
                                       'assignment'],
                       'data_mapping': 'Read QAPLIB flow and distance matrices.',
                       'decision_variables': ['one sequence_var assignment of size 40; '
                                              'assignment[i] is the location chosen for facility '
                                              'i'],
                       'external_callback': 'qap_cost(ctx) computes sum(flow[i][j] * '
                                            'distance[assignment[i]][assignment[j]]) over all '
                                            'facility pairs.',
                       'objective': 'builder.minimize(builder.external_call(qap_cost, '
                                    "name='assignment_cost'), name='assignment_cost')",
                       'solver_routes': ['solve with GaConfig',
                                         'solve with TabuConfig',
                                         'solve with AlnsConfig']},
 'optagent_primitives': ['sequence_var', 'external_call'],
 'recommended_evaluation': {'budgets_seconds': {'calibration': 120, 'full': 600, 'smoke': 10},
                            'primary_route': 'solve(..., strategy=GaConfig/TabuConfig/AlnsConfig); '
                                             'not a natural pure MILP benchmark for OptAgent '
                                             'strategies',
                            'strategy_candidates': ['ga', 'tabu', 'alns'],
                            'target_metrics': ['gap_to_optimum',
                                               'time_to_best',
                                               'external_call_count',
                                               'cache_hit_rate']}},
)

CASES = (LIPA40A,)
