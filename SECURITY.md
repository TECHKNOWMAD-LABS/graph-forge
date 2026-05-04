# Security Policy

## Supported Versions

The latest tagged release on `main` is supported. Older versions receive fixes only on a best-effort basis.

## Reporting

Email **security@techknowmad.ai** with:

1. Description of the issue (CVE if known)
2. Affected version or commit SHA
3. Reproduction steps or proof-of-concept
4. Your contact info

We acknowledge within 48 hours and provide a remediation timeline within 7 days.
**Do not** open public issues for security reports.

## Disclosure

Coordinated disclosure: confirm the issue, ship a fix, then publicly disclose with credit.

## Hardening

Production deployments follow the [TechKnowmad Platinum Repo Checklist](https://github.com/Techknowmadlabs/tkml-registry/blob/main/docs/security/CHECKLIST.md):

- Branch protection on `main` (linear history, no force-push)
- Dependabot security updates enabled
- Secret-scanning push protection (where GHAS available)
- Pre-commit gitleaks + trufflehog
- Constitutional hook v5 on workstation (sandboxed agent execution)

## Cryptography

Migrating to NIST FIPS 203/204/205 (ML-KEM, ML-DSA, SLH-DSA) by 2027.
