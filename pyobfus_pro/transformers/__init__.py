"""Build-pass AST transformers for v0.5 Pro features.

Each transformer is a pure function: source -> transformed source. They run
during obfuscation, before the source is written to the dist directory.
"""
