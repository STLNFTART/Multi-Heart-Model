# Multi-Heart-Model Wiki

Welcome to the **Multi-Heart-Model** wiki! This is a comprehensive guide to the Heart-Brain Coupling Model (HBCM) - a multi-domain physiological modeling platform.

## 🎯 Quick Links

- **[Getting Started](Getting-Started)** - Install and run your first simulation
- **[Architecture Overview](Architecture)** - Understand the system design
- **[API Reference](API-Reference)** - Detailed API documentation
- **[Examples](Examples)** - Code examples and tutorials
- **[Development Guide](Development-Guide)** - Contributing to the project

## 📊 What is the HBCM?

The Heart-Brain Coupling Model (HBCM) is a mathematical and computational framework that integrates:

1. **Core Heart-Brain Coupling**: Bidirectional neural-cardiac interactions using delay-differential equations
2. **Hardware Control Integration**: Primal Logic Processor for automotive control applications
3. **Organ-On-Chip Platform**: Drug toxicity screening with mechanistic multi-organ models
4. **Multi-Language Support**: Python (primary), D (high-performance), APL (reference)

## 🚀 Key Features

- **Minimal Dependencies**: Only NumPy + stdlib (no heavy frameworks)
- **Production Ready**: Hardware deployment paths, comprehensive testing
- **Well Documented**: 3,649 lines of documentation across 15 files
- **High Test Coverage**: ~100% of production code covered
- **Multiple Implementations**: Python, D, and APL versions

## 📈 Repository Statistics

- **Total Python LOC**: 7,271 (57 files)
- **Test LOC**: 1,024 (30+ test methods)
- **License**: MIT

## 🔬 Core Models

| Model | Purpose | LOC |
|-------|---------|-----|
| **VanDerPolOscillator** | Cardiac relaxation oscillator | 30 |
| **FitzHughNagumo** | Two-dimensional neural oscillator | 50 |
| **HeartBrainCouplingModel** | Bidirectional coupling orchestrator | 125 |
| **PrimalLogicProcessor** | Hardware integral controller | 283 |
| **OrganChipSuite** | Multi-organ drug toxicity platform | 2,942 |

## 📚 Documentation Structure

### For New Users
1. [Getting Started](Getting-Started) - Installation and first simulation
2. [Examples](Examples) - Practical code examples
3. [FAQ](FAQ) - Common questions and answers

### For Developers
1. [Architecture](Architecture) - System design and patterns
2. [API Reference](API-Reference) - Detailed API docs
3. [Development Guide](Development-Guide) - Contributing guidelines
4. [Testing Guide](Testing) - How to write and run tests

### For Specialized Use Cases
1. [Organ-On-Chip Platform](Organ-Chip-Platform) - Drug toxicity screening
2. [Hardware Integration](Hardware-Integration) - Microprocessor control systems

## 🎓 Mathematical Foundation

The coupled brain-heart dynamics are governed by delay-differential equations:

```
dn_b(t)/dt = -λ_b n_b(t) + f_b[n_h(t - Δ_bh), S_b(t)]
dn_h(t)/dt = -λ_h n_h(t) + f_h[n_b(t - Δ_hb), S_h(t)]
```

Where:
- `n_b(t)` and `n_h(t)` denote neural and cardiac activation variables
- `λ_b` and `λ_h` are decay rates for each subsystem
- `Δ_bh` and `Δ_hb` capture inter-system communication delays
- `f_b(·)` and `f_h(·)` encode coupling pathways

## 🤝 Contributing

Contributions are welcome! Please see the [Development Guide](Development-Guide) for:
- Code style conventions
- Git workflow
- Testing requirements
- Documentation standards

## 📄 License

This project is licensed under the [MIT License](https://github.com/STLNFTART/Multi-Heart-Model/blob/main/LICENSE).

## 🔗 External Resources

- [GitHub Repository](https://github.com/STLNFTART/Multi-Heart-Model)
- [Issue Tracker](https://github.com/STLNFTART/Multi-Heart-Model/issues)
- [Pull Requests](https://github.com/STLNFTART/Multi-Heart-Model/pulls)

---

**Last Updated**: 2025-11-16
**Repository Version**: See [latest release](https://github.com/STLNFTART/Multi-Heart-Model/releases)
