# Pull Request

## Summary

<!-- Provide a brief summary of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement
- [ ] Build/CI improvement
- [ ] Other (please describe):

## Motivation and Context

**Why are these changes needed?**
<!-- Describe the problem this PR solves -->

**Related issues:**
<!-- Link related issues using #issue_number -->
- Fixes #
- Related to #
- Closes #

## Changes Made

<!-- Provide a detailed list of changes -->

- **Core Changes:**
  -
  -

- **Tests:**
  -
  -

- **Documentation:**
  -
  -

- **Other:**
  -
  -

## Scientific Validation

<!-- If applicable, describe scientific validation performed -->

**Literature Support:**
- [ ] Changes are supported by peer-reviewed literature
- [ ] References added to docs/REFERENCES.md
- [ ] Not applicable (non-scientific changes)

**Physiological Validation:**
- [ ] Parameters are within physiological ranges
- [ ] Model outputs match expected behavior
- [ ] Validated against benchmarks
- [ ] Not applicable

**References:**
<!-- List relevant scientific references -->
- Author et al. (Year). Title. Journal.
-

## Testing

### Test Results

```bash
# Paste test output here
$ pytest tests/ -v

# Example:
# ===== test session starts =====
# tests/test_models.py::test_van_der_pol PASSED
# tests/test_models.py::test_fitzhugh_nagumo PASSED
# ===== 7 passed in 2.34s =====
```

### Test Coverage

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Edge cases tested
- [ ] Integration tests updated (if applicable)
- [ ] Validation scripts run successfully

**Coverage report:**
<!-- If running with --cov, paste coverage results -->

### Manual Testing

<!-- Describe any manual testing performed -->

**Test scenarios:**
1. Scenario 1: Description and results
2. Scenario 2: Description and results
3. Scenario 3: Description and results

**Expected vs. Actual:**
- Expected:
- Actual:
- Status: ✅ Pass / ❌ Fail

## Code Quality

### Style and Standards

- [ ] Code follows project style guidelines (PEP 8, type hints)
- [ ] All functions have docstrings with type hints
- [ ] Complex algorithms have explanatory comments
- [ ] Variable names are clear and descriptive
- [ ] No commented-out code or debug statements

### Performance

- [ ] No significant performance regressions
- [ ] Optimizations documented (if applicable)
- [ ] Memory usage considered
- [ ] Not applicable

### Security

- [ ] No hardcoded secrets or credentials
- [ ] Input validation added where needed
- [ ] No SQL injection or XSS vulnerabilities
- [ ] Dependencies are secure and up-to-date
- [ ] Not applicable

## Documentation

### Updated Documentation

- [ ] README.md (if user-facing changes)
- [ ] docs/QUICK_REFERENCE.md (if new parameters or features)
- [ ] docs/ARCHITECTURE_OVERVIEW.md (if architectural changes)
- [ ] CLAUDE.md (if development workflow changes)
- [ ] API docstrings (for new/modified functions)
- [ ] Examples in examples/ directory
- [ ] Jupyter notebooks (if applicable)
- [ ] No documentation updates needed

### Documentation Completeness

- [ ] All new features are documented
- [ ] All parameters are explained
- [ ] Usage examples provided
- [ ] Limitations and caveats noted
- [ ] Migration guide provided (if breaking changes)

## Backward Compatibility

- [ ] Fully backward compatible
- [ ] Deprecation warnings added for old functionality
- [ ] Breaking changes documented in migration guide
- [ ] Not applicable (new feature)

**Breaking changes:**
<!-- If breaking, describe the impact and migration path -->

## Examples

### Before

```python
# Example of old behavior (if applicable)
```

### After

```python
# Example of new behavior showing the changes
from src.module import NewFeature

# Demonstrate the new functionality
result = NewFeature().compute()
```

## Screenshots / Plots

<!-- If applicable, add screenshots or plots showing results -->

## Deployment Considerations

### Dependencies

- [ ] No new dependencies added
- [ ] New dependencies added (listed below)
- [ ] Dependencies updated (listed below)

**New/Updated dependencies:**
- Package: version (reason)
-

### Configuration

- [ ] No configuration changes
- [ ] Configuration changes (documented below)
- [ ] Default configuration still works

**Configuration changes:**
<!-- Describe any changes to config/default.yaml or other configs -->

### Migration

- [ ] No migration required
- [ ] Migration required (steps documented below)

**Migration steps:**
1. Step 1
2. Step 2
3. Step 3

## Checklist

### Before Submitting

- [ ] I have read [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] I have read [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

### Commit History

- [ ] Commits are logical and well-organized
- [ ] Commit messages are clear and descriptive
- [ ] No merge commits (rebased on latest main)
- [ ] No extraneous commits (squashed if needed)

### Review Readiness

- [ ] PR title is clear and descriptive
- [ ] PR description is complete
- [ ] All checklist items are addressed
- [ ] Ready for review

## Additional Notes

<!-- Any additional information, context, or screenshots -->

## Reviewer Notes

<!-- Notes for reviewers: areas to focus on, known issues, etc. -->

**Focus areas for review:**
-
-

**Known limitations:**
-
-

**Follow-up work:**
-
-

---

## For Maintainers

**Merge Strategy:**
- [ ] Squash and merge (default)
- [ ] Rebase and merge (clean history)
- [ ] Merge commit (preserve full history)

**Post-Merge Actions:**
- [ ] Update CHANGELOG.md
- [ ] Create release (if applicable)
- [ ] Update documentation site
- [ ] Notify contributors
- [ ] Close related issues

---

Thank you for contributing to Multi-Heart-Model! 🎉
