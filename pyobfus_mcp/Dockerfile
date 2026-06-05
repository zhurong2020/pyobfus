FROM python:3.12-slim

RUN pip install --no-cache-dir pyobfus-mcp==0.2.0

RUN useradd --uid 1987 --create-home --shell /bin/sh mcp
USER 1987
WORKDIR /home/mcp

ENTRYPOINT ["pyobfus-mcp"]
