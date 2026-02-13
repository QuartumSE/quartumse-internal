"""Benchmark sweep orchestrator (Measurements Bible §9).

This module provides utilities for orchestrating benchmark sweeps
across protocols, circuits, shot budgets, and replicates.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import numpy as np

from ..io.long_form import LongFormResultBuilder, LongFormResultSet
from ..io.schemas import LongFormRow, RunManifest
from ..observables import ObservableSet
from ..protocols import Estimates, Protocol
from ..utils.provenance import (
    get_environment_lock,
    get_git_commit_hash,
    get_python_version,
    get_quartumse_version,
)


@dataclass
class SweepConfig:
    """Configuration for a benchmark sweep.

    Attributes:
        run_id: Unique identifier for this run.
        methodology_version: Version of the methodology.
        protocols: List of protocol instances to evaluate.
        circuits: List of (circuit_id, circuit) tuples.
        observable_sets: List of (obs_set_id, ObservableSet) tuples.
        n_grid: Shot budget grid.
        n_replicates: Number of replicates per configuration.
        noise_profiles: List of noise profile IDs.
        seeds: Seed configuration.
        tasks: List of task IDs to run.
    """

    run_id: str = field(default_factory=lambda: f"run_{uuid4().hex[:12]}")
    methodology_version: str = "3.0.0"
    protocols: list[Protocol] = field(default_factory=list)
    circuits: list[tuple[str, Any]] = field(default_factory=list)
    observable_sets: list[tuple[str, ObservableSet]] = field(default_factory=list)
    n_grid: list[int] = field(default_factory=lambda: [100, 500, 1000, 5000, 10000])
    n_replicates: int = 10
    noise_profiles: list[str] = field(default_factory=lambda: ["ideal"])
    seeds: dict[str, int] = field(default_factory=lambda: {"base": 42})
    seed_policy: str = "base_replicate_config"
    tasks: list[str] = field(default_factory=list)
    store_raw_shots: bool = True


@dataclass
class SweepProgress:
    """Progress tracking for a sweep.

    Attributes:
        total_configs: Total number of configurations.
        completed_configs: Number of completed configurations.
        current_protocol: Currently running protocol.
        current_circuit: Currently running circuit.
        current_n: Currently running shot budget.
        current_replicate: Currently running replicate.
        start_time: Sweep start time.
        errors: List of errors encountered.
    """

    total_configs: int = 0
    completed_configs: int = 0
    current_protocol: str = ""
    current_circuit: str = ""
    current_n: int = 0
    current_replicate: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def progress_fraction(self) -> float:
        """Fraction of sweep completed."""
        if self.total_configs == 0:
            return 0.0
        return self.completed_configs / self.total_configs

    @property
    def elapsed_seconds(self) -> float:
        """Elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


class SweepOrchestrator:
    """Orchestrator for running benchmark sweeps.

    Manages the execution of protocols across the sweep grid
    and collects results.
    """

    def __init__(
        self,
        config: SweepConfig,
        executor: Callable | None = None,
    ) -> None:
        """Initialize sweep orchestrator.

        Args:
            config: Sweep configuration.
            executor: Optional custom executor for running protocols.
        """
        self.config = config
        self.executor = executor or self._default_executor
        self.results = LongFormResultSet()
        self.progress = SweepProgress()
        self.raw_shot_records: list[dict] = []

    def _default_executor(
        self,
        protocol: Protocol,
        circuit: Any,
        observable_set: ObservableSet,
        n_shots: int,
        seed: int,
        noise_profile: str,
    ) -> Estimates:
        """Default protocol executor using physical measurement paths."""
        from qiskit import QuantumCircuit

        backend = self._resolve_backend(noise_profile)
        if circuit is None:
            circuit = QuantumCircuit(observable_set.n_qubits)

        return protocol.run(
            circuit=circuit,
            observable_set=observable_set,
            total_budget=n_shots,
            backend=backend,
            seed=seed,
        )

    def _resolve_backend(self, noise_profile: str) -> Any:
        """Resolve a backend sampler from a noise profile identifier."""
        from ..backends.sampler import IdealSampler, NoisySampler
        from ..noise.profiles import NoiseType, get_profile

        if noise_profile == "ideal":
            return IdealSampler()

        try:
            profile = get_profile(noise_profile)
        except KeyError:
            return NoisySampler(noise_profile_id=noise_profile)

        if profile.noise_type == NoiseType.READOUT_BITFLIP:
            return NoisySampler(
                noise_profile_id=profile.profile_id,
                readout_error=profile.parameters.get("p", 0.0),
            )
        if profile.noise_type == NoiseType.DEPOLARIZING:
            return NoisySampler(
                noise_profile_id=profile.profile_id,
                depol_1q=profile.parameters.get("p1", 0.0),
                depol_2q=profile.parameters.get("p2", 0.0),
            )

        return NoisySampler(noise_profile_id=profile.profile_id)

    def compute_total_configs(self) -> int:
        """Compute total number of configurations."""
        n_protocols = len(self.config.protocols)
        n_circuits = len(self.config.circuits)
        n_obs_sets = len(self.config.observable_sets)
        n_budgets = len(self.config.n_grid)
        n_replicates = self.config.n_replicates
        n_noise = len(self.config.noise_profiles)

        return n_protocols * n_circuits * n_obs_sets * n_budgets * n_replicates * n_noise

    def generate_seeds(self, replicate_id: int, config_id: int) -> dict[str, int]:
        """Generate reproducible seeds for a configuration.

        Args:
            replicate_id: Replicate number.
            config_id: Configuration index.

        Returns:
            Dict with seed_policy, seed_protocol, seed_acquire, seed_bootstrap.
        """
        base = self.config.seeds.get("base", 42)
        rng = np.random.default_rng(base + replicate_id * 1000 + config_id)

        return {
            "seed_policy": self.config.seed_policy,
            "seed_protocol": int(rng.integers(0, 2**31)),
            "seed_acquire": int(rng.integers(0, 2**31)),
            "seed_bootstrap": int(rng.integers(0, 2**31)),
        }

    def run(
        self,
        progress_callback: Callable[[SweepProgress], None] | None = None,
    ) -> LongFormResultSet:
        """Run the benchmark sweep.

        Args:
            progress_callback: Optional callback for progress updates.

        Returns:
            LongFormResultSet with all results.
        """
        self.progress = SweepProgress(
            total_configs=self.compute_total_configs(),
            start_time=datetime.now(),
        )

        config_id = 0

        for protocol in self.config.protocols:
            self.progress.current_protocol = protocol.protocol_id

            for circuit_id, circuit in self.config.circuits:
                self.progress.current_circuit = circuit_id

                for obs_set_id, observable_set in self.config.observable_sets:
                    for n in self.config.n_grid:
                        self.progress.current_n = n

                        for noise_profile in self.config.noise_profiles:
                            for rep in range(self.config.n_replicates):
                                self.progress.current_replicate = rep

                                try:
                                    seeds = self.generate_seeds(rep, config_id)

                                    estimates = self.executor(
                                        protocol=protocol,
                                        circuit=circuit,
                                        observable_set=observable_set,
                                        n_shots=n,
                                        seed=seeds["seed_protocol"],
                                        noise_profile=noise_profile,
                                    )

                                    # Convert to LongFormRows
                                    rows = self._estimates_to_rows(
                                        estimates=estimates,
                                        circuit_id=circuit_id,
                                        obs_set_id=obs_set_id,
                                        observable_set=observable_set,
                                        n=n,
                                        replicate_id=rep,
                                        noise_profile=noise_profile,
                                        seeds=seeds,
                                    )
                                    self.results.add_many(rows)

                                    # Collect raw shot data
                                    if self.config.store_raw_shots and estimates.raw_chunks:
                                        self._collect_raw_shots(
                                            estimates=estimates,
                                            circuit_id=circuit_id,
                                            n=n,
                                            replicate_id=rep,
                                            noise_profile=noise_profile,
                                        )

                                except Exception as e:
                                    self.progress.errors.append(
                                        {
                                            "protocol": protocol.protocol_id,
                                            "circuit": circuit_id,
                                            "n": n,
                                            "replicate": rep,
                                            "error": str(e),
                                        }
                                    )

                                self.progress.completed_configs += 1
                                config_id += 1

                                if progress_callback:
                                    progress_callback(self.progress)

        return self.results

    def _estimates_to_rows(
        self,
        estimates: Estimates,
        circuit_id: str,
        obs_set_id: str,
        observable_set: ObservableSet,
        n: int,
        replicate_id: int,
        noise_profile: str,
        seeds: dict[str, int],
    ) -> list[LongFormRow]:
        """Convert Estimates to LongFormRows."""
        rows = []
        builder = LongFormResultBuilder()

        for est in estimates.estimates:
            obs = observable_set.get_by_id(est.observable_id)

            row = (
                builder.reset()
                .with_run_id(self.config.run_id)
                .with_methodology_version(self.config.methodology_version)
                .with_circuit(circuit_id, n_qubits=observable_set.n_qubits)
                .with_observable(
                    observable_id=est.observable_id,
                    observable_type=obs.observable_type.value,
                    locality=obs.locality,
                    coefficient=obs.coefficient,
                    observable_set_id=obs_set_id,
                    group_id=obs.group_id,
                    M_total=len(observable_set),
                )
                .with_protocol(estimates.protocol_id, estimates.protocol_version)
                .with_backend("simulator", noise_profile_id=noise_profile)
                .with_replicate(replicate_id)
                .with_seeds(
                    seed_policy=seeds["seed_policy"],
                    seed_protocol=seeds["seed_protocol"],
                    seed_acquire=seeds["seed_acquire"],
                    seed_bootstrap=seeds.get("seed_bootstrap"),
                )
                .with_budget(N_total=n, n_settings=est.n_settings)
                .with_estimate(
                    estimate=est.estimate,
                    se=est.se,
                    ci_low=est.ci.ci_low if est.ci else None,
                    ci_high=est.ci.ci_high if est.ci else None,
                )
                .build()
            )
            rows.append(row)

        return rows

    def _collect_raw_shots(
        self,
        estimates: Estimates,
        circuit_id: str,
        n: int,
        replicate_id: int,
        noise_profile: str,
    ) -> None:
        """Extract raw shot data from estimates and append to raw_shot_records."""
        protocol_id = estimates.protocol_id or ""
        for chunk in estimates.raw_chunks:
            if chunk.bitstrings:
                for setting_id, bitstring_list in chunk.bitstrings.items():
                    self.raw_shot_records.append(
                        {
                            "protocol_id": protocol_id,
                            "circuit_id": circuit_id,
                            "N_total": n,
                            "replicate_id": replicate_id,
                            "noise_profile": noise_profile,
                            "setting_id": setting_id,
                            "bitstrings": json.dumps(bitstring_list),
                            "measurement_bases": None,
                        }
                    )
            elif chunk.outcomes is not None:
                # Array-based format (e.g., shadows)
                unique_settings = (
                    np.unique(chunk.setting_indices)
                    if chunk.setting_indices is not None
                    else [0]
                )
                for si in unique_settings:
                    if chunk.setting_indices is not None:
                        mask = chunk.setting_indices == si
                        outcomes = chunk.outcomes[mask]
                        bases = chunk.basis_choices[mask] if chunk.basis_choices is not None else None
                    else:
                        outcomes = chunk.outcomes
                        bases = chunk.basis_choices

                    self.raw_shot_records.append(
                        {
                            "protocol_id": protocol_id,
                            "circuit_id": circuit_id,
                            "N_total": n,
                            "replicate_id": replicate_id,
                            "noise_profile": noise_profile,
                            "setting_id": str(si),
                            "bitstrings": json.dumps(outcomes.tolist()),
                            "measurement_bases": json.dumps(bases.tolist())
                            if bases is not None
                            else None,
                        }
                    )

    def create_manifest(self) -> RunManifest:
        """Create run manifest for this sweep."""
        return RunManifest(
            run_id=self.config.run_id,
            methodology_version=self.config.methodology_version,
            created_at=self.progress.start_time,
            git_commit_hash=get_git_commit_hash(),
            quartumse_version=get_quartumse_version(),
            python_version=get_python_version(),
            environment_lock=get_environment_lock(),
            circuits=[c[0] for c in self.config.circuits],
            observable_sets=[o[0] for o in self.config.observable_sets],
            protocols=[p.protocol_id for p in self.config.protocols],
            N_grid=self.config.n_grid,
            n_replicates=self.config.n_replicates,
            noise_profiles=self.config.noise_profiles,
            status="completed" if not self.progress.errors else "partial_success",
            completed_at=datetime.now(),
            config={
                "seeds": self.config.seeds,
                "seed_policy": self.config.seed_policy,
                "tasks": self.config.tasks,
            },
        )


def generate_n_grid(
    n_min: int = 100,
    n_max: int = 100000,
    ratio: float = 2.0,
) -> list[int]:
    """Generate geometric shot budget grid.

    Args:
        n_min: Minimum shot count.
        n_max: Maximum shot count.
        ratio: Geometric ratio between consecutive values.

    Returns:
        List of shot counts.
    """
    grid = []
    n = n_min
    while n <= n_max:
        grid.append(int(n))
        n *= ratio
    return grid
