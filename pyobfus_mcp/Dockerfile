# Build context for the Glama listing's build/introspection check only.
# Not used to ship pyobfus-mcp (PyPI wheel is the distribution artifact).
# Keep the pin in sync with pyobfus_mcp/pyproject.toml on every MCP release —
# a stale pin makes Glama introspect an old, smaller tool surface.
FROM python:3.12-slim

RUN pip install --no-cache-dir pyobfus-mcp==0.3.10

RUN useradd --uid 1987 --create-home --shell /bin/sh mcp
USER 1987
WORKDIR /home/mcp

ENTRYPOINT ["pyobfus-mcp"]
