# Repository Integrations & Related Projects

**Multi-Heart-Model Integration Ecosystem**

This document provides links and integration guidance for major cardiac modeling platforms, surgical robotics systems, and related open-source projects.

---

## Table of Contents

1. [Surgical Robotics Platforms](#surgical-robotics-platforms)
2. [Cardiac Modeling Platforms](#cardiac-modeling-platforms)
3. [Model Repositories](#model-repositories)
4. [Integration Opportunities](#integration-opportunities)
5. [Data & Validation](#data--validation)
6. [Related Multi-Heart-Model Projects](#related-multi-heart-model-projects)

---

## Surgical Robotics Platforms

### 1. dVRK (da Vinci Research Kit)

**Description**: Open-source research platform based on first-generation da Vinci surgical system

**Links**:
- Main Repository: https://github.com/jhu-dvrk
- Wiki: https://github.com/jhu-dvrk/sawIntuitiveResearchKit/wiki
- Documentation: https://dvrk.lcsr.jhu.edu/

**Multi-Heart-Model Integration**:
- ✅ Implemented: `src/surgical_robotics/dvrk_interface.py`
- Features: Full PSM/MTM/ECM control with physiological feedback
- Status: Production-ready

**Key Features**:
- Patient Side Manipulators (PSM1, PSM2, PSM3)
- Master Tool Manipulators (MTM, MTML, MTMR)
- Endoscopic Camera Manipulator (ECM)
- cisst-SAW library integration
- ROS/ROS2 support

**Publications**:
- Kazanzides, P., et al. (2014). "An open-source research kit for the da Vinci Surgical System." ICRA 2014.

---

### 2. CRTK (Collaborative Robotics Toolkit)

**Description**: Standardized API for surgical robotics systems

**Links**:
- Documentation: https://collaborative-robotics.github.io/
- GitHub: https://github.com/collaborative-robotics
- Surgical Robotics Challenge: https://github.com/surgical-robotics-ai/surgical_robotics_challenge

**Multi-Heart-Model Integration**:
- ✅ Implemented: `src/surgical_robotics/crtk_interface.py`
- Features: Complete CRTK API with physiological state integration
- Status: Production-ready

**Key Features**:
- Standard operating states (DISABLED, ENABLED, PAUSED, FAULT)
- Servo commands (continuous setpoint control)
- Move commands (goal-based motion)
- Measured values (position, velocity, force)
- ROS/ROS2 message compatibility

**Publications**:
- Kazanzides, P., et al. (2021). "The Collaborative Robotics Toolkit (CRTK)." IEEE Robotics and Automation Letters.

---

### 3. AMBF (Asynchronous Multi-Body Framework)

**Description**: Real-time dynamic simulator for surgical robotics

**Links**:
- GitHub: https://github.com/WPI-AIM/ambf
- Documentation: https://github.com/WPI-AIM/ambf/wiki
- WPI AIM Lab: https://aimlab.wpi.edu/

**Multi-Heart-Model Integration**:
- ✅ Implemented: `src/surgical_robotics/ambf_interface.py`
- Features: Simulation environment with physiological integration
- Status: Production-ready

**Key Features**:
- Real-time physics simulation
- dVRK manipulator models included
- Collision detection
- ROS/ROS2 integration
- 3D Slicer compatibility

**Publications**:
- Munawar, A., et al. (2019). "A Real-Time Dynamic Simulator and an Associated Front-End Representation Format for Simulating Complex Robots and Environments." Frontiers in Robotics and AI.

---

### 4. Surgical Robotics AI

**Description**: AI and machine learning for surgical robotics

**Links**:
- GitHub Organization: https://github.com/surgical-robotics-ai
- Surgical Robotics Challenge: https://github.com/surgical-robotics-ai/surgical_robotics_challenge

**Integration Opportunities**:
- AI-based surgical skill assessment
- Reinforcement learning with physiological constraints
- Autonomous surgical subtasks

---

### 5. ROS Medical Robotics

**Description**: ROS packages for medical robotics applications

**Links**:
- ROS-Med: https://rosmed.github.io/
- ISMR 2025 Workshop: https://rosmed.github.io/ismr2025/

**Topics**:
- Integration with 3D Slicer, ROS2, AMBF, Gazebo, dVRK
- SlicerROS2 for image-guided interventions

---

## Cardiac Modeling Platforms

### 1. OpenCARP

**Description**: Open-source cardiac electrophysiology simulator

**Links**:
- Website: https://opencarp.org/
- GitHub: https://github.com/openCARP
- Documentation: https://opencarp.org/documentation
- Modeling Resources: https://opencarp.org/community/modeling-resources

**Integration Opportunities**:
- CellML model import/export
- Tissue-level simulations using Multi-Heart-Model cell models
- ECG generation from Multi-Heart-Model HBCM

**Key Features**:
- Finite element cardiac simulation
- CellML electrophysiology models
- Monodomain and bidomain solvers
- Torso/ECG simulation
- GPU acceleration

**Compatible Models from Multi-Heart-Model**:
- Luo-Rudy Dynamic
- Ten Tusscher-Panfilov 2006
- O'Hara-Rudy 2011
- Courtemanche atrial

**Publications**:
- Plank, G., et al. (2021). "The openCARP simulation environment for cardiac electrophysiology." Computer Methods and Programs in Biomedicine.

---

### 2. Chaste (Cancer, Heart and Soft Tissue Environment)

**Description**: Computational biology simulation platform with cardiac focus

**Links**:
- Website: https://chaste.github.io/
- GitHub: https://github.com/Chaste/Chaste
- Cardiac Documentation: https://chaste.github.io/components/cardiac/
- CellML Models: https://github.com/Chaste/cellml

**Integration Opportunities**:
- Convert Multi-Heart-Model Python models to CellML format
- Use Chaste for tissue simulations with Multi-Heart-Model cells
- Validation against Chaste reference implementations

**Key Features**:
- C++ simulation framework
- CellML model auto-generation
- Cardiac tissue electrophysiology
- Mechanical contraction
- Uncertainty quantification

**Publications**:
- Cooper, J., et al. (2015). "Cellular cardiac electrophysiology modeling with Chaste and CellML." Frontiers in Physiology.

---

### 3. CellML Repository

**Description**: Repository of mathematical models in CellML format

**Links**:
- CellML.org: https://www.cellml.org/
- Model Repository: https://models.physiomeproject.org/
- Chaste CellML: https://github.com/Chaste/cellml

**Integration Path**:
- Export Multi-Heart-Model models to CellML XML format
- Import CellML models to Multi-Heart-Model
- Cross-validation between platforms

**Available Models** (compatible with Multi-Heart-Model):
- Noble 1962: First cardiac AP model
- Luo-Rudy 1991/1994: Guinea pig ventricular
- Ten Tusscher 2004/2006: Human ventricular
- O'Hara-Rudy 2011: Modern human ventricular (CiPA)
- Courtemanche 1998: Human atrial
- 100+ other cardiac models

---

### 4. CiPA (Comprehensive in vitro Proarrhythmia Assay)

**Description**: FDA/EMA initiative for cardiac safety pharmacology

**Links**:
- FDA CiPA: https://www.fda.gov/drugs/news-events-human-drugs/cipa-comprehensive-vitro-proarrhythmia-assay-initiative
- CiPA Models: https://github.com/FDA/CiPA

**Multi-Heart-Model Integration**:
- ✅ Implemented: O'Hara-Rudy 2011 model (CiPA standard)
- Use Case: Drug-induced arrhythmia risk assessment
- Compatibility: Full CiPA protocol support

**Key Documents**:
- CiPA v1.0 validation data
- ORd model implementation guide
- QT prolongation metrics

---

## Model Repositories

### 1. PhysioNet / PhysioBank

**Description**: Large repository of physiological signals and models

**Links**:
- PhysioNet: https://physionet.org/
- Databases: https://physionet.org/about/database/
- Challenge Archives: https://physionet.org/challenges/

**Relevant Datasets for Multi-Heart-Model**:
- MIT-BIH Arrhythmia Database
- European ST-T Database
- MIMIC-III Clinical Database
- Sudden Cardiac Death Holter Database

**Integration Opportunities**:
- Validate HBCM against real HRV data
- Parameter estimation from clinical data
- Arrhythmia detection with Multi-Heart-Model

---

### 2. Physiome Model Repository

**Description**: Curated physiological models in multiple formats

**Links**:
- Repository: https://models.physiomeproject.org/
- Exposure: https://models.physiomeproject.org/exposure

**Compatible Formats**:
- CellML
- SBML
- FieldML

---

### 3. BioModels

**Description**: Repository of computational models of biological processes

**Links**:
- BioModels: https://www.ebi.ac.uk/biomodels/
- Search: https://www.ebi.ac.uk/biomodels/search

**Relevant Categories**:
- Cardiovascular system models
- Signal transduction models
- Calcium dynamics models

---

## Integration Opportunities

### Cross-Platform Model Validation

**Implementation Plan**:

1. **Export Multi-Heart-Model to CellML**
   ```python
   # Convert Python model to CellML XML
   from multi_heart_model.export import to_cellml

   model = LuoRudyModel()
   cellml_xml = to_cellml(model)
   ```

2. **Run in OpenCARP**
   ```bash
   # Use Multi-Heart-Model cells in tissue simulation
   openCARP +F electrophys +M LuoRudy_MultiHeart.model
   ```

3. **Validate with Chaste**
   ```cpp
   // Load Multi-Heart-Model CellML in Chaste
   CellModelFromCellML cell_model("LuoRudy_MultiHeart.cellml");
   ```

4. **Compare Results**
   - Action potential morphology
   - APD90 values
   - Calcium transients
   - Rate-dependence

---

### Surgical Robot + Physiological Monitoring

**Clinical Workflow**:

```
Patient Monitor → Multi-Heart-Model HBCM → Surgical Robot Control
     ↓                      ↓                        ↓
   HR, BP              Physio State            Adaptive Velocity
   SpO2, ECG           Alert Level             Force Scaling
                       Constraints              Emergency Stop
```

**Implementation**:

```python
from src.surgical_robotics import DVRKInterface, PhysiologicalController
from src.cardiac import LuoRudyModel
from src.coupling import HeartBrainCouplingModel

# Physiological simulation
hbcm = HeartBrainCouplingModel(cardiac_model=LuoRudyModel())
controller = PhysiologicalController(hbcm_model=hbcm)

# Robot control
dvrk = DVRKInterface(...)

# Real-time loop
while surgery_in_progress:
    # Get patient state
    physio_state = controller.get_physiological_feedback()

    # Compute safety constraints
    constraints = controller.compute_control_constraints(physio_state)

    # Adapt robot control
    if constraints.emergency_stop:
        dvrk.disable()
    else:
        robot_velocity *= constraints.max_velocity_scale
```

---

### Drug Safety with CiPA + Surgical Robotics

**Use Case**: Intraoperative drug administration

```python
from src.cardiac import OHaraRudyModel  # CiPA standard
from src.surgical_robotics import PhysiologicalController

# Drug effect on cardiac model
ord_model = OHaraRudyModel()
# Apply drug IC50 values to ion channels
# Simulate response

# Feed to robot controller
controller = PhysiologicalController(cardiac_model=ord_model)
# Robot adapts to drug-induced changes
```

---

## Data & Validation

### Recommended Datasets

**For HBCM Validation**:
1. **MIT-BIH Arrhythmia Database**
   - 48 half-hour ECG recordings
   - Normal and abnormal rhythms
   - RR interval extraction

2. **MIMIC-III**
   - ICU patient data
   - Continuous vital signs
   - Drug administration records

3. **PhysioNet/Computing in Cardiology Challenges**
   - Challenge 2017: AF Classification
   - Challenge 2020: Sleep Apnea Detection

**For Cardiac Models**:
1. **CiPA Training Data**
   - ORd model validation
   - Drug IC50 values
   - QT prolongation metrics

2. **O'Hara et al. 2011 Experimental Data**
   - Human ventricular AP recordings
   - Rate-dependence curves
   - Restitution properties

---

## Related Multi-Heart-Model Projects

### Potential Extensions

1. **Multi-Heart-Model + OpenCARP**
   - Tissue-scale simulations
   - ECG generation
   - Arrhythmia mechanisms

2. **Multi-Heart-Model + dVRK + 3D Slicer**
   - Image-guided surgery with physiological monitoring
   - Real-time visualization
   - SlicerROS2 integration

3. **Multi-Heart-Model + PhysioNet**
   - Parameter estimation from clinical data
   - Population modeling
   - Risk stratification

4. **Multi-Heart-Model + FDA CiPA**
   - Drug safety assessment
   - Proarrhythmia prediction
   - Virtual clinical trials

---

## Collaboration Guidelines

### Contributing Models

If you're from OpenCARP, Chaste, or other platforms and want to contribute:

1. **Convert your model to Multi-Heart-Model format**:
   ```python
   class YourModel:
       def get_initial_state(self) -> np.ndarray:
           # Return initial conditions

       def derivatives(self, t, state, stimulus):
           # Return state derivatives

       def step(self, t, state, dt, stimulus):
           # Time integration step
   ```

2. **Add validation tests**
3. **Document parameter sources**
4. **Submit pull request**

### Integration Requests

To request integration with Multi-Heart-Model:

1. Open GitHub issue: https://github.com/STLNFTART/Multi-Heart-Model/issues
2. Provide:
   - Platform/repository link
   - Desired integration level
   - Use cases
   - Technical requirements

---

## Citation & Attribution

When using Multi-Heart-Model with other platforms:

### Multi-Heart-Model Citation

```bibtex
@software{multi_heart_model_2025,
  title = {Multi-Heart-Model: Comprehensive Cardiovascular Modeling Platform},
  author = {Multi-Heart-Model Development Team},
  year = {2025},
  url = {https://github.com/STLNFTART/Multi-Heart-Model},
  note = {Integrates with dVRK, CRTK, AMBF, OpenCARP, Chaste, and CellML platforms}
}
```

### Platform-Specific Citations

**dVRK**: Kazanzides et al. (2014)
**CRTK**: Kazanzides et al. (2021)
**AMBF**: Munawar et al. (2019)
**OpenCARP**: Plank et al. (2021)
**Chaste**: Cooper et al. (2015)
**Luo-Rudy**: Luo & Rudy (1994)
**Ten Tusscher**: ten Tusscher & Panfilov (2006)
**O'Hara-Rudy**: O'Hara et al. (2011)
**Courtemanche**: Courtemanche et al. (1998)

---

## Quick Reference Links

### Surgical Robotics
| Platform | GitHub | Documentation |
|----------|--------|---------------|
| dVRK | https://github.com/jhu-dvrk | https://dvrk.lcsr.jhu.edu/ |
| CRTK | https://github.com/collaborative-robotics | https://collaborative-robotics.github.io/ |
| AMBF | https://github.com/WPI-AIM/ambf | https://github.com/WPI-AIM/ambf/wiki |

### Cardiac Modeling
| Platform | Website | Repository |
|----------|---------|------------|
| OpenCARP | https://opencarp.org/ | https://github.com/openCARP |
| Chaste | https://chaste.github.io/ | https://github.com/Chaste/Chaste |
| CellML | https://www.cellml.org/ | https://models.physiomeproject.org/ |

### Data Sources
| Resource | Link |
|----------|------|
| PhysioNet | https://physionet.org/ |
| MIMIC-III | https://physionet.org/content/mimiciii/ |
| CiPA | https://www.fda.gov/drugs/news-events-human-drugs/cipa |

---

## Support & Community

**Multi-Heart-Model**:
- Issues: https://github.com/STLNFTART/Multi-Heart-Model/issues
- Discussions: https://github.com/STLNFTART/Multi-Heart-Model/discussions

**Surgical Robotics Community**:
- ROS Medical Robotics: https://rosmed.github.io/
- ISMR Conference: https://ismr.gatech.edu/

**Cardiac Modeling Community**:
- Cardiac Physiome: https://www.physiome.org/
- CellML Community: https://www.cellml.org/community

---

**Last Updated**: 2025-11-23
**Version**: 1.0.0
**Maintainer**: Multi-Heart-Model Development Team
