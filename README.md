# Multi-Heart-Model — APL

APL reimplementation of the Primal Overlay physiology models (Michaelis–Menten, SIR, FitzHugh–Nagumo, Nernst, Poiseuille).
Each `.apl` file exposes a single dfn that evaluates the corresponding right-hand side under the
same residual/parameter-modulation/control semantics as the D reference implementation located in `source/`.

A companion Python package in `python_models/` mirrors the same interface so the systems can be prototyped in
scientific Python environments without leaving the overlay workflow.

## Usage

Each model expects a boxed argument vector `(mode t x θ overlay)`:

- `mode` – character vector identifying the overlay: `Residual`, `ParamMod`, `Control`, `TimeWarp` (case-insensitive).
- `t` – scalar time point.
- `x` – state vector (length depends on the model).
- `θ` – parameter vector.
- `overlay` – optional vector of functions `[R M U]` corresponding to residual, multiplicative modulation,
  and external control. Missing entries default to no-op behaviour.

Example (GNU APL / Dyalog syntax):

```apl
      overlay←({0.1×⍺+0×⍵})
      args←('Residual')(⊂0)(⊂2 0)(⊂1 0.5)(⊂overlay)
      ⎕←MM args
```

The models mirror the behaviour of their D equivalents in `source/models/` and can therefore be used for
comparative studies or to prototype Heart–Brain Coupling Model (HBCM) control strategies in APL environments.

## Python usage

Install the package in-place (or add the repository root to `PYTHONPATH`) and import the model functions:

```python
from python_models import michaelis_menten, sir

dS, dI, dR = sir(
    mode="Residual",
    t=0.0,
    x=(800.0, 50.0, 150.0),
    theta=(0.3, 0.1, 1000.0),
    overlay=[lambda state, time: 0.05 * state, None, None],
)
```

All functions accept `mode`, `t`, `x`, `theta`, and an optional `(R, M, U)` overlay tuple, returning the state
derivative vector that matches the D and APL implementations.
