---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Go to '...'
2. Run command '...'
3. Use parameters '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Error Messages

```
Paste any error messages, stack traces, or relevant output here
```

## Environment

**System Information:**
- OS: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- Python Version: [e.g., 3.10.5]
- NumPy Version: [e.g., 1.24.0]
- Git Commit/Branch: [e.g., main, commit abc123]

**Optional (if relevant):**
- D Compiler Version: [e.g., ldc2 1.35.0]
- Hardware: [if using Primal Logic Processor or QUANT]

## Code Sample

```python
# Minimal code sample that reproduces the issue
from src.cardiac import VanDerPolOscillator

model = VanDerPolOscillator()
# ... rest of the code
```

## Screenshots

If applicable, add screenshots or plots to help explain the problem.

## Additional Context

Add any other context about the problem here:
- Does this happen consistently or intermittently?
- Did this work in a previous version?
- Any relevant configuration files or parameters?
- Related issues or pull requests?

## Possible Solution

If you have ideas on how to fix the bug, please describe them here.

## Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I am using the latest version of the code
- [ ] I have included all relevant information above
- [ ] I have provided a minimal code sample to reproduce the issue
- [ ] I have included error messages and stack traces
