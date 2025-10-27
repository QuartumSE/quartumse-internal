"""
Zero-Noise Extrapolation (ZNE).

Runs circuit at multiple noise levels and extrapolates to zero noise.
"""

from typing import Callable, List, Optional

import numpy as np


class ZeroNoiseExtrapolation:
    """
    Zero-noise extrapolation for error mitigation.

    Scales noise by folding gates, then extrapolates to zero-noise limit.
    """

    def __init__(
        self,
        scale_factors: Optional[List[float]] = None,
        extrapolator: str = "linear",
    ):
        """
        Initialize ZNE.

        Args:
            scale_factors: Noise scaling factors (e.g., [1, 3, 5])
            extrapolator: Extrapolation method ("linear", "exponential", "polynomial")
        """
        self.scale_factors = scale_factors or [1.0, 3.0, 5.0]
        self.extrapolator = extrapolator

    def extrapolate(self, noise_levels: List[float], expectation_values: List[float]) -> float:
        """
        Extrapolate to zero noise.

        Args:
            noise_levels: Noise scale factors
            expectation_values: Measured expectation values

        Returns:
            Extrapolated zero-noise value
        """
        if self.extrapolator == "linear":
            # Linear fit
            coeffs = np.polyfit(noise_levels, expectation_values, 1)
            return float(np.polyval(coeffs, 0))  # Evaluate at noise=0
        else:
            # TODO: Implement other extrapolators
            raise NotImplementedError(f"Extrapolator {self.extrapolator} not implemented")
