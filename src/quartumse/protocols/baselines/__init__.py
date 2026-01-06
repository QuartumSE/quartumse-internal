"""Baseline protocols for benchmarking (Measurements Bible §4.1).

This package provides the required baseline protocols that all advanced
measurement strategies must be compared against:

1. DirectNaiveProtocol (§4.1A): Measures each observable independently.
   - No grouping, no optimization
   - O(M) measurement settings
   - The simplest possible approach

2. DirectGroupedProtocol (§4.1B): Groups commuting observables.
   - Qubit-wise commuting grouping
   - Uniform shot allocation across groups
   - O(G) measurement settings where G ≤ M
   - REQUIRED baseline for defensible benchmarks

3. DirectOptimizedProtocol (§4.1C): Optimal shot allocation.
   - Same grouping as DirectGrouped
   - Optimal shot allocation across groups
   - Represents best direct measurement performance

Usage:
    from quartumse.protocols.baselines import (
        DirectNaiveProtocol,
        DirectGroupedProtocol,
        DirectOptimizedProtocol,
    )

    # Create baseline protocols
    naive = DirectNaiveProtocol()
    grouped = DirectGroupedProtocol(grouping_method="greedy")
    optimized = DirectOptimizedProtocol(allocation_strategy="proportional")

    # Run baseline measurement
    state = naive.initialize(observable_set, N_total, seed=42)
    plan = naive.plan(state)
    # ... execute measurements ...
    estimates = naive.finalize(state, observable_set)

Comparison requirements (§4.1):
- Any advanced protocol must show improvement over DirectGroupedProtocol
- Shot-savings factor (SSF) is computed relative to DirectGroupedProtocol
- Fair comparison requires same observable set and shot budget
"""

from .direct_grouped import DirectGroupedProtocol, DirectGroupedState
from .direct_naive import DirectNaiveProtocol, DirectNaiveState
from .direct_optimized import DirectOptimizedProtocol, DirectOptimizedState

__all__ = [
    # Protocols
    "DirectNaiveProtocol",
    "DirectGroupedProtocol",
    "DirectOptimizedProtocol",
    # States
    "DirectNaiveState",
    "DirectGroupedState",
    "DirectOptimizedState",
]
