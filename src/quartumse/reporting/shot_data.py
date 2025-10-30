"""Shot data persistence and diagnostics for classical shadows experiments."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ShotDataDiagnostics:
    """Summary statistics extracted from persisted shadow measurements."""

    experiment_id: str
    total_shots: int
    num_qubits: int
    measurement_basis_distribution: dict[str, int]
    bitstring_histogram: dict[str, int]
    qubit_marginals: dict[int, dict[str, float]]

    def to_dict(self) -> dict[str, object]:
        """Convert diagnostics to a plain dictionary for templating."""

        return {
            "experiment_id": self.experiment_id,
            "total_shots": self.total_shots,
            "num_qubits": self.num_qubits,
            "measurement_basis_distribution": self.measurement_basis_distribution,
            "bitstring_histogram": self.bitstring_histogram,
            "qubit_marginals": self.qubit_marginals,
        }


class ShotDataWriter:
    """Writes classical shadows measurement data to Parquet format and computes summaries."""

    def __init__(self, data_dir: Path):
        """
        Initialize shot data writer.

        Args:
            data_dir: Base directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.shots_dir = self.data_dir / "shots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)

    def save_shadow_measurements(
        self,
        experiment_id: str,
        measurement_bases: np.ndarray,
        measurement_outcomes: np.ndarray,
        num_qubits: int,
    ) -> Path:
        """
        Save shadow measurement data to Parquet, appending if the experiment already exists.

        Args:
            experiment_id: Unique experiment identifier
            measurement_bases: Array of shape (shadow_size, num_qubits) with basis indices
            measurement_outcomes: Array of shape (shadow_size, num_qubits) with measurement outcomes
            num_qubits: Number of qubits

        Returns:
            Path to the saved Parquet file
        """
        shadow_size = len(measurement_outcomes)

        output_path = self.shots_dir / f"{experiment_id}.parquet"

        existing_df = None
        start_index = 0
        if output_path.exists():
            existing_df = pd.read_parquet(output_path, engine="pyarrow")
            if not existing_df.empty:
                existing_num_qubits = int(existing_df["num_qubits"].iloc[0])
                if existing_num_qubits != num_qubits:
                    raise ValueError(
                        "Existing shot data has a different number of qubits than the new chunk."
                    )
                start_index = int(existing_df["shadow_index"].max()) + 1

        # Build dataframe for the new chunk
        records = []
        for offset in range(shadow_size):
            global_index = start_index + offset

            # Encode measurement bases as string (e.g., "XYZ")
            basis_map = {0: "Z", 1: "X", 2: "Y"}  # Common Clifford basis convention
            bases_str = "".join(basis_map.get(int(b), str(b)) for b in measurement_bases[offset])

            # Encode outcomes as bitstring
            outcomes_str = "".join(str(int(o)) for o in measurement_outcomes[offset])

            records.append(
                {
                    "experiment_id": experiment_id,
                    "shadow_index": global_index,
                    "num_qubits": num_qubits,
                    "measurement_bases": bases_str,
                    "measurement_outcomes": outcomes_str,
                    "timestamp": time.time(),
                }
            )

        new_df = pd.DataFrame(records)

        if existing_df is not None and not existing_df.empty:
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = new_df

        df = df.sort_values("shadow_index").reset_index(drop=True)

        df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)

        return output_path

    def _load_dataframe(self, experiment_id: str) -> pd.DataFrame:
        """Load the raw Parquet dataframe for an experiment."""

        parquet_path = self.shots_dir / f"{experiment_id}.parquet"
        if not parquet_path.exists():
            raise FileNotFoundError(f"Shot data not found: {parquet_path}")

        return pd.read_parquet(parquet_path, engine="pyarrow")

    def load_shadow_measurements(self, experiment_id: str) -> tuple[np.ndarray, np.ndarray, int]:
        """
        Load shadow measurement data from Parquet.

        Args:
            experiment_id: Unique experiment identifier

        Returns:
            Tuple of (measurement_bases, measurement_outcomes, num_qubits)
        """
        df = self._load_dataframe(experiment_id)

        # Decode bases
        basis_map_inv = {"Z": 0, "X": 1, "Y": 2}
        measurement_bases_list: list[list[int]] = []
        for bases_str in df["measurement_bases"]:
            bases = [basis_map_inv[b] for b in bases_str]
            measurement_bases_list.append(bases)

        measurement_bases_array = np.asarray(measurement_bases_list, dtype=int)

        # Decode outcomes
        measurement_outcomes_list: list[list[int]] = []
        for outcomes_str in df["measurement_outcomes"]:
            outcomes = [int(o) for o in outcomes_str]
            measurement_outcomes_list.append(outcomes)

        measurement_outcomes_array = np.asarray(measurement_outcomes_list, dtype=int)

        num_qubits = int(df["num_qubits"].iloc[0])

        return measurement_bases_array, measurement_outcomes_array, num_qubits

    def summarize_shadow_measurements(
        self, experiment_id: str, *, top_bitstrings: int = 10
    ) -> ShotDataDiagnostics:
        """Compute diagnostics for persisted shadow measurements."""

        df = self._load_dataframe(experiment_id)
        return summarize_dataframe(df, experiment_id=experiment_id, top_bitstrings=top_bitstrings)

    @staticmethod
    def summarize_parquet(
        parquet_path: str | Path, *, top_bitstrings: int = 10
    ) -> ShotDataDiagnostics:
        """Compute diagnostics directly from a Parquet file."""

        parquet_path = Path(parquet_path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Shot data not found: {parquet_path}")

        df = pd.read_parquet(parquet_path, engine="pyarrow")
        experiment_id = parquet_path.stem
        return summarize_dataframe(df, experiment_id=experiment_id, top_bitstrings=top_bitstrings)


def summarize_dataframe(
    df: pd.DataFrame, *, experiment_id: str, top_bitstrings: int = 10
) -> ShotDataDiagnostics:
    """Create diagnostics from an in-memory dataframe."""

    if df.empty:
        raise ValueError("Shot data dataframe is empty; cannot compute diagnostics.")

    total_shots = len(df)
    num_qubits = int(df["num_qubits"].iloc[0])

    basis_distribution = (
        df["measurement_bases"].value_counts().sort_values(ascending=False).to_dict()
    )

    bitstring_counts = df["measurement_outcomes"].value_counts().head(top_bitstrings).to_dict()
    bitstring_histogram = {bit: int(count) for bit, count in bitstring_counts.items()}

    qubit_marginals: dict[int, dict[str, float]] = {}
    for qubit in range(num_qubits):
        qubit_bits = df["measurement_outcomes"].str.get(qubit)
        counts = Counter(qubit_bits)
        total = sum(counts.values())
        qubit_marginals[qubit] = {
            "0": counts.get("0", 0) / total if total else 0.0,
            "1": counts.get("1", 0) / total if total else 0.0,
        }

    return ShotDataDiagnostics(
        experiment_id=experiment_id,
        total_shots=total_shots,
        num_qubits=num_qubits,
        measurement_basis_distribution={k: int(v) for k, v in basis_distribution.items()},
        bitstring_histogram=bitstring_histogram,
        qubit_marginals=qubit_marginals,
    )
