# Contributing to Multi-Heart-Model

Thank you for your interest in contributing to the Multi-Heart-Model project! We welcome contributions from the community to help advance cardiovascular modeling and clinical education.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Getting Help](#getting-help)

---

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
- Check the [existing issues](https://github.com/STLNFTART/Multi-Heart-Model/issues) to avoid duplicates
- Use the latest version of the code
- Collect relevant information (error messages, system details, reproduction steps)

**Submit a bug report:**
- Use the bug report issue template
- Provide a clear, descriptive title
- Include detailed reproduction steps
- Describe expected vs. actual behavior
- Include relevant code snippets, error messages, and system information

### Suggesting Enhancements

We welcome feature requests and enhancement suggestions:
- Use the feature request issue template
- Clearly describe the proposed functionality
- Explain the motivation and use cases
- Consider backward compatibility
- Link to relevant literature or references when applicable

### Contributing Code

We accept contributions in several areas:
- **Core Models**: New physiological models (cardiac, neural, organ systems)
- **Validation**: Additional benchmarks, clinical data comparisons
- **Documentation**: Tutorials, examples, improved explanations
- **Testing**: New test cases, improved coverage
- **Performance**: Optimization, algorithm improvements
- **Integration**: Hardware interfaces, data pipeline enhancements

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- (Optional) D compiler (ldc2) for D language components
- (Optional) Jupyter for running notebooks

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model

# No installation required for core models (minimal dependencies)
# Optional: Install development dependencies
pip install pytest pytest-cov matplotlib numpy jupyter

# Optional: Build D language components
make build
```

### Run Tests

```bash
# Run Python tests
pytest tests/ -v

# Run validation scripts
python test_new_modules.py
python validate_integration.py
python validate_organchip.py

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the coding standards (see below)
- Write tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Check code style (if using linters)
flake8 src/
mypy src/
```

### 4. Commit Your Changes

```bash
# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "Add feature: brief description

Detailed explanation of changes:
- What was added/changed
- Why it was necessary
- How it was implemented
- References to issues or literature"
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request via GitHub UI or gh CLI
gh pr create --title "Add feature: description" --body "Detailed description"
```

---

## Coding Standards

### Python Style Guide

**Follow PEP 8** with these conventions:

```python
# Type hints on all functions
def derivatives(self, t: float, state: Tuple[float, float],
                input_drive: float = 0.0) -> Tuple[float, float]:
    """Compute derivatives with full type annotations."""
    pass

# Dataclasses for configuration
from dataclasses import dataclass

@dataclass
class ModelParameters:
    """Type-safe parameter container."""
    param1: float = 1.0
    param2: float = 0.5

# Comprehensive docstrings (Google style)
def simulate(self, initial_state, t_span, dt):
    """
    Simulate the coupled system.

    Args:
        initial_state: Tuple (v, w, x, y) - initial conditions
        t_span: Tuple (t_start, t_end) - time interval
        dt: float - time step size (seconds)

    Returns:
        List of (time, state) tuples

    Raises:
        ValueError: If dt <= 0 or t_span invalid
    """
    pass
```

### Naming Conventions

- **Classes**: PascalCase (`VanDerPolOscillator`, `HeartBrainCouplingModel`)
- **Functions/Methods**: snake_case (`compute_control`, `extract_series`)
- **Constants**: UPPER_CASE (`PLANCK_SCALE`, `IC50_hERG`)
- **Private methods**: `_delayed_state`, `_compute_input`
- **Module files**: snake_case matching class name

### File Organization

- One main class per file
- Supporting classes in same file as main class
- `__init__.py` exports define public API
- Tests mirror source structure (`src/cardiac/` → `tests/test_cardiac/`)

### Mathematical Conventions

- **Time variables**: `t` (current time), `dt` (timestep), `t_span` (interval)
- **State representation**:
  - Neural: `(v, w)` (voltage, recovery)
  - Cardiac: `(x, y)` (position, velocity)
  - Combined: `(v, w, x, y)` (neural first, cardiac second)
- **Units**: All times in seconds unless explicitly documented otherwise

---

## Testing Guidelines

### Test Structure

**Unit Tests** (`tests/test_models.py`):
- Test individual model derivatives
- Test parameter initialization
- Test edge cases and boundary conditions
- Use `pytest.approx` for float comparisons

**Integration Tests** (`tests/integration/`):
- Test coupled system behavior
- Test delay lookups
- Test end-to-end workflows

**Validation Tests**:
- Compare against literature benchmarks
- Test physiological parameter ranges
- Verify clinical scenarios

### Testing Best Practices

```python
import pytest

# Parameterized tests for multiple scenarios
@pytest.mark.parametrize(
    "state,input_drive,expected",
    [
        ((0.0, 0.0), 0.0, (0.0, pytest.approx(0.233))),
        ((1.0, -0.5), 0.1, (pytest.approx(1.533), pytest.approx(0.9))),
    ],
)
def test_model_derivatives(state, input_drive, expected):
    model = MyModel()
    result = model.derivatives(0.0, state, input_drive=input_drive)
    assert result == expected

# Use fixtures for common setups
@pytest.fixture
def coupling_model():
    """Provide standard coupling model for tests."""
    from src.coupling import HeartBrainCouplingModel
    return HeartBrainCouplingModel()

# Test edge cases
def test_zero_timestep_raises():
    model = MyModel()
    with pytest.raises(ValueError):
        model.simulate(initial_state=(0, 0), t_span=(0, 10), dt=0)
```

### Coverage Expectations

- **Unit tests**: Aim for 100% coverage of core models
- **Integration tests**: Cover all coupling mechanisms
- **Edge cases**: Test boundary conditions, zero inputs, extreme parameters

---

## Documentation

### Code Documentation

- **Docstrings**: All public classes, methods, and functions
- **Type hints**: All function signatures
- **Inline comments**: For complex algorithms or non-obvious logic
- **References**: Cite literature sources in docstrings

### External Documentation

When adding significant features, update:
- `docs/QUICK_REFERENCE.md` - Add parameter tables, examples
- `docs/ARCHITECTURE_OVERVIEW.md` - Add architectural details
- `CLAUDE.md` - Update development guide if needed
- `README.md` - Update if user-facing changes

### Examples and Tutorials

- Add demonstration scripts to `examples/`
- Create Jupyter notebooks for interactive features
- Include visualizations when helpful
- Document expected outputs

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why are these changes needed?

## Changes
- Bullet point list of specific changes
- Include new files, modified files
- Note any breaking changes

## Testing
- Describe testing performed
- Include test results
- Note any edge cases tested

## References
- Link to related issues
- Cite relevant literature
- Link to related PRs

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainer reviews code quality, design, and tests
3. **Discussion**: Address reviewer comments and suggestions
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge or rebase depending on commit structure

### After Merge

- Your contribution will be acknowledged in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Major features may be highlighted in release notes
- You'll be notified if issues arise with your contribution

---

## Getting Help

### Resources

- **Documentation**: [docs/](docs/) - Comprehensive technical documentation
- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **Developer Guide**: [CLAUDE.md](CLAUDE.md)
- **Architecture**: [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
- **Examples**: [examples/](examples/) - Working code examples

### Communication

- **Issues**: [GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues) - Bug reports, feature requests
- **Discussions**: [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions) - Questions, ideas
- **Wiki**: [Project Wiki](wiki/) - Extended guides and tutorials

### Common Questions

**Q: How do I add a new physiological model?**
A: See [CLAUDE.md](CLAUDE.md) section "Extension Patterns" for detailed examples.

**Q: How do I validate my model against literature?**
A: See [docs/VALIDATION.md](docs/VALIDATION.md) for validation framework and examples.

**Q: What physiological parameters are valid?**
A: See [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for parameter ranges and references.

**Q: How do I run the D language components?**
A: Run `make build` to compile, then execute `./primal_overlay`.

---

## Recognition

We value all contributions, whether code, documentation, testing, or community support. All contributors are acknowledged in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md) - Complete list of contributors
- Release notes for significant contributions
- Repository insights and statistics

---

## License

By contributing to Multi-Heart-Model, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Thank You!

Your contributions help advance cardiovascular modeling, clinical education, and medical research. We appreciate your time and effort!

For detailed development information, see [CLAUDE.md](CLAUDE.md) - our comprehensive AI assistant and developer guide.

---

**Questions?** Open an issue or start a discussion. We're here to help!
