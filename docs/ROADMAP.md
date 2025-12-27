# Development Roadmap

This document outlines **future plans** for pyobfus. For released version history, see [CHANGELOG.md](../CHANGELOG.md).

**Target Users**: Individual developers and small teams
**Positioning**: Free open-source alternative to commercial tools (PyArmor, Oxyry)

---

## Current Status

See [CHANGELOG.md](../CHANGELOG.md) for the latest release and version history.

- 410+ tests with 56%+ coverage
- Full Pro feature set available

---

## Next Release (v0.3.3+)

### Pending Items
- None currently planned

### Potential Additions
- [ ] Performance optimization for large projects (1000+ files)
- [ ] Parallel file processing

---

## v0.4.0 - Ecosystem Enhancements

**Goal**: Improve user experience, build community

### P1 - Should Have

**1. Enhanced Key Obfuscation**
- Key splitting across multiple variables
- Decoy/fake keys to confuse analysis
- Key derivation from code structure
- Dynamic key reconstruction at runtime

### P2 - Nice to Have

**2. VSCode Extension**
- Right-click obfuscation
- Config file intellisense

**3. Incremental Obfuscation**
- Only process changed files
- Result caching

**4. Code Compression**
- Minify whitespace
- Reduce file size

---

## Long-term Ideas

**Future Consideration** (not yet planned):
- Professional email system with auto-responders
- License inquiry self-service automation
- Plugin system for custom transformers

---

## What We Won't Do

To maintain focus on core users (individual developers/small teams):

- **Deep Bytecode Encryption** - Too complex to maintain
- **Compile to C/Machine Code** - Cython already does this well
- **Enterprise License Server** - Not our target market
- **Compete with PyArmor Pro** - Different price/feature tier

---

## Success Metrics

### Current (v0.3.x)
- GitHub Stars: 0 → target 100+
- PyPI Downloads: 750/month → target 2K+/month
- First Pro license sale

### v0.4.0 Targets
- GitHub Stars: 300+
- PyPI Downloads: 5K+/month
- Community contributors: 5+

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

Feature requests: GitHub issues with `enhancement` tag.

---

**Last Updated**: December 27, 2025
