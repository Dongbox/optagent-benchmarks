from __future__ import annotations

from benchmarks.cases.tsplib.routing.tsp._common import TspCase, SOURCE, SOURCE_KEY, PROBLEM_TYPE, INSTANCE_TYPE, FAMILY, MODEL_STYLE, BLACKBOX_TSP_MODEL_STYLE, GRAPH_TSP_MODEL_STYLE, DEFAULT_TSP_MODEL_STYLES, SUPPORTED_TSP_MODEL_STYLES

CASE_MODULE = __name__

A280 = TspCase(
    benchmark_id='tsplib_a280',
    source='TSPLIB95',
    problem_type='routing',
    instance_type='tsp',
    instance='a280',
    family='sequence_blackbox_tsp',
    tier='full',
    compare_key='tsplib/routing/tsp/a280',
    series_key='tsplib/routing/tsp/a280/sequence_var_external_call',
    size={'nodes': 280},
    data={'instance_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/a280.tsp.gz',
 'mirror_urls': ['https://raw.githubusercontent.com/mastqe/tsplib/master/a280.tsp'],
 'solution_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html'},
    reference={'notes': 'TSPLIB STSP page states all symmetric TSP instances are solved to optimality.',
 'objective': 2579,
 'source_url': 'https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html',
 'status': 'optimal',
 'value_kind': 'optimal'},
    problem_description=('TSPLIB symmetric TSP instance a280: find the shortest Hamiltonian cycle over 280 cities using '
 'the instance distance metric. The benchmark is a blackbox sequence optimization case with a '
 'published optimal tour length.'),
    case_module=CASE_MODULE,
    modeling_notes={'model_style': 'sequence_var_external_call',
 'objective_sense': 'minimize',
 'public_api_primitives': ['sequence_var', 'external_call']},
    extra={'modeling_form': 'sequence_var route with external_call distance evaluator',
 'objective_sense': 'minimize',
 'optagent_modeling': {'constraints': ['sequence_var represents a permutation, so no separate '
                                       'all-different constraint is required'],
                       'data_mapping': 'Read TSPLIB coordinates or explicit distances and '
                                       'implement the documented TSPLIB distance metric in a '
                                       'callback.',
                       'decision_variables': ['one sequence_var tour of size 280; the sequence is '
                                              'the city visit order'],
                       'external_callback': 'route_cost(ctx) reads ctx.value(tour), sums '
                                            'consecutive arc costs, and adds the return-to-start '
                                            'arc.',
                       'objective': 'builder.minimize(builder.external_call(route_cost, '
                                    "name='tour_length'), name='tour_length')",
                       'solver_routes': ['solve with GaConfig',
                                         'solve with TabuConfig',
                                         'solve with AlnsConfig']},
 'optagent_primitives': ['sequence_var', 'external_call'],
 'recommended_evaluation': {'budgets_seconds': {'calibration': 60, 'full': 300, 'smoke': 10},
                            'primary_route': 'solve(..., strategy=GaConfig/TabuConfig/AlnsConfig); '
                                             'exact route only for small diagnostic comparisons',
                            'strategy_candidates': ['ga', 'tabu', 'alns'],
                            'target_metrics': ['gap_to_optimum',
                                               'time_to_best',
                                               'external_call_count',
                                               'cache_hit_rate']}},
)

CASES = (A280,)
