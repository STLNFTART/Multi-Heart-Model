# Source Layout

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
