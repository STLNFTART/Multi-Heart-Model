# Source Layout

The `src/` directory hosts the hybrid modeling pipeline that links neural control modules with cardiac electrophysiology solvers. The directories are scaffolded to mirror the mathematical structure of the Heart–Brain Coupling Model (HBCM).

## Directory overview

- `neural/` – oscillatory neural models, autonomic controllers, and neural signal processing utilities.
- `cardiac/` – cardiac electrophysiology and hemodynamic models able to emit ECG and pressure/volume traces.
- `coupling/` – integration logic that exchanges state between subsystems, enforces delays, and manages numerical solvers.

Populate these folders with actual implementations as development progresses. Each subdirectory includes a README to document expectations and facilitate collaboration.
