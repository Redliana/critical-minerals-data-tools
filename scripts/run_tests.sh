#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER_PY="${ROOT_DIR}/CLaiMM/.venv/bin/python"
CMM_DATA_SRC="${ROOT_DIR}/../cmm-data/src"
CMM_DATA_SITE="${ROOT_DIR}/../cmm-data/.venv/lib/python3.14/site-packages"

if [[ ! -x "${RUNNER_PY}" ]]; then
  echo "Missing runner python: ${RUNNER_PY}" >&2
  exit 1
fi

# Route imports to local source trees so we can test without network installs.
export PYTHONPATH="${ROOT_DIR}/BGS_MCP/src:${ROOT_DIR}/OSTI_MCP/src:${ROOT_DIR}/CMM_API/src:${ROOT_DIR}/CLaiMM/src:${ROOT_DIR}/UNComtrade_MCP/src:${CMM_DATA_SRC}:${CMM_DATA_SITE}:${PYTHONPATH:-}"
export PYTHONPYCACHEPREFIX="/tmp/pycache"

echo "Using python: ${RUNNER_PY}"
"${RUNNER_PY}" -V

echo "Running compile checks..."
"${RUNNER_PY}" -m compileall -q \
  "${ROOT_DIR}/BGS_MCP/src/bgs_mcp" \
  "${ROOT_DIR}/OSTI_MCP/src/osti_mcp" \
  "${ROOT_DIR}/CMM_API/src/cmm_api" \
  "${ROOT_DIR}/CLaiMM/src/claimm_mcp"

echo "Running import checks..."
"${RUNNER_PY}" - <<'PY'
import importlib

modules = [
    "bgs_mcp.bgs_client",
    "osti_mcp.client",
    "cmm_api.clients",
    "claimm_mcp.edx_client",
    "cmm_data.clients",
]
for mod in modules:
    importlib.import_module(mod)
print("Import checks passed")
PY

echo "Running unit tests..."
"${RUNNER_PY}" -m pytest -q "${ROOT_DIR}/UNComtrade_MCP/tests/test_client.py"

echo "All checks passed."
