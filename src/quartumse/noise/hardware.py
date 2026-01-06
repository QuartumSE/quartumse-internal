"""Hardware execution metadata and tracking (Measurements Bible §9.5).

This module provides utilities for tracking hardware-specific metadata
required for interpreting benchmark results from real quantum devices.

Required metadata:
- Queue time and scheduling
- Calibration drift detection
- Connectivity and compilation
- Failure handling and partial data
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Status of a hardware job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobMetadata:
    """Metadata for a single hardware job.

    Attributes:
        job_id: Unique job identifier from the backend.
        backend_id: Backend identifier.
        status: Job execution status.
        submitted_at: Job submission timestamp.
        started_at: Job start timestamp (when execution began).
        completed_at: Job completion timestamp.
        queue_time_s: Time spent in queue (seconds).
        execution_time_s: Actual execution time (seconds).
        n_shots: Number of shots requested.
        n_circuits: Number of circuits in the job.
        error_message: Error message if failed.
        metadata: Additional backend-specific metadata.
    """

    job_id: str
    backend_id: str
    status: JobStatus = JobStatus.QUEUED
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    queue_time_s: float | None = None
    execution_time_s: float | None = None
    n_shots: int = 0
    n_circuits: int = 0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def compute_timings(self) -> None:
        """Compute timing fields from timestamps."""
        if self.submitted_at and self.started_at:
            self.queue_time_s = (self.started_at - self.submitted_at).total_seconds()
        if self.started_at and self.completed_at:
            self.execution_time_s = (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "backend_id": self.backend_id,
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "queue_time_s": self.queue_time_s,
            "execution_time_s": self.execution_time_s,
            "n_shots": self.n_shots,
            "n_circuits": self.n_circuits,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class CalibrationData:
    """Calibration data snapshot from a backend.

    Attributes:
        backend_id: Backend identifier.
        timestamp: When calibration was retrieved.
        t1_times: T1 times per qubit (microseconds).
        t2_times: T2 times per qubit (microseconds).
        readout_errors: Readout error rates per qubit.
        gate_errors_1q: Single-qubit gate errors per qubit.
        gate_errors_2q: Two-qubit gate errors per qubit pair.
        coupling_map: Qubit connectivity.
        metadata: Additional calibration metadata.
    """

    backend_id: str
    timestamp: datetime
    t1_times: dict[int, float] = field(default_factory=dict)
    t2_times: dict[int, float] = field(default_factory=dict)
    readout_errors: dict[int, float] = field(default_factory=dict)
    gate_errors_1q: dict[int, float] = field(default_factory=dict)
    gate_errors_2q: dict[tuple[int, int], float] = field(default_factory=dict)
    coupling_map: list[tuple[int, int]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def mean_t1(self) -> float:
        """Mean T1 time across qubits."""
        if not self.t1_times:
            return 0.0
        return sum(self.t1_times.values()) / len(self.t1_times)

    def mean_t2(self) -> float:
        """Mean T2 time across qubits."""
        if not self.t2_times:
            return 0.0
        return sum(self.t2_times.values()) / len(self.t2_times)

    def mean_readout_error(self) -> float:
        """Mean readout error across qubits."""
        if not self.readout_errors:
            return 0.0
        return sum(self.readout_errors.values()) / len(self.readout_errors)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backend_id": self.backend_id,
            "timestamp": self.timestamp.isoformat(),
            "t1_times": self.t1_times,
            "t2_times": self.t2_times,
            "readout_errors": self.readout_errors,
            "gate_errors_1q": self.gate_errors_1q,
            "gate_errors_2q": {
                f"{q1}-{q2}": e for (q1, q2), e in self.gate_errors_2q.items()
            },
            "coupling_map": self.coupling_map,
            "metadata": self.metadata,
        }


@dataclass
class CompilationInfo:
    """Information about circuit compilation.

    Attributes:
        original_depth: Circuit depth before compilation.
        compiled_depth: Circuit depth after compilation.
        original_2q_count: 2-qubit gate count before compilation.
        compiled_2q_count: 2-qubit gate count after compilation.
        qubit_mapping: Logical to physical qubit mapping.
        optimization_level: Optimization level used.
        basis_gates: Basis gates used.
        metadata: Additional compilation metadata.
    """

    original_depth: int = 0
    compiled_depth: int = 0
    original_2q_count: int = 0
    compiled_2q_count: int = 0
    qubit_mapping: dict[int, int] = field(default_factory=dict)
    optimization_level: int = 1
    basis_gates: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def depth_overhead(self) -> float:
        """Ratio of compiled to original depth."""
        if self.original_depth == 0:
            return 1.0
        return self.compiled_depth / self.original_depth

    @property
    def gate_overhead(self) -> float:
        """Ratio of compiled to original 2Q gate count."""
        if self.original_2q_count == 0:
            return 1.0
        return self.compiled_2q_count / self.original_2q_count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_depth": self.original_depth,
            "compiled_depth": self.compiled_depth,
            "original_2q_count": self.original_2q_count,
            "compiled_2q_count": self.compiled_2q_count,
            "qubit_mapping": self.qubit_mapping,
            "optimization_level": self.optimization_level,
            "basis_gates": self.basis_gates,
            "depth_overhead": self.depth_overhead,
            "gate_overhead": self.gate_overhead,
            "metadata": self.metadata,
        }


@dataclass
class HardwareSession:
    """Tracks a hardware execution session.

    A session groups related jobs and tracks calibration drift.

    Attributes:
        session_id: Unique session identifier.
        backend_id: Backend identifier.
        start_time: Session start time.
        end_time: Session end time.
        calibration_before: Calibration at session start.
        calibration_after: Calibration at session end.
        jobs: List of jobs in this session.
        max_batch_duration_s: Maximum allowed batch duration.
        drift_detected: Whether calibration drift was detected.
    """

    session_id: str
    backend_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    calibration_before: CalibrationData | None = None
    calibration_after: CalibrationData | None = None
    jobs: list[JobMetadata] = field(default_factory=list)
    max_batch_duration_s: float = 3600.0  # 1 hour default
    drift_detected: bool = False

    def add_job(self, job: JobMetadata) -> None:
        """Add a job to this session."""
        self.jobs.append(job)

    def close(self, calibration_after: CalibrationData | None = None) -> None:
        """Close the session and check for drift."""
        self.end_time = datetime.now()
        self.calibration_after = calibration_after

        # Check for drift
        self.drift_detected = self._check_drift()

    def _check_drift(self) -> bool:
        """Check if calibration drifted during session."""
        if not self.calibration_before or not self.calibration_after:
            return False

        # Check T1/T2 drift (>20% change indicates drift)
        t1_before = self.calibration_before.mean_t1()
        t1_after = self.calibration_after.mean_t1()
        if t1_before > 0 and abs(t1_after - t1_before) / t1_before > 0.2:
            return True

        t2_before = self.calibration_before.mean_t2()
        t2_after = self.calibration_after.mean_t2()
        if t2_before > 0 and abs(t2_after - t2_before) / t2_before > 0.2:
            return True

        # Check readout error drift
        ro_before = self.calibration_before.mean_readout_error()
        ro_after = self.calibration_after.mean_readout_error()
        if ro_before > 0 and abs(ro_after - ro_before) / ro_before > 0.5:
            return True

        return False

    @property
    def duration_s(self) -> float:
        """Session duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def exceeds_max_duration(self) -> bool:
        """Whether session exceeds maximum duration."""
        return self.duration_s > self.max_batch_duration_s

    @property
    def total_queue_time_s(self) -> float:
        """Total queue time across all jobs."""
        return sum(j.queue_time_s or 0 for j in self.jobs)

    @property
    def total_execution_time_s(self) -> float:
        """Total execution time across all jobs."""
        return sum(j.execution_time_s or 0 for j in self.jobs)

    @property
    def success_rate(self) -> float:
        """Fraction of successful jobs."""
        if not self.jobs:
            return 0.0
        successful = sum(
            1 for j in self.jobs if j.status in (JobStatus.SUCCESS, JobStatus.PARTIAL_SUCCESS)
        )
        return successful / len(self.jobs)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "backend_id": self.backend_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_s": self.duration_s,
            "n_jobs": len(self.jobs),
            "success_rate": self.success_rate,
            "total_queue_time_s": self.total_queue_time_s,
            "total_execution_time_s": self.total_execution_time_s,
            "drift_detected": self.drift_detected,
            "exceeds_max_duration": self.exceeds_max_duration,
            "calibration_before": self.calibration_before.to_dict() if self.calibration_before else None,
            "calibration_after": self.calibration_after.to_dict() if self.calibration_after else None,
            "jobs": [j.to_dict() for j in self.jobs],
        }


class HardwareTracker:
    """Tracks hardware execution across sessions.

    Provides utilities for managing hardware sessions, tracking
    calibration drift, and aggregating job statistics.
    """

    def __init__(self) -> None:
        """Initialize tracker."""
        self.sessions: dict[str, HardwareSession] = {}
        self.current_session: HardwareSession | None = None

    def start_session(
        self,
        session_id: str,
        backend_id: str,
        calibration: CalibrationData | None = None,
        max_batch_duration_s: float = 3600.0,
    ) -> HardwareSession:
        """Start a new hardware session.

        Args:
            session_id: Unique session identifier.
            backend_id: Backend identifier.
            calibration: Initial calibration data.
            max_batch_duration_s: Maximum batch duration.

        Returns:
            New HardwareSession.
        """
        session = HardwareSession(
            session_id=session_id,
            backend_id=backend_id,
            calibration_before=calibration,
            max_batch_duration_s=max_batch_duration_s,
        )
        self.sessions[session_id] = session
        self.current_session = session
        return session

    def end_session(
        self,
        session_id: str | None = None,
        calibration: CalibrationData | None = None,
    ) -> HardwareSession | None:
        """End a hardware session.

        Args:
            session_id: Session to end (or current session if None).
            calibration: Final calibration data.

        Returns:
            Closed HardwareSession.
        """
        if session_id is None:
            session = self.current_session
        else:
            session = self.sessions.get(session_id)

        if session:
            session.close(calibration)
            if session == self.current_session:
                self.current_session = None

        return session

    def add_job(self, job: JobMetadata, session_id: str | None = None) -> None:
        """Add a job to a session.

        Args:
            job: Job metadata to add.
            session_id: Session to add to (or current session if None).
        """
        if session_id:
            session = self.sessions.get(session_id)
        else:
            session = self.current_session

        if session:
            session.add_job(job)

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all sessions."""
        return {
            "n_sessions": len(self.sessions),
            "sessions": {
                sid: {
                    "n_jobs": len(s.jobs),
                    "success_rate": s.success_rate,
                    "drift_detected": s.drift_detected,
                    "duration_s": s.duration_s,
                }
                for sid, s in self.sessions.items()
            },
        }
