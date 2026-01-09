# Final Benchmark Report

## Configuration
- Circuit: GHZ (4 qubits)
- Observables: 27
- Shot grid: [100, 500, 1000, 5000]
- Replicates: 20
- Epsilon: 0.01, Delta: 0.05

## Protocol Summaries (max N)
- direct_naive: {'mean_se': np.float64(0.059907566496439885), 'max_se': np.float64(0.07371990106478842), 'median_se': np.float64(0.07353873901897406), 'mean_abs_error': np.float64(0.04928928928928933), 'max_abs_error': np.float64(0.24324324324324326)}
- direct_grouped: {'mean_se': np.float64(0.03644331299092116), 'max_se': np.float64(0.044766148103584515), 'median_se': np.float64(0.04473713023477575), 'mean_abs_error': np.float64(0.02740740740740745), 'max_abs_error': np.float64(0.116)}
- direct_optimized: {'mean_se': np.float64(0.03578104254132738), 'max_se': np.float64(0.05652334189442215), 'median_se': np.float64(0.03989582064456459), 'mean_abs_error': np.float64(0.029779231049112953), 'max_abs_error': np.float64(0.14149443561208266)}
- classical_shadows_v0: {'mean_se': np.float64(0.05691220322560587), 'max_se': np.float64(0.15312539590805962), 'median_se': np.float64(0.042727412658308275), 'mean_abs_error': np.float64(0.047346296296296296), 'max_abs_error': np.float64(0.4742000000000002)}

## Task Outputs
- task2_direct_naive: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based'}
- task2_direct_grouped: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based'}
- task2_direct_optimized: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based'}
- task2_classical_shadows_v0: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based'}
- task4_dominance_summary: {'crossover_n': None, 'a_dominates_at': [], 'b_dominates_at': [100, 500, 1000, 5000], 'always_a_better': False, 'always_b_better': True, 'blocking_observables': ['obs_b3f1d11a', 'obs_c022ce9f', 'obs_181f3284', 'obs_bf1aec14', 'obs_f20b99ef', 'obs_c5123b46', 'obs_a73aa0db', 'obs_879308b3', 'obs_06f81318', 'obs_d6966bab', 'obs_707b5670', 'obs_d68fe337', 'obs_1406fc7f'], 'metrics_a': {100: np.float64(0.3276481481481482), 500: np.float64(0.14354074074074075), 1000: np.float64(0.10217407407407408), 5000: np.float64(0.047346296296296296)}, 'metrics_b': {100: np.float64(0.19592592592592598), 500: np.float64(0.08755555555555558), 1000: np.float64(0.068962962962963), 5000: np.float64(0.02740740740740745)}, 'metric_used': 'mean_error'}
- task5_pilot_selection: {'pilot_n': 100, 'target_n': 5000, 'selection_accuracy': 0.6, 'regret': 0.003838460688985932, 'criterion_type': 'truth_based'}
- task8_direct_naive: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based', 'baseline_n_star': None}
- task8_direct_grouped: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based', 'baseline_n_star': None}
- task8_direct_optimized: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based', 'baseline_n_star': None}
- task8_classical_shadows_v0: {'epsilon': 0.01, 'delta': 0.05, 'criterion_type': 'truth_based', 'baseline_n_star': None}
- task7_direct_naive: {'epsilon': 0.01, 'delta': 0.05, 'baseline_noise_profile': 'ideal', 'failure_rate': 1.0}
- task7_direct_grouped: {'epsilon': 0.01, 'delta': 0.05, 'baseline_noise_profile': 'ideal', 'failure_rate': 1.0}
- task7_direct_optimized: {'epsilon': 0.01, 'delta': 0.05, 'baseline_noise_profile': 'ideal', 'failure_rate': 1.0}
- task7_classical_shadows_v0: {'epsilon': 0.01, 'delta': 0.05, 'baseline_noise_profile': 'ideal', 'failure_rate': 1.0}

## Conclusions
- Run ID: publication_benchmark_364c6ed4 with 4 protocols
- Ground truth computed: True
- Classical shadows v0 is benchmarked against direct baselines under identical budgets.
- Task 7 noise sensitivity is evaluated across canonical profiles.
- Artifacts include long-form, summary, plots, and provenance manifest in output_dir.