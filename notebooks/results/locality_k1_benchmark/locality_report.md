# Locality Benchmark Report (K=1)

## Configuration
- Locality K: 1
- Variance factor: 3^1 = 3
- Circuit: 4-qubit GHZ
- Observables: 12
- Shot grid: [100, 500, 1000, 5000]
- Replicates: 20

## Results

| Protocol | Mean SE | Median SE | Max SE |
|----------|---------|-----------|--------|
| direct_naive | 0.0490 | 0.0491 | 0.0491 |
| direct_grouped | 0.0245 | 0.0245 | 0.0245 |
| direct_optimized | 0.0245 | 0.0245 | 0.0245 |
| classical_shadows_v0 | 0.0245 | 0.0245 | 0.0253 |

## Dominance Analysis
- Crossover N: None
- Shadows wins at: [100, 500, 1000, 5000]
- Grouped wins at: []

## Conclusion
At locality K=1, **SHADOWS** performs better.
