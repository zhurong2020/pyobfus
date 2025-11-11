# Development Roadmap

This document outlines the planned technical features and improvements for pyobfus.

## Current Status

✅ **Phase 1 Complete** (January 2025)
- Core obfuscation engine with AST-based name mangling
- Multi-file support with configuration system
- Test suite with 32 tests, 51% coverage
- CI/CD pipeline for Python 3.8-3.12 across multiple OS
- Public release preparation complete
- GitHub Pages documentation live

## Planned Features

### High Priority

**Cross-file Import Mapping**
- Properly handle cross-file function/class references
- Maintain naming consistency across obfuscated modules
- Essential for large multi-file projects

**Performance Optimization**
- Profile and optimize transformation pipeline
- Improve obfuscation speed for large codebases
- Reduce memory usage during processing

**Enhanced Configuration**
- Configuration templates for common project types
- Better validation and error reporting
- Extended exclude patterns and customization

### Medium Priority

**Advanced Obfuscation Techniques**
- Control flow flattening for if/else structures
- Additional string encoding methods
- Dead code injection options

**Code Analysis Features**
- Obfuscation strength metrics
- Complexity analysis reporting
- Compatibility checks

**Development Tools Integration**
- VSCode extension for easy obfuscation
- CI/CD pipeline plugins (GitHub Actions, GitLab CI)
- Pre-commit hooks support

### Low Priority / Research

**Incremental Obfuscation**
- Only re-obfuscate changed files
- Result caching for faster iterations
- Watch mode for development

**Bytecode-level Protection**
- Additional .pyc file obfuscation
- Investigation of bytecode manipulation techniques

**Plugin System**
- Allow custom transformation plugins
- Community-driven extensions

## Technical Improvements

### Code Quality
- Increase test coverage to 80%+
- Comprehensive integration test suite
- Performance benchmarking framework

### Compatibility
- Support for newer Python versions (3.13+)
- Better handling of modern Python syntax features
- Improved error messages and debugging

### Documentation
- API documentation with examples
- Advanced usage guides
- Architecture documentation

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Feature requests can be submitted via GitHub issues with the `enhancement` tag.

---

**Last Updated**: November 2025
