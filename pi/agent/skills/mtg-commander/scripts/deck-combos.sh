#!/usr/bin/env bash
# Find combos in a Commander deck using Commander Spellbook
# Queries each card in the deck and reports complete combos + near-misses
#
# Usage: ./deck-combos.sh <deck_id_or_url> [options]
# Options:
#   --max-missing N    Show combos missing up to N cards from deck (default: 2)
#   --verbose          Show step-by-step combo instructions
#
# Examples:
#   ./deck-combos.sh 22675268
#   ./deck-combos.sh https://archidekt.com/decks/22675268/cinder
#   ./deck-combos.sh 22675268 --max-missing 1
#   ./deck-combos.sh 22675268 --verbose

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <deck_id_or_url> [--max-missing N] [--verbose]"
  exit 1
fi

INPUT="$1"
shift

MAX_MISSING=2
VERBOSE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --max-missing) MAX_MISSING="$2"; shift 2 ;;
    --verbose)     VERBOSE="--verbose"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Extract deck ID from URL or use directly
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

# Validate response
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

TMPFILE=$(mktemp /tmp/deck-combos-XXXXXX.json)
trap 'rm -f "$TMPFILE"' EXIT
echo "$RESPONSE" > "$TMPFILE"

PYARGS=(--max-missing "$MAX_MISSING")
[ -n "$VERBOSE" ] && PYARGS+=("$VERBOSE")

python3 "${SCRIPT_DIR}/deck_combos.py" "${PYARGS[@]}" < "$TMPFILE"
