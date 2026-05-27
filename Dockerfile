# Dockerfile for regintel-mcp — used by the Glama MCP registry for health checks
# and introspection. The image installs the package via pip and exposes the
# `regintel-mcp` CLI as the entrypoint (which runs the MCP server over stdio).
#
# Notes for reviewers:
# - The server starts cleanly without REGINTEL_API_KEY (it only enforces the
#   key at tool-call time, not at startup). Glama introspection (initialize,
#   tools/list) therefore passes without secrets.
# - REGINTEL_API_KEY is set to a stub value so server startup logs a warning
#   instead of being silent — useful when debugging the container.
# - The base image uses python:3.12-slim for a small footprint (~150 MB).

FROM python:3.12-slim

WORKDIR /app

# Copy project metadata first for layer caching.
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install the package and its runtime deps. `pip install .` resolves the
# pyproject.toml, registers the `regintel-mcp` console script, and pulls in
# `mcp[cli]>=1.2.0` and `httpx>=0.27.0`.
RUN pip install --no-cache-dir .

# Glama / clients can override these at runtime. The stub value makes
# the server log a single warning at startup instead of crashing.
ENV REGINTEL_API_KEY=glama-introspection-stub \
    REGINTEL_API_BASE=https://api.regintelapi.com \
    PYTHONUNBUFFERED=1

# MCP servers communicate over stdio by default. No EXPOSE / port needed.
ENTRYPOINT ["regintel-mcp"]
