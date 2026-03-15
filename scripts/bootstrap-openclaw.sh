#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE_DIR="${1:-$HOME/.openclaw/workspace}"

PYTHONPATH="$REPO_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace "$WORKSPACE_DIR" \
  --repo "$REPO_DIR"

echo ""
echo "Next steps:"
echo "  cd $WORKSPACE_DIR"
echo "  python3 memory-system/index/build_pageindex.py"
echo "  python3 memory-system/index/search_pageindex.py 'primary model'"
