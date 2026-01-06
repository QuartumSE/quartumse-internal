"""Benchmark tasks for protocol evaluation (Measurements Bible §8).

This package provides implementations of the 8 benchmark tasks defined
in the Measurements Bible:

Task 1: Worst-case guarantee (simultaneous; required)
Task 2: Average/weighted accuracy target
Task 3: Fixed-budget distribution (required)
Task 4: Dominance and crossover (required)
Task 5: Pilot-based selection (meta-protocol; required)
Task 6: Bias-variance decomposition (required in simulation)
Task 7: Noise sensitivity and robustness
Task 8: Adaptive protocol efficiency

Usage:
    from quartumse.tasks import (
        WorstCaseTask,
        FixedBudgetDistributionTask,
        DominanceTask,
        BiasVarianceTask,
        TaskConfig,
        TaskType,
        SweepOrchestrator,
        SweepConfig,
    )

    # Configure a task
    config = TaskConfig(
        task_id="task1_epsilon01",
        task_type=TaskType.WORST_CASE,
        epsilon=0.01,
        delta=0.05,
    )

    # Create and evaluate task
    task = WorstCaseTask(config)
    output = task.evaluate(long_form_results, truth_values)

    # Run a sweep
    sweep_config = SweepConfig(
        protocols=[protocol1, protocol2],
        circuits=[(circuit_id, circuit)],
        observable_sets=[(obs_set_id, obs_set)],
        n_grid=[100, 500, 1000, 5000],
    )
    orchestrator = SweepOrchestrator(sweep_config)
    results = orchestrator.run()
"""

from .base import (
    BenchmarkTask,
    CriterionType,
    TaskConfig,
    TaskOutput,
    TaskType,
    compute_attainment,
    group_results_by_n,
    group_results_by_replicate,
)
from .sweep import (
    SweepConfig,
    SweepOrchestrator,
    SweepProgress,
    generate_n_grid,
)
from .task1_worstcase import WorstCaseTask
from .task3_distribution import DistributionStats, FixedBudgetDistributionTask
from .task4_dominance import DominanceTask
from .task6_biasvar import BiasVarianceStats, BiasVarianceTask

__all__ = [
    # Base classes
    "BenchmarkTask",
    "TaskConfig",
    "TaskOutput",
    "TaskType",
    "CriterionType",
    # Utilities
    "compute_attainment",
    "group_results_by_n",
    "group_results_by_replicate",
    # Sweep orchestration
    "SweepConfig",
    "SweepOrchestrator",
    "SweepProgress",
    "generate_n_grid",
    # Task implementations
    "WorstCaseTask",
    "FixedBudgetDistributionTask",
    "DominanceTask",
    "BiasVarianceTask",
    # Data classes
    "DistributionStats",
    "BiasVarianceStats",
]
