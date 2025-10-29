#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
mkdir -p "${REPO_ROOT}/docs/reference"
OUTPUT_FILE="${REPO_ROOT}/docs/reference/cli.md"
if command -v quartumse >/dev/null 2>&1; then
  quartumse --help > "${OUTPUT_FILE}"
else
  PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:$PYTHONPATH}" \
    python - <<'PY' > "${OUTPUT_FILE}"
from quartumse.cli import app
from typer.main import get_command
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(get_command(app), ["--help"], prog_name="quartumse")
if result.exception is not None:
    raise result.exception
print(result.output, end="")
PY
fi
