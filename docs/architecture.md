# Heart–Brain Coupling Model Architecture

The Heart–Brain Coupling Model (HBCM) captures bidirectional dynamics between neural and cardiac systems using coupled oscillators with configurable delays and feedback strengths. Each subsystem follows the generic form

$$\dot{n}_b(t) = -\lambda_b n_b(t) + f_b\big(n_h(t - \Delta_{bh}), S_b(t)\big)$$
$$\dot{n}_h(t) = -\lambda_h n_h(t) + f_h\big(n_b(t - \Delta_{hb}), S_h(t)\big)$$

where:

- $n_b(t)$ and $n_h(t)$ represent neural and cardiac activation variables.
- $\lambda_b$ and $\lambda_h$ denote subsystem-specific damping terms.
- $\Delta_{bh}$ and $\Delta_{hb}$ encode signal transmission delays between the subsystems.
- $f_b$ and $f_h$ are coupling functions that may include electrical, mechanical, or biochemical pathways.
- $S_b(t)$ and $S_h(t)$ aggregate external stimuli and regulatory signals.

## Subsystem responsibilities

### Neural domain (`src/neural/`)
- Model the neural oscillators that form the brain-side dynamics.
- Implement autonomic control strategies (vagal, sympathetic, baroreflex).
- Emit control signals for the cardiac subsystem based on sensory feedback and internal rhythms.

### Cardiac domain (`src/cardiac/`)
- Provide electrophysiological models that can respond to neural inputs.
- Generate measurable outputs such as ECG traces, blood pressure, and volume waveforms.
- Supply sensory signals back to the neural subsystem for feedback loops.

### Coupling domain (`src/coupling/`)
- Synchronize disparate time scales and integrators between neural and cardiac solvers.
- Manage configurable delays and strength parameters defined in configuration files.
- Monitor stability, entrainment, and resonance behaviours across the coupled system.

## Configuration flow

Parameters such as decay rates, coupling strengths, and delays are defined in YAML configuration files under `config/`. Simulation routines should ingest these values to construct subsystem instances and orchestrate time stepping.

## Outputs and analysis

The coupled simulation is expected to produce multi-modal signals:

- Neural oscillations and derived features.
- Cardiac electrocardiogram (ECG) traces.
- Hemodynamic waveforms, including pressure–volume loops.

Results can be exported to `results/` and further analyzed with notebooks or scripts stored in `docs/` or `data/` as the project evolves.
