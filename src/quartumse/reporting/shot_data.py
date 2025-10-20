"""
Shot data persistence for classical shadows experiments.

Handles writing and reading raw measurement data to/from Parquet format.
"""

import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


class ShotDataWriter:
    """Writes classical shadows measurement data to Parquet format."""

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
        Save shadow measurement data to Parquet.

        Args:
            experiment_id: Unique experiment identifier
            measurement_bases: Array of shape (shadow_size, num_qubits) with basis indices
            measurement_outcomes: Array of shape (shadow_size, num_qubits) with measurement outcomes
            num_qubits: Number of qubits

        Returns:
            Path to the saved Parquet file
        """
        shadow_size = len(measurement_outcomes)

        # Build dataframe
        records = []
        for shadow_idx in range(shadow_size):
            # Encode measurement bases as string (e.g., "XYZ")
            basis_map = {0: "Z", 1: "X", 2: "Y"}  # Common Clifford basis convention
            bases_str = "".join(
                basis_map.get(int(b), str(b)) for b in measurement_bases[shadow_idx]
            )

            # Encode outcomes as bitstring
            outcomes_str = "".join(str(int(o)) for o in measurement_outcomes[shadow_idx])

            records.append(
                {
                    "experiment_id": experiment_id,
                    "shadow_index": shadow_idx,
                    "num_qubits": num_qubits,
                    "measurement_bases": bases_str,
                    "measurement_outcomes": outcomes_str,
                    "timestamp": time.time(),
                }
            )

        df = pd.DataFrame(records)

        # Write to Parquet
        output_path = self.shots_dir / f"{experiment_id}.parquet"
        df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)

        return output_path

    def load_shadow_measurements(
        self, experiment_id: str
    ) -> tuple[np.ndarray, np.ndarray, int]:
        """
        Load shadow measurement data from Parquet.

        Args:
            experiment_id: Unique experiment identifier

        Returns:
            Tuple of (measurement_bases, measurement_outcomes, num_qubits)
        """
        parquet_path = self.shots_dir / f"{experiment_id}.parquet"

        if not parquet_path.exists():
            raise FileNotFoundError(f"Shot data not found: {parquet_path}")

        df = pd.read_parquet(parquet_path, engine="pyarrow")

        # Decode bases
        basis_map_inv = {"Z": 0, "X": 1, "Y": 2}
        measurement_bases = []
        for bases_str in df["measurement_bases"]:
            bases = [basis_map_inv[b] for b in bases_str]
            measurement_bases.append(bases)

        measurement_bases = np.array(measurement_bases)

        # Decode outcomes
        measurement_outcomes = []
        for outcomes_str in df["measurement_outcomes"]:
            outcomes = [int(o) for o in outcomes_str]
            measurement_outcomes.append(outcomes)

        measurement_outcomes = np.array(measurement_outcomes)

        num_qubits = int(df["num_qubits"].iloc[0])

        return measurement_bases, measurement_outcomes, num_qubits
