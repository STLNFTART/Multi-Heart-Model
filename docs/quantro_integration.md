# Quantro-Heart-Model Integration Guide

## Overview

The Multi-Heart-Model repository integrates with the [Quantro-Heart-Model](https://github.com/STLNFTART/Quantro-Heart-Model) to provide a comprehensive suite of physiological modeling tools. The Quantro-Heart-Model serves as the foundational APL implementation, while Multi-Heart-Model extends it with hybrid Python/D capabilities and brain-heart coupling functionality.

## Repository Relationship

```
Multi-Heart-Model (This Repository)
├── Extends Quantro-Heart-Model with brain-heart coupling
├── Adds hybrid Python/D implementation
├── Provides event-driven dynamics support
└── Includes Quantro-Heart-Model as submodule for reference

Quantro-Heart-Model (Submodule in external/)
├── APL-based Primal Overlay framework
├── Reference physiological models
├── Warp-aware RK4 integrator
└── Python analysis tools
```

## Getting Started

### Cloning with Submodules

When cloning this repository for the first time, initialize the Quantro-Heart-Model submodule:

```bash
# Clone with submodules
git clone --recursive https://github.com/STLNFTART/Multi-Heart-Model.git

# Or if already cloned, initialize submodules
git submodule init
git submodule update
```

### Accessing Quantro-Heart-Model

The Quantro-Heart-Model is located in `external/quantro-heart-model/`:

```bash
cd external/quantro-heart-model/

# Run APL models (requires Dyalog APL or GNU APL)
dyalog run.apl

# Analyze results with Python
python analyze_results.py results.csv
```

## Integration Workflows

### 1. Using APL Reference Models

The Quantro-Heart-Model provides reference implementations that can be used to validate the Multi-Heart-Model implementations:

**APL Models Available:**
- `mm.apl` - Michaelis-Menten kinetics
- `sir.apl` - SIR epidemiological model
- `fhn.apl` - FitzHugh-Nagumo neural oscillator
- `nernst.apl` - Nernst potential
- `poiseuille.apl` - Poiseuille flow

**Example validation workflow:**
1. Run the APL reference model: `cd external/quantro-heart-model && dyalog fhn.apl`
2. Compare with Python implementation: `python -c "from src.neural import FitzHughNagumo; ..."`
3. Validate D implementation: `./primal_overlay`

### 2. Leveraging Overlay Mechanisms

The Quantro-Heart-Model's overlay system (Residual, ParamMod, Control, TimeWarp) can be integrated with Multi-Heart-Model's coupling parameters:

```python
# Example: Using Quantro overlays with HBCM coupling
from src.cardiac import VanDerPolOscillator
from src.coupling import CouplingParameters, HeartBrainCouplingModel
from src.neural import FitzHughNagumo

# Initialize with overlay-inspired parameters
coupling = CouplingParameters(
    neural_to_cardiac_gain=0.5,    # Similar to ParamMod overlay
    cardiac_to_neural_gain=0.3,
    time_delay=0.1                  # Similar to TimeWarp overlay
)

hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
    cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
    coupling=coupling
)
```

### 3. Analysis Pipeline Integration

Use Quantro-Heart-Model's Python analysis tools for Multi-Heart-Model outputs:

```bash
# Run Multi-Heart-Model simulation
./primal_overlay

# Analyze with Quantro tools
python external/quantro-heart-model/analyze_results.py results.csv
```

## Model Correspondence

| Quantro-Heart-Model (APL) | Multi-Heart-Model (Python) | Multi-Heart-Model (D) |
|---------------------------|----------------------------|------------------------|
| `fhn.apl` | `src/neural/fitzhugh_nagumo.py` | `source/models/fhn.d` |
| `mm.apl` | Planned in `src/cardiac/` | `source/models/mm.d` |
| `sir.apl` | Not implemented | `source/models/sir.d` |
| `nernst.apl` | Planned in `src/cardiac/` | `source/models/nernst.d` |
| `poiseuille.apl` | Planned in `src/cardiac/` | `source/models/poiseuille.d` |

## Advanced Integration

### Custom Overlay Development

To develop custom overlays that work with both repositories:

1. **Define in APL** (Quantro-Heart-Model):
   - Implement overlay logic in `external/quantro-heart-model/overlays.apl`
   - Test with warp-aware RK4 integrator

2. **Port to Python** (Multi-Heart-Model):
   - Create corresponding coupling parameters in `src/coupling/`
   - Integrate with HBCM framework

3. **Optimize in D** (Multi-Heart-Model):
   - Implement high-performance version in `source/`
   - Validate against APL reference

### Cross-Repository Testing

Use the submodule for cross-validation:

```bash
# Run tests against both implementations
pytest tests/                           # Multi-Heart-Model tests
cd external/quantro-heart-model
pytest tests/                           # Quantro-Heart-Model tests
cd ../..

# Compare outputs
diff results.csv external/quantro-heart-model/results.csv
```

## Updating the Submodule

To update to the latest Quantro-Heart-Model version:

```bash
cd external/quantro-heart-model
git pull origin main
cd ../..
git add external/quantro-heart-model
git commit -m "Update Quantro-Heart-Model submodule"
```

## Contributing

When contributing to either repository:

1. **Quantro-Heart-Model changes**: Submit PRs to https://github.com/STLNFTART/Quantro-Heart-Model
2. **Multi-Heart-Model changes**: Submit PRs to this repository
3. **Cross-repository features**:
   - Implement reference in Quantro-Heart-Model first
   - Extend in Multi-Heart-Model
   - Document integration in this guide

## References

- [Quantro-Heart-Model Repository](https://github.com/STLNFTART/Quantro-Heart-Model)
- [Multi-Heart-Model Architecture](./hbcm_overview.md)
- [HBCM Overview](./hbcm_overview.md)

## Support

For Quantro-Heart-Model specific issues, see: https://github.com/STLNFTART/Quantro-Heart-Model/issues
For Multi-Heart-Model and integration issues, see: https://github.com/STLNFTART/Multi-Heart-Model/issues
