# Heart–Brain Coupling Model Overview

The Heart–Brain Coupling Model (HBCM) formalizes how cardiac and neural systems modulate one another through coupled oscillators and delayed feedback pathways. It extends the existing Primal Overlay physiology suite with neuromodulation layers that capture autonomic regulation phenomena.

## Core formulation

The HBCM describes neural activity $n_b(t)$ and cardiac activation $n_h(t)$ using coupled delay-differential equations:

$$
\begin{aligned}
\dot{n}_b(t) &= -\lambda_b\, n_b(t) + f_b\big[n_h(t - \Delta_{bh}),\; S_b(t)\big], \\
\dot{n}_h(t) &= -\lambda_h\, n_h(t) + f_h\big[n_b(t - \Delta_{hb}),\; S_h(t)\big].
\end{aligned}
$$

* $\lambda_b$ and $\lambda_h$ represent intrinsic damping.
* $\Delta_{bh}$ and $\Delta_{hb}$ capture communication delays between neural and cardiac pathways.
* $f_b(\cdot)$ and $f_h(\cdot)$ aggregate coupling effects such as autonomic nerve signals, baroreceptor feedback, or hormone-mediated modulation.
* $S_b(t)$ and $S_h(t)$ are exogenous stimulus terms (e.g., respiration, pharmacological interventions, task demands).

The model supports both continuous-time integration and event-driven updates, enabling the same formulation to power real-time control experiments or offline analyses of recorded signals.

## Capabilities and use cases

* **Autonomic regulation studies** – Simulate heart-rate variability, baroreflex loops, and vagal–sympathetic balance.
* **Multimodal signal generation** – Produce ECG, neural oscillations, pressure–volume loops, and hemodynamic waveforms for algorithm development or visualization.
* **Control and synchronization research** – Evaluate strategies for coordinating neural stimulation with cardiac rhythm management devices.
* **Hybrid data assimilation** – Combine synthetic and empirical data within a shared coupling framework for parameter identification or forecasting.

## Workflow integration

The repository complements the mathematical model with:

* D-based implementations in `source/` for high-performance simulation and CSV data export.
* APL reference models (`*.apl`) for benchmarking and prototyping physiological subsystems.
* A staged `src/` layout ready for neural, cardiac, and coupling modules that implement the HBCM equations.
* Documentation assets in `docs/` to capture architecture decisions, validation plans, and usage guides.

As the project matures, this overview will link to detailed subsystem documentation, parameter libraries, and experiment notebooks housed in the same directory.
