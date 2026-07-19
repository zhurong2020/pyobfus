# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Package        | Version | Supported          |
| -------------- | ------- | ------------------ |
| pyobfus        | 0.5.x   | :white_check_mark: |
| pyobfus        | < 0.5   | :x:                |
| pyobfus-mcp    | 0.3.x   | :white_check_mark: |
| pyobfus-mcp    | < 0.3   | :x:                |

## Reporting a Vulnerability

We take the security of pyobfus seriously. If you discover a security vulnerability, please use **one** of these private channels:

### Preferred: GitHub Security Advisories

Open a private advisory at <https://github.com/zhurong2020/pyobfus/security/advisories/new>. This is a private channel between the reporter and the maintainer; the report stays confidential until a coordinated public disclosure.

### Alternative: Email

Send the report to **zhurong0525@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes (if available)

### Disclosure expectations

1. **Give us reasonable time** to respond and fix the issue before public disclosure (typically 90 days)
2. **Act in good faith** - avoid privacy violations, data destruction, and service disruption

### Please Don't:

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before we've had a chance to address it
- Exploit the vulnerability beyond what is necessary to demonstrate it

## Security Update Process

1. We will acknowledge receipt of your vulnerability report within 48 hours
2. We will provide a more detailed response within 7 days
3. We will work on a fix and keep you informed of progress
4. Once fixed, we will release a security update and credit you (unless you prefer to remain anonymous)

## Scope

This security policy applies to:

- The core `pyobfus` package
- The `pyobfus-mcp` MCP server package
- Official examples and documentation
- The CI/CD pipeline

## Out of Scope

- Vulnerabilities in dependencies (please report to the respective projects)
- Issues in third-party integrations
- Social engineering attacks
- **Bypassing the Pro trial** — see the trust boundary below

## Trust boundary: the Pro trial is not a security boundary

The 5-day Pro trial (`pyobfus-trial start`) records state in an unsigned JSON
file under the user's home directory, and `pyobfus/trial.py` ships as readable
Apache-2.0 source. Anyone who controls their own machine can edit either the
state file or the trial duration constant.

**This is known, expected, and not treated as a vulnerability.** No client-side
check inside an open-source package can be made tamper-proof: the code that
performs the check is distributed to the person it is checking. Signing the
state file, or issuing entitlements from a server, would raise the bar for
editing the *data* while leaving the *verifier* equally patchable — so we do not
ship that and describe it as protection.

The trial exists to give honest evaluators a frictionless five days. Reports of
trial bypasses are welcome as ordinary issues (thanks to
[#20](https://github.com/zhurong2020/pyobfus/issues/20) and
[#21](https://github.com/zhurong2020/pyobfus/issues/21)), but they are not
security vulnerabilities and do not need the private advisory channel.

Note that the **Community Edition is fully Apache-2.0 licensed with no file or
line limits** and involves no trial at all. The trial gates only the Pro
build-fusion mechanisms.

Genuine security issues in scope include: obfuscated output that fails to
execute correctly, the reverse-mapping tooling leaking data it should not, path
traversal or command injection in the CLI or MCP server, and supply-chain
integrity of the published artifacts.

## Recognition

We appreciate the security research community's efforts to improve pyobfus security. Contributors who report valid security issues will be:

- Credited in the security advisory (if desired)
- Mentioned in the changelog
- Added to our acknowledgments

Thank you for helping keep pyobfus and its users safe!
