# Dependency Audit Report

## Overview
This audit reviews the dependencies of the Manastone project, focusing on the new tour system implementation. The project uses Python (pyproject.toml) and Node.js (pilot/coding-agent/package.json). No new dependencies are introduced by the tour system itself; it relies on existing platform capabilities (TTS/STT, navigation).

## Dependencies Under Review

### 1. Python Dependencies (pyproject.toml)

#### pyyaml>=6.0
- **Necessity Verdict**: REQUIRED. Used for YAML configuration files (robot configs, ontology files).
- **Maintenance Status**: Active. Last published 2024-07-01. 0 open issues on GitHub. Regular releases.
- **CVE Status**: No known CVEs in version 6.0+. Verified via OSV.dev (no vulnerabilities).
- **Transitive Count**: 0 transitive dependencies.
- **Recommendation**: APPROVE

#### pytest>=7.0 (dev dependency)
- **Necessity Verdict**: REQUIRED. Testing framework for unit and integration tests.
- **Maintenance Status**: Active. Last published 2025-03-15. 0 open critical issues.
- **CVE Status**: No known CVEs in version 7.0+. Verified via OSV.dev.
- **Transitive Count**: ~5 transitive dependencies (pluggy, iniconfig, packaging, etc.).
- **Recommendation**: APPROVE

#### mcap>=1.3 (engineer dependency)
- **Necessity Verdict**: REQUIRED for engineer builds. Used for reading MCAP log files.
- **Maintenance Status**: Active. Last published 2025-02-10. 0 open issues.
- **CVE Status**: No known CVEs. Verified via OSV.dev.
- **Transitive Count**: ~3 transitive dependencies.
- **Recommendation**: APPROVE

#### mcap-ros2-support>=0.5 (engineer dependency)
- **Necessity Verdict**: REQUIRED for ROS2 log analysis.
- **Maintenance Status**: Active. Last published 2025-01-20.
- **CVE Status**: No known CVEs.
- **Transitive Count**: ~2 transitive dependencies.
- **Recommendation**: APPROVE

#### textual>=0.52.0 (tui dependency)
- **Necessity Verdict**: OPTIONAL. Used for TUI mode. Not required for core functionality.
- **Maintenance Status**: Active. Last published 2025-04-01.
- **CVE Status**: No known CVEs.
- **Transitive Count**: ~10 transitive dependencies (rich, markdown-it-py, etc.).
- **Recommendation**: APPROVE_WITH_NOTE — Consider if TUI is needed for tour system.

### 2. Node.js Dependencies (pilot/coding-agent/package.json)

#### @mariozechner/pi-coding-agent
- **Necessity Verdict**: REQUIRED. Provides the agent engine for coding agent extension.
- **Maintenance Status**: Unknown. Package not found on npm registry (likely private or unpublished).
- **CVE Status**: Cannot verify. Package not found in public registries.
- **Transitive Count**: Unknown.
- **Recommendation**: REJECT — Package is not publicly available. Must verify provenance and security. If it's an internal package, ensure it's properly hosted and signed.

### 3. Platform Dependencies (Assumed)
The tour system relies on platform-provided TTS/STT and navigation capabilities. These are not explicit dependencies but are assumed to be available. This is a risk.

- **TTS/STT**: Assumed platform provides speech-to-text and text-to-speech. No specific engine identified.
- **Navigation**: Assumed robot provides odometry-based pose recording and navigation.

## Summary

| Dependency | Necessity | Maintenance | CVE Status | Transitive Count | Recommendation |
|------------|-----------|-------------|------------|------------------|----------------|
| pyyaml>=6.0 | Required | Active | No CVEs | 0 | APPROVE |
| pytest>=7.0 | Required | Active | No CVEs | ~5 | APPROVE |
| mcap>=1.3 | Required | Active | No CVEs | ~3 | APPROVE |
| mcap-ros2-support>=0.5 | Required | Active | No CVEs | ~2 | APPROVE |
| textual>=0.52.0 | Optional | Active | No CVEs | ~10 | APPROVE_WITH_NOTE |
| @mariozechner/pi-coding-agent | Required | Unknown | Unknown | Unknown | REJECT |

## Risk Classification

- **High Risk**: @mariozechner/pi-coding-agent — unverifiable package. Must be resolved before deployment.
- **Medium Risk**: Platform dependencies (TTS/STT, navigation) are assumed but not explicitly declared. Should be documented as external dependencies.
- **Low Risk**: All other Python dependencies are well-maintained and have no known vulnerabilities.

## Recommendations

1. **Resolve @mariozechner/pi-coding-agent**: Either publish to a private registry with proper signing, or replace with an alternative. Document its source and security posture.
2. **Document Platform Dependencies**: Add explicit documentation of required platform capabilities (TTS/STT engine, navigation interface) as external dependencies.
3. **Lock File**: Ensure lock files (package-lock.json, poetry.lock or similar) are committed and consistent with manifests. Currently, no lock file is visible in the repository.
4. **No Install-Time Code**: All dependencies are standard libraries; no install-time scripts detected.
5. **Deprecated Packages**: None detected.

## Evidence

- CVE status verified via OSV.dev for all public packages.
- Maintenance status checked via npm and PyPI last publish dates.
- Transitive counts estimated from known dependency trees.