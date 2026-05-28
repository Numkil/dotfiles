#!/usr/bin/env bash
# Tailored goldfish simulator for the Cinder & Brine / Rielle deck
# Archidekt: https://archidekt.com/decks/21998868/cinder_brine
#
# Usage:
#   ./deck-goldfish-cinder-brine.sh [deck_id_or_url]
#   ./deck-goldfish-cinder-brine.sh 21998868 --games 50 --turns 8 --quiet
#   ./deck-goldfish-cinder-brine.sh 21998868 --seed 42
#
# Defaults to deck 21998868 if no ID given.
#
# Options (passed through to cinder_brine_goldfish.py):
#   --games N     Number of games (default: 20)
#   --turns N     Turns per game (default: 8)
#   --seed N      Random seed for reproducibility
#   --quiet       Only show aggregate stats

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default deck ID
DEFAULT_DECK_ID="21998868"

# Parse first argument as deck ID or URL (optional)
if [ $# -ge 1 ] && [[ "$1" != --* ]]; then
  INPUT="$1"
  shift
else
  INPUT="$DEFAULT_DECK_ID"
fi

# Extract numeric deck ID from URL or use directly
DECK_ID=$(echo "$INPUT" | python3 -c "
import sys, re
inp = sys.stdin.read().strip()
m = re.search(r'(?:archidekt\.com/(?:api/)?decks?/)(\d+)', inp)
print(m.group(1) if m else inp)
")

echo "Fetching deck $DECK_ID from Archidekt..." >&2

RESPONSE=$(curl -s "https://archidekt.com/api/decks/${DECK_ID}/")

# Sanity check
STATUS=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print('error: ' + d['detail'] if 'detail' in d else ('ok' if 'id' in d else 'error: unexpected format'))
except Exception as e:
    print('error: ' + str(e))
" 2>/dev/null)

if [[ "$STATUS" != ok ]]; then
  echo "Failed to fetch deck: $STATUS" >&2
  exit 1
fi

echo "$RESPONSE" | python3 "${SCRIPT_DIR}/cinder_brine_goldfish.py" "$@"
