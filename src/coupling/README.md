# Coupling Layer

Implement bidirectional communication between neural and cardiac modules here. Core responsibilities:

- Maintain shared state describing activation variables and feedback signals.
- Apply configurable delays (Δ_{bh}, Δ_{hb}); support multiple coupling pathways.
- Provide numerical integrators or adapters required to synchronize heterogeneous solvers.
- Expose metrics to monitor entrainment, resonance, and control performance.

As models evolve, document the chosen integration scheme and stability considerations.
