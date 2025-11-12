# Multi-Heart-Model Documentation Index

This index provides a comprehensive guide to understanding the Multi-Heart-Model codebase architecture and structure.

## Documentation Files

### Quick Start & References (Read These First)
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Start here for quick answers
   - Quick start code examples
   - Key files and their purposes
   - Parameter ranges and defaults
   - Common usage patterns
   - Troubleshooting guide
   - **Best for**: Developers familiar with the project or quick lookups

2. **[CODEBASE_ANALYSIS_SUMMARY.md](CODEBASE_ANALYSIS_SUMMARY.md)** - Executive overview
   - High-level summary of architecture
   - Key findings and strengths
   - Technical specifications
   - Next steps for integration
   - **Best for**: Project managers and system architects

### Detailed Technical Documentation (Read For Deep Understanding)
3. **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - Comprehensive technical guide
   - Complete module descriptions
   - All existing models and their specifications
   - Architecture patterns and design decisions
   - Coupling and integration mechanisms
   - Testing framework details
   - Extensibility patterns
   - **Best for**: Developers implementing new features

4. **[ARCHITECTURE_DIAGRAM.txt](ARCHITECTURE_DIAGRAM.txt)** - Visual reference
   - System architecture diagrams (ASCII)
   - Data flow illustrations
   - Component relationship diagrams
   - Testing infrastructure overview
   - Configuration structure
   - **Best for**: Understanding system flow visually

### Original Project Documentation
5. **[architecture.md](architecture.md)** - Original architecture document
   - Mathematical formulation
   - Subsystem responsibilities
   - Configuration flow
   - Output specifications

6. **[hbcm_overview.md](hbcm_overview.md)** - HBCM model overview
   - Core mathematical formulation
   - Model capabilities
   - Use cases and applications
   - Workflow integration

7. **[microprocessor_motorhand_integration.md](microprocessor_motorhand_integration.md)** - Hardware integration details
   - Primal Logic Processor specifications
   - MotorHandPro integration
   - Hardware deployment information

---

## How to Navigate This Documentation

### I'm a New Developer
1. Start with **QUICK_REFERENCE.md** (5 min read)
2. Review **ARCHITECTURE_DIAGRAM.txt** for visual understanding (10 min)
3. Read **ARCHITECTURE_OVERVIEW.md** for complete context (30 min)
4. Examine code in `src/` directory
5. Run tests: `pytest tests/ -v`

### I'm Adding a New Organ System
1. Review **ARCHITECTURE_OVERVIEW.md** section "10. PATTERNS FOR ORGAN CHIP SYSTEM INTEGRATION"
2. Check **QUICK_REFERENCE.md** "Integration Testing Checklist"
3. Study existing models in `src/cardiac/` and `src/neural/`
4. Follow the modular composition pattern
5. Add comprehensive tests

### I'm Optimizing for Performance
1. Read **ARCHITECTURE_OVERVIEW.md** section "9. PERFORMANCE CHARACTERISTICS"
2. Review **QUICK_REFERENCE.md** "Performance Tips"
3. Profile using Python's cProfile or pytest-benchmark
4. Consider upgrading from Euler to RK4 integration
5. Evaluate vectorization opportunities

### I'm Preparing for Hardware Deployment
1. Review **CODEBASE_ANALYSIS_SUMMARY.md** "Hardware Deployment Ready"
2. Study `src/integration/motorhand_bridge.py` for QUANT interface
3. Review Arduino code generation in `generate_arduino_interface()`
4. Read **QUICK_REFERENCE.md** "Hardware Deployment Path"
5. Follow integration testing checklist

### I'm Debugging an Issue
1. Check **QUICK_REFERENCE.md** "Troubleshooting" section
2. Review relevant test file for expected behavior
3. Consult **ARCHITECTURE_OVERVIEW.md** for implementation details
4. Check parameter ranges in **QUICK_REFERENCE.md**

---

## Key Concepts Quick Links

### Models
- **Neural Model**: See ARCHITECTURE_OVERVIEW.md § 2.B
- **Cardiac Model**: See ARCHITECTURE_OVERVIEW.md § 2.A
- **Coupling Model**: See ARCHITECTURE_OVERVIEW.md § 2.C

### Systems
- **Primal Logic Processor**: See ARCHITECTURE_OVERVIEW.md § 2.D
- **Motor Integration**: See ARCHITECTURE_OVERVIEW.md § 2.E

### Patterns
- **Model Interface**: See ARCHITECTURE_OVERVIEW.md § 3.A
- **Coupling Pattern**: See ARCHITECTURE_OVERVIEW.md § 3.B
- **Extensibility Pattern**: See ARCHITECTURE_OVERVIEW.md § 10

### Testing
- **Unit Tests**: See ARCHITECTURE_OVERVIEW.md § 6
- **Integration Tests**: See ARCHITECTURE_DIAGRAM.txt "TESTING & VALIDATION"

### Configuration
- **YAML Configuration**: See ARCHITECTURE_DIAGRAM.txt "CONFIGURATION SYSTEM"
- **Parameter Ranges**: See QUICK_REFERENCE.md "Parameter Ranges & Defaults"

---

## Code Navigation

### Source Code Structure
```
src/
├── cardiac/         → VanDerPolOscillator model
├── neural/          → FitzHughNagumo model
├── coupling/        → HeartBrainCouplingModel orchestrator
├── microprocessor/  → PrimalLogicProcessor controller
└── integration/     → MotorHandBridge interface
```

### Test Files
```
tests/
├── test_models.py                           → Unit tests
└── integration/test_microprocessor_motorhand.py  → Integration tests
```

### Configuration
```
config/
└── default.yaml     → YAML parameters
```

### Examples
```
examples/
└── microprocessor_motorhand_demo.py  → Complete demo script
```

---

## Quick Facts

| Metric | Value |
|--------|-------|
| Total Python LOC | 1,153 |
| Test Coverage | ~100% of production code |
| Test Methods | 30+ |
| Main Modules | 5 |
| Dependencies | NumPy (core only) |
| Default Timestep | 0.01s (100 Hz) |
| Integration Pattern | Explicit Euler |
| State Dimensionality | 4D (extendable) |
| Control Performance | 75% jerk reduction |
| Hardware Target | SkyWater 90nm |

---

## Documentation Quality Levels

### Level 1: Quick Answers (QUICK_REFERENCE.md)
- Quick start examples
- Parameter tables
- Common patterns
- Troubleshooting

### Level 2: Executive Overview (CODEBASE_ANALYSIS_SUMMARY.md)
- High-level architecture
- Key findings
- Next steps
- Conclusions

### Level 3: Technical Details (ARCHITECTURE_OVERVIEW.md)
- Complete module descriptions
- All equations and mathematics
- Data structures
- Integration mechanisms

### Level 4: Visual Understanding (ARCHITECTURE_DIAGRAM.txt)
- ASCII diagrams
- Data flow illustrations
- Component relationships

### Level 5: Deep Dive (Original documentation)
- Research background
- Mathematical derivations
- Hardware specifications

---

## Common Tasks & Documentation

### Task: Understand basic model structure
**Read**: QUICK_REFERENCE.md → Module Relationships
**Time**: 5 minutes

### Task: Add a new organ system
**Read**: ARCHITECTURE_OVERVIEW.md § 10 → QUICK_REFERENCE.md § Integration Testing Checklist
**Time**: 30 minutes planning + implementation

### Task: Modify coupling parameters
**Read**: QUICK_REFERENCE.md § Parameter Ranges & Defaults
**Time**: 5 minutes

### Task: Optimize for performance
**Read**: ARCHITECTURE_OVERVIEW.md § 9 → QUICK_REFERENCE.md § Performance Tips
**Time**: 20 minutes analysis + optimization

### Task: Deploy to hardware
**Read**: CODEBASE_ANALYSIS_SUMMARY.md → QUICK_REFERENCE.md § Hardware Deployment Path
**Time**: 2-4 hours

### Task: Debug simulation divergence
**Read**: QUICK_REFERENCE.md § Troubleshooting → ARCHITECTURE_OVERVIEW.md relevant section
**Time**: 10-30 minutes

---

## References to Code

When reading documentation, you can jump to actual code files:

- **Cardiac model**: `/src/cardiac/van_der_pol.py`
- **Neural model**: `/src/neural/fhn.py`
- **Coupling model**: `/src/coupling/hbcm.py`
- **Primal Logic**: `/src/microprocessor/primal_processor.py`
- **Control utilities**: `/src/microprocessor/control_system.py`
- **Motor bridge**: `/src/integration/motorhand_bridge.py`
- **Unit tests**: `/tests/test_models.py`
- **Integration tests**: `/tests/integration/test_microprocessor_motorhand.py`
- **Example**: `/examples/microprocessor_motorhand_demo.py`

---

## How Documentation Connects

```
QUICK_REFERENCE.md (Start here)
    ↓
    ├→ ARCHITECTURE_DIAGRAM.txt (Visual overview)
    │   ↓
    └→ ARCHITECTURE_OVERVIEW.md (Deep technical details)
        ↓
        └→ CODEBASE_ANALYSIS_SUMMARY.md (Executive summary)
            ↓
            └→ Original documentation (Research details)
```

---

## Feedback & Updates

This documentation was generated on: **November 12, 2025**

For updates or clarifications:
1. Check original `.md` files in the `docs/` directory
2. Review relevant code files in `src/`
3. Run test suite to validate understanding
4. Refer to example scripts in `examples/`

---

## Version Information

- **Documentation Version**: 1.0
- **Repository**: Multi-Heart-Model
- **License**: MIT
- **Patent**: U.S. Provisional Patent Application No. 63/842,846
- **Status**: Production-ready

---

**Last Updated**: November 12, 2025
**Total Documentation Pages**: 4 comprehensive guides + this index
**Total Words**: ~30,000
**Code References**: 100+ specific file references
**Diagrams**: 5+ ASCII diagrams
