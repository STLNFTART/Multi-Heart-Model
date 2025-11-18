# Security Policy

## Overview

The Multi-Heart-Model project takes security seriously. This document outlines our security policy, including supported versions, how to report vulnerabilities, and security best practices for using this software.

**IMPORTANT DISCLAIMER**: This software is intended for research and educational purposes. It is NOT approved for clinical decision-making, patient diagnosis, or treatment. Always consult qualified healthcare professionals for medical decisions.

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| main    | :white_check_mark: | Active development |
| 1.x.x   | :white_check_mark: | Security fixes |
| < 1.0   | :x:                | No longer supported |

**Recommendation**: Always use the latest release for security updates and bug fixes.

---

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. **DO** report privately using one of these methods:
   - GitHub Security Advisories (preferred): [Security tab](https://github.com/STLNFTART/Multi-Heart-Model/security/advisories)
   - Email project maintainers directly (see repository contacts)
   - Private message to repository maintainers

### What to Include

Please provide:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity assessment
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Affected Components**: Which files, modules, or features are affected
- **Suggested Fix**: If you have ideas for remediation
- **CVE Information**: If a CVE has been assigned
- **Your Contact**: For follow-up questions

### Response Timeline

- **Initial Response**: Within 48 hours
- **Vulnerability Assessment**: Within 1 week
- **Fix Development**: Depends on severity (critical issues prioritized)
- **Public Disclosure**: After fix is released (coordinated disclosure)

### Coordinated Disclosure

We follow responsible disclosure practices:
- We will work with you to understand and validate the issue
- We will develop and test a fix
- We will coordinate public disclosure timing with you
- We will credit you in the security advisory (unless you prefer anonymity)

---

## Security Considerations

### Medical and Clinical Use

**CRITICAL**: This software is for research and education only:

- **Not FDA Approved**: Not approved for clinical use or medical devices
- **Not Validated for Diagnosis**: Do not use for patient diagnosis or treatment
- **Research Tool**: Intended for academic research and education
- **No Warranty**: Provided "as-is" without warranty (see LICENSE)
- **Professional Consultation**: Always consult qualified healthcare professionals

### Data Privacy

**Protected Health Information (PHI)**:
- **DO NOT** use real patient data without proper IRB approval and HIPAA compliance
- **DO NOT** commit PHI or sensitive data to the repository
- **DO** anonymize any clinical data used for research
- **DO** comply with applicable data protection regulations (HIPAA, GDPR, etc.)

**Data Security**:
- Encrypt sensitive data at rest and in transit
- Use secure communication channels (SSH, HTTPS, VPN)
- Follow your institution's data security policies
- See `security/zerotier/` for secure network configuration examples

### Code Security

**Dependency Management**:
- Minimal dependencies (NumPy + stdlib) reduces attack surface
- Regularly update dependencies to patched versions
- Review `requirements.txt` and `dub.json` for known vulnerabilities
- Use `pip install --upgrade` and `dub upgrade` regularly

**Input Validation**:
- All models validate input parameters
- Type hints and runtime checks prevent invalid states
- Sanitize user inputs in web interfaces and APIs
- Validate file inputs before processing

**Code Injection**:
- Never use `eval()` or `exec()` with user input
- Sanitize any dynamic code generation
- Use parameterized queries for databases
- Validate configuration file contents

### Network Security

**ZeroTier Configuration** (see `security/zerotier/`):
- Use encrypted peer-to-peer connections
- Implement role-based access control
- Configure firewall rules appropriately
- Isolate research networks from production systems

**Remote Access**:
- Use SSH key authentication (disable password auth)
- Implement multi-factor authentication when possible
- Use VPN or ZeroTier for secure remote access
- Monitor and log access attempts

### Hardware Integration

**Primal Logic Processor / QUANT System**:
- Validate control signals before hardware output
- Implement safety limits and bounds checking
- Use watchdog timers for critical systems
- Follow automotive/medical device security standards
- Maintain physical security of hardware interfaces

---

## Security Best Practices

### For Developers

**Code Review**:
- All code changes require review before merge
- Security-sensitive changes require additional scrutiny
- Use static analysis tools (mypy, flake8, bandit)
- Follow secure coding guidelines

**Testing**:
- Include security test cases
- Test boundary conditions and edge cases
- Validate error handling
- Test with invalid/malicious inputs

**Secrets Management**:
- NEVER commit secrets, API keys, or credentials
- Use environment variables or secure vaults
- Add sensitive files to `.gitignore`
- Rotate credentials regularly

### For Users

**Installation**:
- Clone from official repository only
- Verify repository authenticity
- Use official releases and tags
- Check file integrity (checksums, signatures)

**Configuration**:
- Review configuration files before use
- Use secure default settings
- Restrict file permissions appropriately
- Keep configuration files out of version control if they contain secrets

**Execution**:
- Run with minimal necessary privileges
- Use virtual environments for Python
- Isolate from production systems
- Monitor system resources and logs

---

## Known Security Considerations

### Numerical Stability

- **Issue**: Euler integration can become unstable with large timesteps
- **Impact**: Incorrect simulation results
- **Mitigation**: Use small timesteps (dt ≤ 0.001), validate outputs
- **Severity**: Low (research quality issue, not security vulnerability)

### Configuration Files

- **Issue**: YAML configuration files could contain malicious code if using unsafe loaders
- **Mitigation**: Use `yaml.safe_load()` only (implemented)
- **Severity**: Low (controlled environment expected)

### D Language Components

- **Issue**: Compiled D executables could have memory safety issues
- **Mitigation**: Use latest ldc2 compiler, test thoroughly
- **Severity**: Low (optional components)

---

## Compliance and Regulations

### Research Compliance

- **IRB Approval**: Obtain IRB approval for human subjects research
- **Animal Research**: Follow IACUC guidelines for animal studies
- **Data Protection**: Comply with HIPAA, GDPR, and local regulations
- **Export Control**: Check export control regulations for your jurisdiction

### Medical Device Regulations

**If adapting for medical devices**:
- **FDA**: Follow FDA guidance for medical device software
- **CE Mark**: Comply with EU Medical Device Regulation (MDR)
- **ISO 13485**: Implement quality management system
- **IEC 62304**: Follow medical device software lifecycle processes
- **Risk Management**: Conduct ISO 14971 risk analysis

### Software Licenses

- **MIT License**: See [LICENSE](LICENSE) for terms
- **Third-Party**: Review licenses of all dependencies
- **Attribution**: Maintain license notices and attributions

---

## Security Monitoring

### Continuous Monitoring

We monitor:
- GitHub security advisories for dependencies
- CVE databases for known vulnerabilities
- Security scanning tools (Dependabot, CodeQL)
- Community reports and feedback

### Audit Trail

- Git history provides complete audit trail
- CI/CD logs track automated testing
- Release notes document security fixes
- GitHub provides transparency for all changes

---

## Incident Response

### In Case of Security Incident

1. **Identify**: Detect and confirm the security issue
2. **Contain**: Prevent further damage or exposure
3. **Investigate**: Determine root cause and scope
4. **Remediate**: Develop and deploy fix
5. **Notify**: Inform affected users and stakeholders
6. **Document**: Record lessons learned and update processes

### Communication

- Security advisories posted to GitHub Security tab
- Critical issues announced via GitHub releases
- Users notified through GitHub watch/star notifications
- Updates posted to discussions and documentation

---

## Resources

### Security Documentation

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FDA Medical Device Cybersecurity](https://www.fda.gov/medical-devices/digital-health-center-excellence/cybersecurity)

### Project Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Secure development practices
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines
- [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) - Technical details
- [security/zerotier/](security/zerotier/) - Network security configuration

---

## Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

<!-- Contributors who report security issues will be listed here -->

*Be the first to help improve our security!*

---

## Disclaimer

**NO WARRANTY**: This software is provided "as-is" under the MIT License without warranty of any kind. See [LICENSE](LICENSE) for full terms.

**RESEARCH ONLY**: This software is for research and educational purposes. It is not approved for clinical use, medical diagnosis, or treatment decisions.

**USER RESPONSIBILITY**: Users are responsible for:
- Ensuring appropriate use of the software
- Compliance with applicable laws and regulations
- Proper validation for their specific use cases
- Security of their own systems and data

---

## Contact

For security issues and questions:

- **Security Advisories**: [GitHub Security Tab](https://github.com/STLNFTART/Multi-Heart-Model/security)
- **General Issues**: [GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues)
- **Discussions**: [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions)

---

**Last Updated**: 2025-11-18
**Version**: 1.0

Thank you for helping keep Multi-Heart-Model secure!
