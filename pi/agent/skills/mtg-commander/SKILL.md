---
name: mtg-commander
description: "Magic: The Gathering Commander/EDH format assistant. Use when the user asks about MTG Commander rules, card lookups, deck building, card interactions, deck analysis, or anything related to the Commander format. Can look up cards via Scryfall, fetch decklists from Archidekt, and validate decks against Commander rules."
---

# MTG Commander Skill

This skill provides tools for working with Magic: The Gathering's Commander (EDH) format. It can look up card details, fetch and analyze decklists, validate decks against format rules, and answer rules questions.

## Quick Start

Before answering any Commander question, read the [Commander rules reference](references/commander-rules.md) to ground your answers in the official rules.

For Scryfall search syntax, see the [Scryfall syntax reference](references/scryfall-syntax.md).

## Card Lookup

When a user mentions a card by name, **always look it up** to get accurate details rather than relying on memory:

```bash
# Look up a single card by name (fuzzy match)
./scripts/card-lookup.sh "Sol Ring"
./scripts/card-lookup.sh "Thassa, Deep-Dwelling"
./scripts/card-lookup.sh "Kenrith, the Returned King"

# Get raw JSON for further analysis
./scripts/card-lookup.sh "Sol Ring" --json
```

The script uses Scryfall's fuzzy matching — partial or misspelled names work. It returns: name, mana cost, type, oracle text, color identity, Commander legality, and links.

**Important:** Whenever a card is mentioned in conversation — whether for rules questions, deck advice, or comparison — run the lookup script to confirm the card's actual oracle text, color identity, and legality. Do NOT rely on memory for card details.

## Batch Card Lookup

When you need to verify multiple cards at once (e.g. verifying a deck description, checking a list of suggestions):

```bash
# Look up multiple cards by name as arguments
./scripts/card-lookup-batch.sh "Sol Ring" "Arcane Signet" "Command Tower"

# Pipe card names via stdin (one per line)
echo -e "Sol Ring\nArcane Signet\nCommand Tower" | ./scripts/card-lookup-batch.sh --stdin
```

This calls `card-lookup.sh` for each card with proper Scryfall rate limiting (100ms between requests). Reports found/failed counts at the end. Use this instead of repeated individual lookups when verifying 3+ cards.

## Card Search

Find cards matching specific criteria using Scryfall search syntax:

```bash
# Search for cards (default: 10 results, sorted by EDHREC popularity)
./scripts/card-search.sh "t:legendary t:creature ci:bg cmc<=4"

# Limit results
./scripts/card-search.sh "o:\"draw a card\" ci<=u f:commander" 5

# Find possible commanders
./scripts/card-search.sh "is:commander ci=wubrg"

# Find cards with specific abilities
./scripts/card-search.sh "keyword:partner t:legendary"
```

## Archidekt Decklists

Fetch and analyze decklists from Archidekt:

```bash
# By deck ID
./scripts/deck-fetch.sh 12345

# By URL
./scripts/deck-fetch.sh "https://archidekt.com/decks/12345/my-deck-name"

# Summary view (default) — shows categories with card lists
./scripts/deck-fetch.sh 12345 --summary

# Full view — includes oracle text for every card
./scripts/deck-fetch.sh 12345 --full

# Deck description/primer text only
./scripts/deck-fetch.sh 12345 --description

# Raw JSON for custom analysis
./scripts/deck-fetch.sh 12345 --json
```

## Deck Goldfish (Solitaire Testing)

Simulate goldfish games to test mana development, ramp consistency, and commander timing:

```bash
# Basic: 10 games, 6 turns each
./scripts/deck-goldfish.sh 12345

# Custom game count and turn depth
./scripts/deck-goldfish.sh 12345 --games 20 --turns 8

# Set minimum X for X-cost commanders (e.g., Old Stickfingers)
./scripts/deck-goldfish.sh 12345 --commander-min-x 3

# Reproducible results with a seed
./scripts/deck-goldfish.sh 12345 --seed 42

# Only show aggregate stats
./scripts/deck-goldfish.sh 12345 --quiet
```

The simulator:
- Draws opening hands with mulligan logic (keeps 2-5 lands)
- Plays lands with color priority (missing colors first, then duals > basics > colorless)
- **Tries to cast the commander FIRST** each turn if it's castable at `--commander-min-x` (models the real-play decision of holding ramp when you could cast commander instead)
- After commander attempt, casts remaining spells by priority: ramp early, then draw, then creatures, then other
- Heuristically resolves spell effects using oracle text (land ramp, mana rocks, draw, sac-draw, kicker)
- Resolves draw-then-discard spells properly (Frantic Search, Compulsive Research, etc.)
- Detects and creates tokens from ETB/cast triggers and attack triggers
- Detects and tracks non-creature artifact tokens (Clue, Treasure, Blood, Food, Powerstone, Map)
- Cracks Clue tokens for draw and Blood tokens for loot with remaining mana after spell casting
- Detects and uses **activated abilities** on permanents (discard outlets, tap-to-create-token, tap-for-mana, tap-to-draw) with remaining mana after spell casting
- Resolves **upkeep triggers** (forced discard, draw, discard-hand-then-draw wheels, graveyard recursion)
- Tracks commander casting with optional minimum X value
- Reports per-game logs + aggregate stats (mana curve, missed land drops, ramp rate, commander timing, **token count**, **artifact token count**, **discard count**)

**Limitations:** This is a goldfish (no opponent). Spells that target opponents or interact with combat are cast but effects not modeled. Triggered abilities on permanents that fire from game events (e.g., "whenever you discard") are not generically modeled — only the card's own activated abilities and ETB/upkeep/attack triggers are resolved. Modal spells default to draw modes. Sac-draw spells require a creature/artifact on board. For decks with complex trigger chains (discard payoffs, death triggers, etc.), a custom goldfish script may still be needed.

### ⚠️ CRITICAL: Always Sanity-Check Goldfish Output Against Hand-Math

The goldfish uses heuristic priorities that may not match optimal play for a specific deck. **Never present goldfish numbers as ground truth without first validating they match reasonable play sequences.**

**Before drawing conclusions from goldfish statistics, do this check:**

1. **Work out by hand what the "minimum viable" cast turn should be.** E.g., for an X-cost commander like Old Stickfingers at X=3 (5 mana needed): natural curve gets 5 mana on T5, one ramp spell brings it to T4, one 1-CMC ritual or T2 rock brings it to T3.

2. **Estimate a rough floor probability** using hypergeometric math. If the deck has ~50 mana sources in 99 cards, the chance of having enough ramp + lands for a T4–T5 cast should be well above 50%.

3. **If the goldfish number is dramatically lower than your hand-math estimate, the sim is wrong, not you.** Do not rationalize surprising numbers. Investigate.

4. **Common sim pitfalls for X-cost and high-value commanders:**
   - The sim casts ramp spells BEFORE trying to cast the commander each turn. If you have 5 mana + Cultivate + Stickfingers playable, the sim casts Cultivate (3 mana), then tries Stickfingers with 2 mana left → fails. Real play would hold the ramp.
   - The sim's `cast_priority` is: ramp → draw → creatures → other. Commanders are cast in a separate block AFTER hand spells.
   - For decks where the commander IS the win condition (X-cost grave-fillers, combo enablers), this mis-orders play.

5. **When in doubt, run a verbose per-game log (not `--quiet`) and trace 3–5 games manually** to see if the sim is sequencing like a real player would.

6. **If the user's intuition conflicts with sim output, trust the user first and investigate the sim.** Users who built their deck often have a better mental model than the heuristic simulator.

**Lesson from a real session:** A user's 36-land / 13-ramp Old Stickfingers deck showed T5 cast rate of 15.8% and T6 of 32% in the sim. The user pushed back — their own hand-math showed T5 should be achievable 60%+ of the time. Investigation revealed the sim was casting 3-mana ramp spells first and depleting mana before attempting Stickfingers. After patching the sim to try the commander FIRST when castable at min_x, the real rates were T5 = 85%, T6 = 90%. The user was right; the sim was wrong. An earlier deck-building recommendation based on the bad numbers had to be retracted.

**When recommending deck changes based on goldfish data, explicitly note:** "These numbers assume the sim plays correctly. If the numbers look surprisingly bad, we should verify before making changes."

## Deck Validation

Validate an Archidekt deck against Commander format rules:

```bash
./scripts/deck-validate.sh 12345
./scripts/deck-validate.sh "https://archidekt.com/decks/12345/my-deck"
```

This checks:
- ✅ Deck is exactly 100 cards
- ✅ Commander is a valid legendary creature (or has "can be your commander")
- ✅ Partner/Partner-with validity for dual commanders
- ✅ All cards' color identity is within the commander's color identity
- ✅ No banned cards
- ✅ Singleton rule (no duplicates except basic lands and exempt cards)

## Answering Rules Questions

When answering rules questions:

1. **Always consult** the [Commander rules reference](references/commander-rules.md) first
2. **Look up any cards mentioned** using `card-lookup.sh` to get their exact oracle text
3. Cite the specific rule from the reference
4. If a question involves card interactions, look up ALL cards involved
5. If unsure about a card's current legality, check with the lookup script (Scryfall data is authoritative)

## Common Tasks

### "Is [card] legal in Commander?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check the "Commander:" line in the output
```

### "What's the color identity of [card]?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check the "Color Identity:" line
```

### "Can [card] be my commander?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check: Is it legendary creature? Or does oracle text say "can be your commander"?
```

### "Suggest cards for my [theme] deck in [colors]"
```bash
./scripts/card-search.sh "o:\"relevant ability\" ci<=COLORS f:commander" 15
```

### "Analyze my Archidekt deck"
```bash
./scripts/deck-fetch.sh DECK_ID --summary
./scripts/deck-validate.sh DECK_ID
# Then look up specific cards of interest with card-lookup.sh
```

### "Goldfish my deck" / "Test my mana base"
```bash
# Basic goldfish test
./scripts/deck-goldfish.sh DECK_ID

# For X-cost commanders, set minimum X
./scripts/deck-goldfish.sh DECK_ID --commander-min-x 3

# More games for better statistics
./scripts/deck-goldfish.sh DECK_ID --games 20 --turns 8 --quiet
```

### "Verify/review my deck description"

Deck descriptions and primers frequently contain errors — wrong power/toughness, incorrect oracle text paraphrasing, or references to cards that aren't actually in the deck. Follow this workflow:

1. Fetch the decklist and description:
```bash
./scripts/deck-fetch.sh DECK_ID --full
./scripts/deck-fetch.sh DECK_ID --description
```

2. Extract every card name mentioned in the description text. Cross-reference each one against the actual decklist. Flag any card names that appear in the description but NOT in the deck — these are phantom references (cards that were cut or never added).

3. Look up every card mentioned in the description to verify claims:
```bash
./scripts/card-lookup-batch.sh "Card One" "Card Two" "Card Three"
```

4. Check for these common errors:
   - **Wrong stats**: power/toughness, mana cost, CMC quoted incorrectly
   - **Phantom cards**: cards described that aren't in the decklist
   - **Misquoted abilities**: oracle text paraphrased incorrectly (e.g., saying a card "creates a token" when it doesn't, or wrong trigger conditions)
   - **Wrong counts**: "the deck runs five X" when the actual count differs
   - **Assumed synergies that don't work**: abilities that don't interact the way the description claims (always verify against actual oracle text)
   - **Legality issues**: cards that aren't legal in Commander (Un-sets, banned cards) without noting Rule Zero

## API Rate Limits

- **Scryfall**: Requests should be spaced by 50-100ms. The scripts make single requests so this is generally fine. Do not bulk-query in tight loops.
- **Archidekt**: No official rate limit documentation, but be reasonable with requests.

## Price Checking

When suggesting cards, **always verify prices** before presenting them. Do NOT guess prices from memory.

Use Scryfall's API to get EUR prices (sourced from Cardmarket):
```bash
curl -s "https://api.scryfall.com/cards/named?fuzzy=CARD_NAME" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('prices',{}); print(f\"EUR: {p.get('eur','N/A')}  EUR foil: {p.get('eur_foil','N/A')}\")"
```

For batch price checks:
```bash
for card in "Card One" "Card Two" "Card Three"; do
  echo "=== $card ==="
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote(\"$card\"))")
  curl -s "https://api.scryfall.com/cards/named?fuzzy=$encoded" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('prices',{}); print(f\"  EUR: {p.get('eur','N/A')}  EUR foil: {p.get('eur_foil','N/A')}\")"
  sleep 0.2
done
```

**Note:** Cards with apostrophes in their name (e.g. "Bolas's Citadel") will break the python quoting. Use the fuzzy search without the apostrophe (e.g. "Bolas Citadel") or handle quoting carefully.

When the user has a budget constraint, check prices BEFORE suggesting cards, not after. Present price alongside every suggestion.

## Mana Restriction Awareness

When building around specific mana sources, **always check what that mana can and cannot pay for**. Common restrictions:

- **Powerstone tokens**: "{T}: Add {C}. This mana can't be spent to cast a nonartifact spell." — CAN pay for: artifact spells, activated abilities (on any permanent), equip costs, special costs. CANNOT pay for: creature spells (unless artifact creature), instants, sorceries, enchantments, planeswalkers.
- **Treasure tokens**: No restrictions (any color, any purpose).
- **Eldrazi Spawn/Scion**: Sacrifice for {C}, no spending restrictions but colorless only.
- **Gold tokens**: Any one color, no other restrictions.

When suggesting payoffs for decks built around restricted mana sources, verify every suggestion is actually payable. Do not suggest instants/sorceries as payoffs for Powerstone mana, etc.

## Deck Building Session Workflow

When helping a user build a deck iteratively:

1. Fetch the decklist and understand the commander + gameplan first
2. Ask clarifying questions about win condition, budget, power level, and theme preferences before suggesting cards
3. Present suggestions **one at a time** unless asked otherwise — let the user decide before moving on
4. For each suggestion, include: card name, Scryfall link, EUR price, and a clear explanation of why it fits THIS specific deck
5. Track budget spent vs remaining when the user has a budget constraint
6. When a session is interrupted, offer to write a context file summarizing progress, pending suggestions, and remaining needs

## Tips

- Scryfall fuzzy search is forgiving — "thassa deep" will find "Thassa, Deep-Dwelling"
- For double-faced cards (MDFCs, transform), both faces are displayed
- The Archidekt deck format number 3 = Commander/EDH
- When helping with deck building, consider: mana curve, ramp, card draw, removal, win conditions, and mana base
- A typical Commander deck wants: ~36-38 lands, 10+ ramp, 10+ card draw, 5-10 removal, and the rest toward the deck's strategy
