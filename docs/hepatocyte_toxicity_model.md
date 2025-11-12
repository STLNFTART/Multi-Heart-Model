# Hepatocyte Toxicity Model Overview

The Hepatocyte Toxicity Model captures drug-induced liver injury (DILI) through a multi-state ordinary differential equation (ODE) system that integrates cellular dynamics, drug metabolism, energy homeostasis, and antioxidant defense mechanisms. This model extends the Multi-Heart-Model framework to include hepatic organ systems for toxicology and pharmacokinetic/pharmacodynamic (PK/PD) simulations.

## Model Structure

### State Vector

The model tracks 8 state variables that collectively describe hepatocyte viability, drug/metabolite concentrations, and cellular biochemistry:

```
State[0]: N_viable      - Number of viable hepatocytes
State[1]: N_damaged     - Number of damaged hepatocytes
State[2]: N_dead        - Number of dead hepatocytes
State[3]: drug_conc     - Drug concentration in liver (μM)
State[4]: metabolite_conc - Metabolite concentration (μM)
State[5]: CYP450_activity - Enzyme activity (normalized, 0-1)
State[6]: ATP_level     - Cellular ATP (mM)
State[7]: GSH_level     - Glutathione (mM)
```

### Core Formulation

The hepatocyte toxicity dynamics are governed by the following system of ODEs:

#### 1. Cell Population Dynamics

Hepatocytes transition through three states in a damage-dependent cascade:

$$
\begin{aligned}
\frac{dN_{\text{viable}}}{dt} &= -k_{\text{damage}} \cdot D(t) \cdot N_{\text{viable}} + k_{\text{repair}} \cdot R(t) \cdot N_{\text{damaged}} \\
\frac{dN_{\text{damaged}}}{dt} &= k_{\text{damage}} \cdot D(t) \cdot N_{\text{viable}} - k_{\text{repair}} \cdot R(t) \cdot N_{\text{damaged}} - k_{\text{death}} \cdot S(t) \cdot N_{\text{damaged}} \\
\frac{dN_{\text{dead}}}{dt} &= k_{\text{death}} \cdot S(t) \cdot N_{\text{damaged}}
\end{aligned}
$$

where:
- $D(t)$ is the damage index (see below)
- $R(t)$ is the repair efficiency factor: $R(t) = \min\left(1, \frac{\text{ATP}}{3}\right) \cdot \min\left(1, \frac{\text{GSH}}{5}\right)$
- $S(t)$ is the severe damage factor: $S(t) = \max(0, D(t) - \theta_{\text{death}})$

#### 2. Drug Metabolism (Michaelis-Menten Kinetics)

Drug is metabolized by CYP450 enzymes following saturable enzyme kinetics:

$$
\begin{aligned}
\frac{d[\text{Drug}]}{dt} &= I_{\text{drug}}(t) - V_{\text{max}} \cdot \text{CYP450} \cdot \frac{[\text{Drug}]}{K_m + [\text{Drug}]} - k_{\text{clear}} \cdot [\text{Drug}] \\
\frac{d[\text{Metabolite}]}{dt} &= V_{\text{max}} \cdot \text{CYP450} \cdot \frac{[\text{Drug}]}{K_m + [\text{Drug}]} - k_{\text{met}} \cdot [\text{Metabolite}]
\end{aligned}
$$

where:
- $I_{\text{drug}}(t)$ is the external drug input (dosing regimen)
- $V_{\text{max}}$ is the maximum metabolic rate
- $K_m$ is the Michaelis-Menten half-saturation constant
- $k_{\text{clear}}$ and $k_{\text{met}}$ are first-order clearance rates

#### 3. CYP450 Enzyme Dynamics

CYP450 enzyme activity is dynamically regulated by synthesis, degradation, and metabolite-mediated inhibition:

$$
\frac{d\text{CYP450}}{dt} = k_{\text{syn}} \cdot (1 - f_{\text{damage}}) \cdot \frac{1}{1 + \beta \cdot [\text{Metabolite}]} - k_{\text{deg}} \cdot \text{CYP450}
$$

where:
- $f_{\text{damage}} = \frac{N_{\text{damaged}}}{N_{\text{viable}} + N_{\text{damaged}}}$ represents the fractional cellular damage
- $\beta$ is the metabolite-mediated inhibition constant

#### 4. ATP Energy Metabolism

Cellular ATP is produced by viable hepatocytes and consumed for basal metabolism and repair:

$$
\frac{d\text{ATP}}{dt} = \text{ATP}_{\text{prod}} \cdot \frac{N_{\text{viable}}}{N_{\text{total}}} - \text{ATP}_{\text{basal}} - \text{ATP}_{\text{repair}} \cdot k_{\text{repair}} \cdot N_{\text{damaged}}
$$

#### 5. Glutathione Antioxidant Defense

Glutathione (GSH) is depleted by oxidative stress and regenerated in an ATP-dependent manner:

$$
\frac{d\text{GSH}}{dt} = \text{GSH}_{\text{syn}} \cdot \frac{\text{ATP}}{\text{ATP} + 1} + k_{\text{rec}} \cdot (10 - \text{GSH}) - k_{\text{GSH}} \cdot \text{ROS}(t) \cdot \text{GSH}
$$

where $\text{ROS}(t) = k_{\text{ROS}} \cdot [\text{Metabolite}]$ represents reactive oxygen species generation.

#### 6. Damage Index

The cellular damage index integrates multiple stress sources:

$$
D(t) = \alpha_{\text{drug}} \cdot [\text{Drug}] + \alpha_{\text{met}} \cdot [\text{Metabolite}] + 0.5 \cdot \max(0, 2 - \text{ATP}) + 0.3 \cdot \max(0, 3 - \text{GSH})
$$

where $\alpha_{\text{drug}}$ and $\alpha_{\text{met}}$ are toxicity coefficients for the parent drug and metabolite, respectively.

## Key Features

### 1. Multi-Scale Dynamics
- **Cellular level**: Population dynamics of viable, damaged, and dead hepatocytes
- **Biochemical level**: Drug/metabolite concentrations, enzyme activity
- **Metabolic level**: Energy (ATP) and antioxidant (GSH) homeostasis

### 2. Mechanistic Toxicity
- Direct cytotoxicity from parent drug and metabolites
- Indirect toxicity via ATP depletion (energy crisis)
- Oxidative stress via GSH depletion
- CYP450 inhibition by metabolites

### 3. Adaptive Cellular Responses
- ATP-dependent repair mechanisms
- GSH-mediated antioxidant defense
- Dose-dependent enzyme regulation

### 4. Flexible Dosing Regimens
- Bolus dosing (acute exposure)
- Continuous infusion (chronic exposure)
- Multiple-dose schedules
- Wash-out and recovery scenarios

## Capabilities and Use Cases

### Toxicology Applications
- **Drug safety screening**: Predict hepatotoxicity potential of new chemical entities
- **Dose-response analysis**: Estimate IC50 and therapeutic windows
- **Mechanism identification**: Distinguish direct toxicity from metabolic activation
- **Biomarker discovery**: Correlate model outputs with clinical injury markers (ALT, AST)

### Pharmacokinetic/Pharmacodynamic Modeling
- **First-pass metabolism**: Simulate hepatic drug clearance
- **Metabolite kinetics**: Track formation and elimination of active/toxic metabolites
- **Drug-drug interactions**: Model CYP450-mediated interactions
- **Enzyme induction/inhibition**: Simulate adaptive metabolic responses

### Clinical Translation
- **Risk stratification**: Identify high-risk patient populations
- **Optimal dosing**: Balance efficacy and toxicity
- **Combination therapy**: Assess synergistic/antagonistic hepatotoxicity
- **Recovery prediction**: Forecast outcomes after drug withdrawal

## Implementation Details

### Numerical Integration
The model uses explicit Euler integration with adaptive timestep control. State variables are constrained to remain non-negative, and CYP450 activity is clamped to [0, 1].

```python
from src.hepatic import HepatocyteToxicityModel

# Initialize model with default parameters
model = HepatocyteToxicityModel()

# Generate initial state
state = model.get_initial_state(N_total=1000.0)

# Simulation loop
dt = 0.01  # hours
for t in range(1000):
    state = model.step(t * dt, state, dt, drug_input=50.0)
```

### Parameter Customization
All model parameters are configurable via the dataclass interface or YAML configuration:

```python
# Custom parameters
model = HepatocyteToxicityModel(
    Vmax=150.0,
    Km=50.0,
    drug_toxicity=0.03,
    metabolite_toxicity=0.08
)
```

Or via `config/default.yaml`:
```yaml
hepatic:
  Vmax: 150.0
  Km: 50.0
  drug_toxicity: 0.03
  metabolite_toxicity: 0.08
```

## Validation and Calibration

### Parameter Estimation
Model parameters can be fitted to experimental data using:
- **In vitro** hepatocyte viability assays
- **In vivo** pharmacokinetic studies
- Clinical biomarker time courses (ALT, AST, bilirubin)

### Validation Datasets
- Acetaminophen (APAP) toxicity: prototype reactive metabolite injury
- Diclofenac: idiosyncratic DILI
- Isoniazid: dose-dependent hepatotoxicity

### Sensitivity Analysis
Key parameters influencing model behavior:
1. `metabolite_toxicity` (α_met): Most sensitive parameter for outcome
2. `Vmax` and `Km`: Control metabolic activation rate
3. `k_repair`: Determines recovery capacity
4. `ATP_baseline`: Influences cellular resilience

## Output Biomarkers

The model provides surrogate biomarkers comparable to clinical measures:

```python
markers = model.compute_injury_markers(state)
```

Returns:
- **viability**: Cell viability percentage (0-100%)
- **damage_fraction**: Fraction of damaged cells
- **death_fraction**: Fraction of dead cells (correlates with ALT/AST release)
- **metabolic_capacity**: Functional metabolic capacity
- **oxidative_stress**: ROS burden index
- **energy_deficit**: ATP depletion severity

## Example Scenarios

### Acute High-Dose Toxicity
```bash
python examples/hepatocyte_toxicity_demo.py
```
Simulates a 300 μM bolus dose over 48 hours, demonstrating rapid cell death and metabolic collapse.

### Chronic Low-Dose Exposure
Models continuous 15 μM/hr infusion over 7 days, showing steady-state balance between damage and repair.

### Recovery After Withdrawal
Demonstrates cellular recovery after 24-hour exposure followed by 72-hour drug-free period.

## Integration with Multi-Organ Models

The hepatocyte model can be coupled with existing cardiac and neural models for:
- **Drug cardiotoxicity**: Simulate combined hepatic + cardiac effects (e.g., QT prolongation)
- **Autonomic dysfunction**: Model liver injury effects on vagal tone
- **Systemic toxicity**: Multi-organ failure cascades

Future extensions will include:
- Bidirectional coupling via systemic circulation compartments
- Hormone-mediated cross-talk (cortisol, insulin)
- Immune-mediated injury mechanisms

## References

### Biological Background
1. Jaeschke H, et al. (2012). *Mechanisms of hepatotoxicity*. Toxicol Sci 65(2): 166-176.
2. Wilkening S, et al. (2003). *Comparison of primary human hepatocytes and hepatoma cell line HepG2 with regard to their biotransformation properties*. Drug Metab Dispos 31(8): 1035-1042.

### Mathematical Modeling
3. Howell BA, et al. (2012). *In vitro to in vivo extrapolation and species response comparisons for drug-induced liver injury using DILIsym*. J Pharmacokinet Pharmacodyn 39(5): 527-541.
4. Liao KH, et al. (2007). *Development of a multi-route physiologically based pharmacokinetic (PBPK) model for methanol*. Toxicol Sci 95(2): 512-526.

### Enzyme Kinetics
5. Michaelis L, Menten ML (1913). *Die Kinetik der Invertinwirkung*. Biochem Z 49: 333-369.
6. Nelson DR, et al. (2004). *Comparison of cytochrome P450 (CYP) genes from the mouse and human genomes*. Pharmacogenetics 14(1): 1-18.

## File Structure

```
src/hepatic/
├── __init__.py           - Module exports
├── hepatocyte.py         - Core HepatocyteToxicityModel class

tests/
├── test_hepatic.py       - Unit and integration tests

examples/
├── hepatocyte_toxicity_demo.py - Demonstration scenarios

config/
├── default.yaml          - Model configuration (hepatic section)

docs/
├── hepatocyte_toxicity_model.md - This document
```

## Future Developments

### Planned Extensions
1. **Zonation**: Model acinar heterogeneity (periportal vs. pericentral)
2. **Immune response**: Add Kupffer cell activation and inflammation
3. **Regeneration**: Include hepatocyte proliferation
4. **Fibrosis**: Extend to chronic injury and stellate cell activation
5. **PBPK integration**: Embed within full-body pharmacokinetic models

### Advanced Features
- Stochastic cell death for small populations
- Spatial modeling using partial differential equations (PDEs)
- Multi-drug combination effects
- Genetic polymorphism effects (CYP450 variants)

## Contact and Contributions

For questions, bug reports, or contributions related to the hepatocyte toxicity model, please refer to the main repository documentation.

---

**Model Version**: 1.0.0
**Last Updated**: 2025-11-12
**Status**: Production-ready
