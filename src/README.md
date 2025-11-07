# Source Layout

codex/initialize-github-repository-scaffold-6u2hgd
The `src/` directory now contains a lightweight Python package that links
neural control modules with cardiac oscillators. Each subsystem can be used
independently or orchestrated via the Heart–Brain Coupling Model (HBCM)
wrapper in `coupling/`.

Current layout:

* `neural/` – FitzHugh–Nagumo oscillator implementation modelling neural activation.
* `cardiac/` – Van der Pol-based relaxation oscillator representing rhythmic cardiac motion.
* `coupling/` – Bidirectional feedback utilities stitching neural and cardiac dynamics together.

The modules expose simple Euler integration helpers and a convenience
`HeartBrainCouplingModel` class for end-to-end simulations. Extend these
packages with richer physiology models as the project matures.

The `src/` directory hosts the hybrid modeling pipeline that links neural control modules with cardiac electrophysiology solvers. The directories are scaffolded to mirror the mathematical structure of the Heart–Brain Coupling Model (HBCM).

## Directory overview

- `neural/` – oscillatory neural models, autonomic controllers, and neural signal processing utilities.
- `cardiac/` – cardiac electrophysiology and hemodynamic models able to emit ECG and pressure/volume traces.
- `coupling/` – integration logic that exchanges state between subsystems, enforces delays, and manages numerical solvers.

Populate these folders with actual implementations as development progresses. Each subdirectory includes a README to document expectations and facilitate collaboration main
