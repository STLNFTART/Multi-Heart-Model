# Multi-Heart-Model — APL

APL reimplementation of the Primal Overlay physiology models (Michaelis–Menten, SIR, FitzHugh–Nagumo, Nernst, Poiseuille).
Each `.apl` file exposes a single dfn that evaluates the corresponding right-hand side under the
same residual/parameter-modulation/control semantics as the D reference implementation located in `source/`.

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
