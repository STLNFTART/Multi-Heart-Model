  codex/initialize-github-repository-scaffold-6u2hgd
# Multi-Heart-Model (HBCM)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The Multi-Heart-Model repository develops the **Heart–Brain Coupling Model (HBCM)**—a mathematical and computational framework that captures how cardiac and neural systems influence one another through dynamic feedback. Each subsystem is treated as an oscillatory process with a characteristic frequency, damping, and coupling strength, enabling simulations of entrainment, resonance, and modulation observed in physiological data.

## Repository name and license

* **Repository**: `Multi-Heart-Model`
* **License**: [MIT License](LICENSE)

## Model formulation

The coupled brain–heart dynamics are governed by delay-differential equations that exchange state information through bidirectional feedback terms:

$$
\begin{aligned}
\dot{n}_b(t) &= -\lambda_b\, n_b(t) + f_b\big[n_h(t - \Delta_{bh}),\; S_b(t)\big], \\
\dot{n}_h(t) &= -\lambda_h\, n_h(t) + f_h\big[n_b(t - \Delta_{hb}),\; S_h(t)\big].
\end{aligned}
$$

Where:

* $n_b(t)$ and $n_h(t)$ denote the neural and cardiac activation variables.
* $\lambda_b$ and $\lambda_h$ are decay rates for each subsystem.
* $\Delta_{bh}$ and $\Delta_{hb}$ capture inter-system communication delays.
* $f_b(\cdot)$ and $f_h(\cdot)$ encode coupling pathways that incorporate electrical, mechanical, or biochemical feedback through stimulus terms $S_b(t)$ and $S_h(t)$.

This structure supports continuous-time and event-driven formulations, making the HBCM suitable for real-time control experiments as well as offline analysis.

## Capabilities

* Simulates autonomic regulation phenomena such as heart-rate variability, baroreflex responses, and vagal–sympathetic balance.
* Generates multimodal synthetic signals, including ECG traces, neural oscillations, pressure–volume loops, and hemodynamic waveforms.
* Provides a sandbox for testing control, prediction, and synchronization algorithms that span brain–heart interactions.
* Offers configurable coupling functions for continuous or event-driven dynamics to support online and batch workflows.

For a narrative overview, see [docs/hbcm_overview.md](docs/hbcm_overview.md).

## Project goals

1. Provide reference implementations for canonical physiology models (Michaelis–Menten, SIR, FitzHugh–Nagumo, Nernst, Poiseuille) in both APL and D.
2. Prototype neural overlays that modulate cardiac dynamics for hybrid brain–cardiac simulations.
3. Offer a reproducible workflow for running experiments and capturing CSV outputs for downstream analysis.

# Heart–Brain Coupling Model (HBCM)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The Heart–Brain Coupling Model (HBCM) is a mathematical and computational framework for representing how cardiac and neural systems influence each other through dynamic feedback. Each subsystem is modelled as an oscillatory process with its own natural frequency, damping, and feedback strength. Bidirectional coupling terms transmit information between them, allowing simulation of entrainment, resonance, and modulation observed in real physiological data.

## Repository name and license

- **Repository**: `Multi-Heart-Model`
- **License**: [MIT License](LICENSE)

## Model overview

The coupled system is described by

$$\dot{n}_b(t) = -\lambda_b n_b(t) + f_b\big(n_h(t - \Delta_{bh}), S_b(t)\big)$$
$$\dot{n}_h(t) = -\lambda_h n_h(t) + f_h\big(n_b(t - \Delta_{hb}), S_h(t)\big)$$

where:

- $n_b(t)$ and $n_h(t)$ represent neural and cardiac activation variables.
- $\lambda_b$ and $\lambda_h$ are decay rates.
- $\Delta_{bh}$ and $\Delta_{hb}$ are communication delays.
- $f_b$ and $f_h$ encode electrical, mechanical, or biochemical feedback along with external stimuli $S_b(t)$ and $S_h(t)$.

### Capabilities

- Simulates autonomic regulation, including heart-rate variability, baroreflex, and vagal–sympathetic balance.
- Supports multimodal signal generation: ECG, neural oscillations, pressure–volume loops, and hemodynamic waveforms.
- Enables algorithm testing for control, prediction, or synchronization tasks across brain and heart domains.
- Configurable for both continuous and event-driven dynamics, enabling real-time and offline analysis.
- main

## Repository structure

```text
.
 codex/initialize-github-repository-scaffold-6u2hgd
├── data/                # Placeholder for experimental inputs, parameter sweeps, and captured telemetry
├── docs/                # Project documentation, architecture notes, validation reports
├── src/                 # Upcoming hybrid neural–cardiac pipeline sources (neural, cardiac, coupling modules)
├── source/              # Existing D implementation of the Primal Overlay engine
├── *.apl                # Standalone APL model files for physiology benchmarks
├── Makefile             # Convenience build targets for the D toolchain
├── dub.json             # dub configuration for building the D executable
└── results.csv          # Example output generated by the Primal Overlay runner
```

## Usage overview

### Prototype the Python Heart–Brain Coupling package

The Python modules under `src/` expose a minimal hybrid simulation scaffold.
The snippet below integrates the coupled FitzHugh–Nagumo/Van der Pol system
for 10 seconds with modest bidirectional feedback:

```python
from src.cardiac import VanDerPolOscillator
from src.coupling import CouplingParameters, HeartBrainCouplingModel
from src.neural import FitzHughNagumo

hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
    cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
    coupling=CouplingParameters(neural_to_cardiac_gain=0.5, cardiac_to_neural_gain=0.3),
)

trajectory = hbcm.simulate(initial_state=(0.0, 0.0, 1.0, 0.0), t_span=(0.0, 10.0), dt=0.01)
times, neural, cardiac = hbcm.extract_series(trajectory)
```

The resulting `times`, `neural`, and `cardiac` lists can be plotted with
Matplotlib or analysed numerically to explore entrainment behaviour.

├── config/             # YAML configurations for simulations and experiments
├── data/               # Experimental inputs, parameter sweeps, and captured telemetry
├── docs/               # Project documentation, architecture notes, validation reports
├── src/                # Hybrid neural–cardiac pipeline sources (neural, cardiac, coupling modules)
├── source/             # Existing D implementation of the Primal Overlay engine
├── *.apl               # Standalone APL model files for physiology benchmarks
├── Makefile            # Convenience build targets for the D toolchain
├── dub.json            # dub configuration for building the D executable
└── results.csv         # Example output generated by the Primal Overlay runner


## Configuration

Simulation parameters are stored in YAML under `config/`. The provided [`config/default.yaml`](config/default.yaml) file captures representative frequencies, damping coefficients, coupling strengths, and signal export options. Update or extend these configurations to match experimental needs.

## Usage overview
 main

### Build and run the D Primal Overlay engine

```bash
dub build --compiler=ldc2 --build=release
./primal_overlay


The executable writes simulation metrics to `results.csv`. Adjust the models or overlays under `source/models/` to explore alternative physiology dynamics.

### Explore the APL reference models

Run the `.apl` files (e.g., `fhn.apl`, `mm.apl`) with Dyalog APL or GNU APL to validate model behaviour independently of the overlay engine.

  codex/initialize-github-repository-scaffold-6u2hgd
### Prepare data assets

Use the `data/` directory to store curated datasets, patient-specific parameters, or synthetic signals used in hybrid experiments. Check `docs/` for guidance on expected file formats as documentation evolves.

## Contributing and next steps

1. Flesh out the neural and cardiac modules in `src/` following the suggested subdirectory layout.
2. Document the neural–cardiac coupling strategy in `docs/` (e.g., `architecture.md`).
3. Add automated tests and CI badges as the codebase matures.

### Develop hybrid simulations

1. Configure the neural, cardiac, and coupling parameters in `config/default.yaml` (or a scenario-specific copy).
2. Implement subsystem logic in `src/neural/`, `src/cardiac/`, and `src/coupling/`.
3. Integrate the modules with the Primal Overlay engine or a custom runner to produce coupled simulations.

## Contributing and next steps

- Flesh out the neural and cardiac modules in `src/` following the scaffolded subdirectories.
- Extend documentation in `docs/` (e.g., add validation protocols and control strategies).
- Add automated tests and CI workflows as the codebase matures.
- main

## Primal Logic Organ-on-Chip Digital Twin

### Overview

The repository now includes a comprehensive **Heart-Liver Organ-on-Chip Digital Twin** framework for drug screening and toxicity prediction. This extends the HBCM with multiscale integration from molecular drug-receptor binding to systemic circulation.

### Key Features

**Multiscale Architecture:**
- **Molecular**: Ligand-receptor binding dynamics with drug-specific kinetics
- **Cellular**: Immune signaling, hepatocyte and cardiomyocyte populations
- **Organ**: Liver metabolism (CYP450 enzymes) and cardiac electrophysiology
- **Systemic**: Blood circulation and pharmacokinetics (ADME)
- **Bidirectional Coupling**: Feedback across all scales

**Recursive Planck Operator (RPO) Framework:**

Unified mathematical kernel for memory-dependent biological processes:

```
ż = -λz + βm + S(t)
ṁ = α(z - m)
```

Where `z` is the current state, `m` is the exponentially weighted memory, and parameters control decay (λ), feedback (β), and memory formation (α).

**Drug Toxicity Assessment:**
- **Hepatotoxicity**: 5 mechanisms (mitochondrial, oxidative, cholestatic, immune, direct)
- **Cardiotoxicity**: hERG channel blockade, QT prolongation, arrhythmia risk
- **Biomarkers**: ALT, AST, troponin, BNP, ATP, GSH
- **PK Metrics**: Cmax, Tmax, AUC, T1/2, clearance

### Quick Start

```python
from primal_logic.integration import OrganChipSuite

# Initialize digital twin
suite = OrganChipSuite()

# Screen a drug
times, results = suite.run_drug_screen(
    drug_name="doxorubicin",
    dose=50.0,  # mg
    duration=48.0,  # hours
    dosing_schedule="bolus"
)

# Get toxicity report
report = suite.assess_toxicity(times, results)
print(suite.generate_report(report))
```

### Package Structure

```
primal_logic/
├── core/               # RPO mathematical framework
├── molecular/          # Ligand-receptor binding
├── cellular/           # Immune signaling
├── organ/
│   ├── liver/          # Hepatocyte, metabolism, toxicity
│   └── cardiac/        # Cardiomyocyte, electrophysiology
├── systemic/           # Circulation and PK
└── integration/        # Multiscale coupling, organ chip suite
```

### Pre-configured Validation Drugs

- **Acetaminophen**: Hepatotoxic (dose-dependent GSH depletion)
- **Doxorubicin**: Dual toxicity (cardio + hepato)
- **Dofetilide**: Cardiotoxic (potent hERG blocker)
- **Amiodarone**: Dual toxicity (long-term effects)
- **Aspirin**: Reference safe drug

### Demo

```bash
python demos/demo_heart_liver_organ_chip.py
```

### Documentation

See [docs/heart_liver_organ_chip.md](docs/heart_liver_organ_chip.md) for comprehensive documentation including:
- Mathematical formulations for each component
- Parameter guidelines and typical ranges
- Validation against known toxic drugs
- Applications in drug discovery and personalized medicine

### Applications

1. **Pre-clinical Drug Screening**: Toxicity prediction before animal studies
2. **Drug-Drug Interactions**: CYP450 inhibition/induction effects
3. **Dose Optimization**: Safety margin determination
4. **Personalized Medicine**: Patient-specific parameter adjustments
5. **Clinical Trial Design**: Biomarker selection and monitoring strategies

## Acknowledgements

The HBCM scaffold builds upon the original Primal Overlay physiology suite and extends it toward hybrid neural–cardiac experimentation. The Primal Logic Organ-on-Chip framework was developed by Donte Lightfoot (Lightfoot Technology) and integrates the Recursive Planck Operator mathematical formalism across biological scales.
