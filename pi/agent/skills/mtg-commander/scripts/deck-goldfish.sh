#!/usr/bin/env bash
# Goldfish (solitaire) simulator for Commander decks from Archidekt
# Plays N games of M turns each, tracking mana development, spell casting, and board state
#
# Usage: ./deck-goldfish.sh <deck_id_or_url> [options]
# Options:
#   --games N          Number of games to simulate (default: 10)
#   --turns N          Number of turns per game (default: 6)
#   --commander-min-x N  Minimum X value when casting X-cost commanders (default: 0)
#   --seed N           Random seed for reproducibility (default: random)
#   --quiet            Only show aggregate stats, skip per-game logs
#
# Examples:
#   ./deck-goldfish.sh 19369270
#   ./deck-goldfish.sh 19369270 --games 20 --turns 8
#   ./deck-goldfish.sh 19369270 --commander-min-x 3 --quiet

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <deck_id_or_url> [--games N] [--turns N] [--commander-min-x N] [--seed N] [--quiet]"
  exit 1
fi

INPUT="$1"
shift

# Parse options
GAMES=10
TURNS=6
CMD_MIN_X=0
SEED=""
QUIET=""
ASHNOD_VIGILANCE=""
EXTRA_ARGS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --games) GAMES="$2"; shift 2 ;;
    --turns) TURNS="$2"; shift 2 ;;
    --commander-min-x) CMD_MIN_X="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --quiet) QUIET="1"; shift ;;
    --ashnod-vigilance) ASHNOD_VIGILANCE="1"; shift ;;
    --exclude) EXTRA_ARGS="$EXTRA_ARGS --exclude \"$2\""; shift 2 ;;
    --include) EXTRA_ARGS="$EXTRA_ARGS --include \"$2\""; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Extract deck ID
DECK_ID=$(echo "$INPUT" | python3 -c "
import sys, re
inp = sys.stdin.read().strip()
m = re.search(r'(?:archidekt\.com/(?:api/)?decks?/)(\d+)', inp)
if m:
    print(m.group(1))
else:
    print(inp)
")

# Fetch deck JSON
RESPONSE=$(curl -s "https://archidekt.com/api/decks/${DECK_ID}/")

# Check for errors
ERROR_CHECK=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'detail' in data:
        print(f\"Error: {data['detail']}\")
    elif 'id' not in data:
        print('Error: Unexpected response format')
    else:
        print('ok')
except:
    print('Error: Failed to parse response')
" 2>/dev/null)

if [ "$ERROR_CHECK" != "ok" ]; then
  echo "$ERROR_CHECK"
  exit 1
fi

# Run the goldfish simulation (pipe via temp file to avoid eval+large JSON issues)
TMPFILE=$(mktemp /tmp/deck-goldfish-XXXXXX.json)
trap 'rm -f "$TMPFILE"' EXIT
echo "$RESPONSE" > "$TMPFILE"

# Build args array
PYARGS=(--games "$GAMES" --turns "$TURNS" --commander-min-x "$CMD_MIN_X")
[ -n "$SEED" ] && PYARGS+=(--seed "$SEED")
[ -n "$QUIET" ] && PYARGS+=(--quiet)
[ -n "$ASHNOD_VIGILANCE" ] && PYARGS+=(--ashnod-vigilance)
# Parse EXTRA_ARGS string back into array (handles quoted card names)
if [ -n "$EXTRA_ARGS" ]; then
  eval "EXTRA_ARRAY=($EXTRA_ARGS)"
  PYARGS+=("${EXTRA_ARRAY[@]}")
fi

python3 "${SCRIPT_DIR}/goldfish_sim.py" "${PYARGS[@]}" < "$TMPFILE"
