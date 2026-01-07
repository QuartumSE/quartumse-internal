from __future__ import annotations

from quartumse.io.schemas import LongFormRow
from quartumse.tasks import TaskConfig, TaskType
from quartumse.tasks.task2_average_target import AverageTargetTask
from quartumse.tasks.task5_pilot_selection import PilotSelectionTask
from quartumse.tasks.task7_noise_sensitivity import NoiseSensitivityTask
from quartumse.tasks.task8_adaptive_efficiency import AdaptiveEfficiencyTask


def make_row(
    *,
    protocol_id: str,
    observable_id: str,
    replicate_id: int,
    N_total: int,
    se: float,
    estimate: float = 0.0,
    noise_profile_id: str = "ideal",
    n_settings: int = 1,
    time_classical_s: float | None = None,
) -> LongFormRow:
    return LongFormRow(
        run_id="run",
        methodology_version="3.0.0",
        circuit_id="circuit",
        observable_set_id="obs_set",
        observable_id=observable_id,
        protocol_id=protocol_id,
        protocol_version="v1",
        backend_id="backend",
        noise_profile_id=noise_profile_id,
        replicate_id=replicate_id,
        seed_protocol=1,
        seed_acquire=2,
        seed_bootstrap=3,
        n_qubits=2,
        circuit_depth=1,
        twoq_gate_count=0,
        observable_type="pauli_string",
        locality=1,
        coefficient=1.0,
        group_id=None,
        M_total=2,
        N_total=N_total,
        n_settings=n_settings,
        time_quantum_s=None,
        time_classical_s=time_classical_s,
        memory_bytes=None,
        estimate=estimate,
        se=se,
        ci_low_raw=None,
        ci_high_raw=None,
        ci_low=None,
        ci_high=None,
        ci_method_id=None,
        confidence_level=0.95,
        truth_value=None,
        truth_se=None,
        truth_mode=None,
        abs_err=None,
        sq_err=None,
        metadata={},
    )


def test_average_target_task_n_star() -> None:
    config = TaskConfig(
        task_id="task2_avg",
        task_type=TaskType.AVERAGE_TARGET,
        epsilon=0.1,
        delta=0.0,
    )
    task = AverageTargetTask(config)
    rows = []
    for replicate_id in [0, 1]:
        rows.extend(
            [
                make_row(
                    protocol_id="proto",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=100,
                    se=0.2,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=100,
                    se=0.2,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=0.05,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=0.05,
                ),
            ]
        )

    output = task.evaluate(rows)

    assert output.n_star == 200
    assert output.details["success_fraction_by_n"][100] == 0.0
    assert output.details["success_fraction_by_n"][200] == 1.0


def test_pilot_selection_accuracy_and_regret() -> None:
    config = TaskConfig(
        task_id="task5_pilot",
        task_type=TaskType.PILOT_SELECTION,
        epsilon=0.1,
        delta=0.0,
        additional_params={"pilot_n": 50, "target_n": 200},
    )
    task = PilotSelectionTask(config)
    rows = []

    for replicate_id, pilot_a, pilot_b, target_a, target_b in [
        (0, 0.1, 0.2, 0.05, 0.1),
        (1, 0.2, 0.1, 0.1, 0.05),
    ]:
        rows.extend(
            [
                make_row(
                    protocol_id="A",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=50,
                    se=pilot_a,
                ),
                make_row(
                    protocol_id="A",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=50,
                    se=pilot_a,
                ),
                make_row(
                    protocol_id="B",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=50,
                    se=pilot_b,
                ),
                make_row(
                    protocol_id="B",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=50,
                    se=pilot_b,
                ),
                make_row(
                    protocol_id="A",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=target_a,
                ),
                make_row(
                    protocol_id="A",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=target_a,
                ),
                make_row(
                    protocol_id="B",
                    observable_id="o1",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=target_b,
                ),
                make_row(
                    protocol_id="B",
                    observable_id="o2",
                    replicate_id=replicate_id,
                    N_total=200,
                    se=target_b,
                ),
            ]
        )

    output = task.evaluate(rows)

    assert output.selection_accuracy == 1.0
    assert output.regret == 0.0
    assert output.metrics["selection_accuracy"] == 1.0


def test_noise_sensitivity_n_star_by_noise() -> None:
    config = TaskConfig(
        task_id="task7_noise",
        task_type=TaskType.NOISE_SENSITIVITY,
        epsilon=0.1,
        delta=0.0,
    )
    task = NoiseSensitivityTask(config)
    rows = []

    for noise_profile, n100_se, n200_se in [
        ("ideal", 0.05, 0.04),
        ("noisy", 0.2, 0.08),
    ]:
        rows.extend(
            [
                make_row(
                    protocol_id="proto",
                    observable_id="o1",
                    replicate_id=0,
                    N_total=100,
                    se=n100_se,
                    noise_profile_id=noise_profile,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o2",
                    replicate_id=0,
                    N_total=100,
                    se=n100_se,
                    noise_profile_id=noise_profile,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o1",
                    replicate_id=0,
                    N_total=200,
                    se=n200_se,
                    noise_profile_id=noise_profile,
                ),
                make_row(
                    protocol_id="proto",
                    observable_id="o2",
                    replicate_id=0,
                    N_total=200,
                    se=n200_se,
                    noise_profile_id=noise_profile,
                ),
            ]
        )

    output = task.evaluate(rows)

    assert output.details["n_star_by_noise"]["ideal"] == 100
    assert output.details["n_star_by_noise"]["noisy"] == 200
    assert output.metrics["failure_rate"] == 0.0


def test_adaptive_efficiency_n_star() -> None:
    config = TaskConfig(
        task_id="task8_adaptive",
        task_type=TaskType.ADAPTIVE_EFFICIENCY,
        epsilon=0.1,
        delta=0.0,
    )
    task = AdaptiveEfficiencyTask(config)
    rows = []

    for N_total, se in [(100, 0.2), (200, 0.05)]:
        rows.extend(
            [
                make_row(
                    protocol_id="adaptive",
                    observable_id="o1",
                    replicate_id=0,
                    N_total=N_total,
                    se=se,
                    n_settings=2,
                    time_classical_s=0.5,
                ),
                make_row(
                    protocol_id="adaptive",
                    observable_id="o2",
                    replicate_id=0,
                    N_total=N_total,
                    se=se,
                    n_settings=2,
                    time_classical_s=0.5,
                ),
            ]
        )

    output = task.evaluate(rows)

    assert output.n_star == 200
    assert output.details["efficiency_by_n"][200]["mean_n_settings"] == 2.0
