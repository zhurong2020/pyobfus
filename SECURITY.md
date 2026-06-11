# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Package        | Version | Supported          |
| -------------- | ------- | ------------------ |
| pyobfus        | 0.4.x   | :white_check_mark: |
| pyobfus        | < 0.4   | :x:                |
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

## Recognition

We appreciate the security research community's efforts to improve pyobfus security. Contributors who report valid security issues will be:

- Credited in the security advisory (if desired)
- Mentioned in the changelog
- Added to our acknowledgments

Thank you for helping keep pyobfus and its users safe!
