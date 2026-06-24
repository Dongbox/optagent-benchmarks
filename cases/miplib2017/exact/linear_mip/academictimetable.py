from __future__ import annotations

from benchmarks.cases.miplib2017.exact.linear_mip._common import MipCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE

CASE_MODULE = __name__

ACADEMICTIMETABLESMALL = MipCase(
    benchmark_id='miplib2017_academictimetablesmall',
    source='MIPLIB 2017 benchmark-v2',
    problem_type='exact',
    instance_type='linear_mip',
    instance='academictimetablesmall',
    family='exact_linear_mip',
    tier='full',
    compare_key='miplib2017/exact/linear_mip/academictimetablesmall',
    series_key='miplib2017/exact/linear_mip/academictimetablesmall/mps_linear_mp',
    size={'binaries': 28926,
 'constraints': 23294,
 'continuous': 0,
 'integers': 0,
 'nonzeros': 268350,
 'variables': 28926},
    data={'benchmark_list_url': 'https://miplib.zib.de/downloads/benchmark-v2.test',
 'instance_archive_url': 'https://miplib.zib.de/downloads/benchmark.zip',
 'instance_detail_url': 'https://miplib.zib.de/instance_details_academictimetablesmall.html',
 'solution_url': 'https://miplib.zib.de/downloads/miplib2017-v36.solu'},
    reference={'download_page_url': 'https://miplib.zib.de/download.html',
 'miplib_status': 'easy',
 'notes': 'Use as MP/exact-backend baseline, not as the primary GA/ALNS benchmark family.',
 'objective': 0.0,
 'source_url': 'https://miplib.zib.de/downloads/miplib2017-v36.solu',
 'status': 'opt',
 'tags': ['benchmark',
          'binary',
          'decomposition',
          'benchmark_suitable',
          'aggregations',
          'precedence',
          'variable_bound',
          'set_partitioning',
          'set_packing',
          'cardinality',
          'invariant_knapsack',
          'equation_knapsack',
          'binpacking',
          'knapsack'],
 'value_kind': 'optimal'},
    problem_description=('MIPLIB 2017 benchmark instance academictimetablesmall: linear mixed-integer program with 28926 '
 'variables, 23294 constraints, and tags [benchmark, binary, decomposition, benchmark_suitable, '
 'aggregations, precedence, variable_bound, set_partitioning, set_packing, cardinality, '
 'invariant_knapsack, equation_knapsack, binpacking, knapsack]. It is included as an exact MP/MPS '
 'backend benchmark rather than a primary GA/ALNS search case.'),
    case_module=CASE_MODULE,
    modeling_notes={'model_style': 'mps_linear_mp',
 'objective_sense': 'minimize',
 'public_api_primitives': ['int_var', 'bool_var', 'float_var', 'linear_constraints']},
    extra={'modeling_form': 'MPS/MP rows and columns for exact backend evaluation',
 'objective_sense': 'minimize',
 'optagent_modeling': {'constraints': ['one linear constraint per MPS row using the parsed row '
                                       'sense and right-hand side'],
                       'data_mapping': 'Load the MPS instance through the benchmark MPS/MP loader '
                                       'and preserve row sense, bounds, integrality, and objective '
                                       'coefficients.',
                       'decision_variables': ['bool_var for binary columns',
                                              'int_var for general integer columns',
                                              'float_var for continuous columns'],
                       'objective': 'builder.minimize(parsed_linear_objective, '
                                    "name='mip_objective') unless the source sense states maximize",
                       'solver_routes': ["solve_milp with backend='optx'",
                                         "optional solve_milp with backend='mathopt_mp'"]},
 'optagent_primitives': ['int_var', 'bool_var', 'float_var', 'linear_constraints'],
 'recommended_evaluation': {'budgets_seconds': {'calibration': 300, 'full': 3600, 'smoke': 30},
                            'primary_route': "solve_milp(..., backend='optx') and optional "
                                             'external mathopt_mp comparison',
                            'strategy_candidates': ['exact_optx'],
                            'target_metrics': ['optimality_match',
                                               'time_to_optimal_or_gap',
                                               'native_backend_status']}},
)

CASES = (ACADEMICTIMETABLESMALL,)
