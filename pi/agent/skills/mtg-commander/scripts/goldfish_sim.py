#!/usr/bin/env python3
"""
Generic Commander deck goldfish (solitaire) simulator.

Reads Archidekt deck JSON from stdin and simulates N games of M turns each.
Uses card types, oracle text, mana production, and Archidekt categories
to heuristically resolve spells without hardcoding card names.
"""

import json
import sys
import re
import argparse
import random
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# Card data model
# =============================================================================

@dataclass
class Card:
    name: str
    cmc: int
    types: list
    supertypes: list
    subtypes: list
    text: str
    mana_cost: str
    mana_production: dict
    keywords: list
    categories: list
    power: Optional[str] = None
    toughness: Optional[str] = None
    is_commander: bool = False

    # Derived properties (set after init)
    is_land: bool = False
    is_creature: bool = False
    is_artifact: bool = False
    is_enchantment: bool = False
    is_sorcery: bool = False
    is_instant: bool = False
    is_planeswalker: bool = False
    is_basic: bool = False
    is_ramp: bool = False
    is_mana_rock: bool = False
    is_mana_dork: bool = False
    is_land_ramp: bool = False
    is_draw: bool = False
    is_sac_draw: bool = False
    draw_count: int = 0
    lands_to_field: int = 0
    lands_to_hand: int = 0
    extra_mana: int = 0
    needs_sac_creature: bool = False
    needs_sac_land: bool = False
    needs_sac_artifact: bool = False
    needs_creature_target: bool = False
    has_x_cost: bool = False
    color_costs: dict = field(default_factory=dict)
    produces_colors: set = field(default_factory=set)

    def __post_init__(self):
        self.is_land = 'Land' in self.types
        self.is_creature = 'Creature' in self.types
        self.is_artifact = 'Artifact' in self.types
        self.is_enchantment = 'Enchantment' in self.types
        self.is_sorcery = 'Sorcery' in self.types
        self.is_instant = 'Instant' in self.types
        self.is_planeswalker = 'Planeswalker' in self.types
        self.is_basic = 'Basic' in self.supertypes
        self.has_x_cost = '{X}' in self.mana_cost

        # Parse color requirements from mana cost
        self.color_costs = {}
        for color in 'WUBRG':
            count = self.mana_cost.count('{' + color + '}')
            if count:
                self.color_costs[color] = count

        # Parse mana production
        self.produces_colors = set()
        if self.mana_production:
            for color, amount in self.mana_production.items():
                if amount is not None and amount > 0:
                    self.produces_colors.add(color)

        # Classify using oracle text heuristics + categories
        self._classify()

    def _classify(self):
        text_lower = self.text.lower()
        cats_lower = [c.lower() for c in self.categories]

        # Ramp detection
        is_ramp_category = 'ramp' in cats_lower

        # Mana rock: artifact that produces mana
        if self.is_artifact and self.produces_colors:
            self.is_mana_rock = True
            self.is_ramp = True
            self.extra_mana = max(
                (v for v in self.mana_production.values() if v is not None), default=1
            )

        # Mana dork: creature that produces mana
        if self.is_creature and self.produces_colors:
            self.is_mana_dork = True
            self.is_ramp = True
            self.extra_mana = max(
                (v for v in self.mana_production.values() if v is not None), default=1
            )

        # Enchantment ramp (e.g., Utopia Sprawl, Wild Growth)
        if self.is_enchantment and self.produces_colors:
            self.is_ramp = True
            self.extra_mana = max(
                (v for v in self.mana_production.values() if v is not None), default=1
            )

        # Equipment/artifact that produces mana (e.g., Thieves' Tools - categorized as ramp)
        if is_ramp_category and not self.is_land and self.extra_mana == 0:
            # Check oracle text for mana ability
            if re.search(r'\{t\}:\s*add\s+\{', text_lower) or self.produces_colors:
                self.is_ramp = True
                self.extra_mana = max(
                    (v for v in self.mana_production.values() if v is not None), default=1
                )

        # Land ramp: search library for land/forest/etc, put onto battlefield
        if re.search(r'search your library for .{0,40}(basic )?(land|forest|plains|island|swamp|mountain) cards?.{0,40}put .{0,30}onto the battlefield', text_lower):
            self.is_land_ramp = True
            self.is_ramp = True

            # Count lands to field
            if re.search(r'up to two basic land cards.{0,60}(put one onto the battlefield|one onto the battlefield).{0,40}(other|the other) into your hand', text_lower):
                # Cultivate / Kodama's Reach pattern
                self.lands_to_field = 1
                self.lands_to_hand = 1
            elif re.search(r'up to two basic land cards.{0,30}put them onto the battlefield', text_lower):
                self.lands_to_field = 2
            elif re.search(r'search your library for .{0,50}(basic land|forest|plains|island|swamp|mountain) card.{0,10}put .{0,15}onto the battlefield', text_lower):
                self.lands_to_field = 1

            # Kicker / modal for extra land (e.g., Primal Growth)
            if 'kicker' in text_lower and re.search(r'kicked.{0,50}two basic land cards', text_lower):
                # Base is 1, kicked is 2 - we'll handle this in the sim
                self.lands_to_field = 1  # base case

        # Category-based ramp fallback
        if is_ramp_category and not self.is_ramp:
            self.is_ramp = True
            # Try to determine effect from text
            if self.is_land_ramp or self.lands_to_field > 0:
                pass  # already handled
            elif self.extra_mana == 0:
                self.extra_mana = 1  # conservative default

        # Additional cost detection
        if re.search(r'(additional cost|as an additional cost|kicker).{0,30}sacrifice a creature', text_lower):
            self.needs_sac_creature = True
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice a land', text_lower):
            self.needs_sac_land = True
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice an? artifact', text_lower):
            self.needs_sac_artifact = True
        # "sacrifice an artifact or creature" (e.g., Deadly Dispute)
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice an? (artifact or creature|creature or artifact)', text_lower):
            self.needs_sac_creature = True
            self.needs_sac_artifact = True

        # Draw detection
        # For permanents, only count draw that happens on cast/ETB, not activated abilities
        # Activated abilities have the pattern "{cost}: ...draw"
        draw_text = text_lower
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment or self.is_planeswalker

        if is_permanent:
            # Split on newlines (each paragraph is a separate ability)
            # Only look for draw in ETB/cast triggers or the spell portion, not activated abilities
            lines = text_lower.split('\n')
            etb_draw_lines = []
            for line in lines:
                # Skip activated abilities (contain ":" with a cost before it)
                if re.match(r'^\{.*\}.*:', line):
                    continue
                if re.match(r'^[^:]+,\s*\{.*\}.*:', line):
                    continue
                # Keep ETB triggers and static text
                if 'enters' in line or 'when you cast' in line or 'draw' in line:
                    etb_draw_lines.append(line)
            draw_text = ' '.join(etb_draw_lines) if etb_draw_lines else ''

        draw_match = re.search(r'(?:you )?draws? (?:(\w+|(\d+)) )?cards?', draw_text)
        if draw_match:
            word_to_num = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'a': 1}
            if draw_match.group(1):
                val = draw_match.group(1).lower()
                self.draw_count = word_to_num.get(val, int(val) if val.isdigit() else 1)
            else:
                self.draw_count = 1

            self.is_draw = True

            # Sacrifice-draw (e.g., Village Rites, Deadly Dispute)
            if self.needs_sac_creature or self.needs_sac_artifact:
                self.is_sac_draw = True

        # Draw from categories - only for instants/sorceries, not permanents with activated draw
        if 'draw' in cats_lower and not self.is_draw:
            if not is_permanent:
                self.is_draw = True
                self.draw_count = max(self.draw_count, 1)

        # Modal spells with repeated draw modes (e.g., Wretched Confluence "choose three")
        if re.search(r'choose three', text_lower) and self.draw_count == 1:
            self.draw_count = 3  # assume all modes used for draw in goldfish

        # Harrow special case: sac land, get 2 lands
        if self.needs_sac_land and self.is_land_ramp:
            if re.search(r'up to two basic land cards.{0,30}put them onto the battlefield', text_lower):
                self.lands_to_field = 2

        # Spells that need a creature target on the battlefield (not sac)
        # e.g., "target creature gets +1/-1" or "when it dies... draw"
        # But NOT modal spells where creature targeting is optional
        if (self.is_instant or self.is_sorcery) and not self.needs_sac_creature:
            if re.search(r'target creature (gets|you control)', text_lower):
                # Skip modal spells ("choose") where targeting creature is just one mode
                if not re.search(r'choose (one|two|three|four|five)', text_lower):
                    self.needs_creature_target = True

    def produces_color(self, color):
        """Check if this permanent can produce a specific color."""
        if color in self.produces_colors:
            return True
        # 'C' in produces means colorless, any-color lands would show all colors
        return False

    def __repr__(self):
        return self.name


# =============================================================================
# Deck parsing
# =============================================================================

def parse_deck(data):
    """Parse Archidekt JSON into a deck (list of Cards) + commander info."""
    cards_in_deck = []
    commanders = []
    deck_name = data.get('name', 'Unknown')

    # Determine which categories are "in deck"
    included_cats = set()
    for cat_info in data.get('categories', []):
        if cat_info.get('includedInDeck', True):
            included_cats.add(cat_info['name'])

    for entry in data.get('cards', []):
        categories = entry.get('categories', ['Uncategorized'])
        cats_lower = [c.lower() for c in categories]

        # Skip maybeboard
        if 'maybeboard' in cats_lower:
            continue

        ocard = entry.get('card', {}).get('oracleCard', {})
        quantity = entry.get('quantity', 1)
        is_commander = 'commander' in cats_lower

        card = Card(
            name=ocard.get('name', 'Unknown'),
            cmc=int(ocard.get('cmc', 0)),
            types=ocard.get('types', []),
            supertypes=ocard.get('superTypes', []),
            subtypes=ocard.get('subTypes', []),
            text=ocard.get('text', ''),
            mana_cost=ocard.get('manaCost', ''),
            mana_production=ocard.get('manaProduction', {}),
            keywords=ocard.get('keywords', []),
            categories=categories,
            power=ocard.get('power'),
            toughness=ocard.get('toughness'),
            is_commander=is_commander,
        )

        if is_commander:
            commanders.append(card)
        else:
            for _ in range(quantity):
                cards_in_deck.append(card)

    return deck_name, cards_in_deck, commanders


# =============================================================================
# Game state
# =============================================================================

@dataclass
class GameState:
    library: list = field(default_factory=list)
    hand: list = field(default_factory=list)
    battlefield_lands: list = field(default_factory=list)
    battlefield_creatures: list = field(default_factory=list)
    battlefield_other: list = field(default_factory=list)  # artifacts, enchantments, etc.
    graveyard: list = field(default_factory=list)
    commander_zone: list = field(default_factory=list)
    ramp_mana: int = 0  # extra mana from rocks/dorks/enchantments

    @property
    def total_mana(self):
        return len(self.battlefield_lands) + self.ramp_mana

    @property
    def all_permanents(self):
        return self.battlefield_lands + self.battlefield_creatures + self.battlefield_other

    def color_available(self, color):
        """Check if we can produce a given color."""
        for card in self.all_permanents:
            if card.produces_color(color):
                return True
        return False

    def can_cast(self, card, mana_available):
        """Check if we have enough mana and colors to cast a card."""
        if card.cmc > mana_available:
            return False
        for color, count in card.color_costs.items():
            if not self.color_available(color):
                return False
        return True


# =============================================================================
# Simulation
# =============================================================================

def land_priority(card, game_state):
    """Score a land for play priority. Higher = play first."""
    score = 0
    # Prefer color-producing lands
    color_count = sum(1 for c in 'WUBRG' if card.produces_color(c))
    score += color_count * 5
    # Prefer lands that produce colors we don't yet have
    for c in 'WUBRG':
        if card.produces_color(c) and not game_state.color_available(c):
            score += 20
    # Slight penalty for colorless-only lands
    if color_count == 0:
        score -= 3
    return score


def cast_priority(card, turn):
    """Score a spell for casting priority. Lower = cast first."""
    cats_lower = [c.lower() for c in card.categories]

    # Ramp is highest priority in early turns
    if card.is_ramp and turn <= 4:
        return (0, card.cmc)
    # Draw
    if card.is_draw:
        return (1, card.cmc)
    # Creatures (board development)
    if card.is_creature:
        return (2, card.cmc)
    # Everything else by CMC
    return (3, card.cmc)


def simulate_game(deck_cards, commanders, rng, num_turns, commander_min_x):
    """Simulate one goldfish game. Returns game log dict."""

    library = deck_cards.copy()
    rng.shuffle(library)

    hand = library[:7]
    library = library[7:]

    # Mulligan: keep if 2-5 lands
    mulligan_count = 0
    while mulligan_count < 2:
        hand_lands = sum(1 for c in hand if c.is_land)
        if 2 <= hand_lands <= 5:
            break
        mulligan_count += 1
        library = deck_cards.copy()
        rng.shuffle(library)
        hand = library[:7 - mulligan_count]
        library = library[7 - mulligan_count:]

    state = GameState(
        library=library,
        hand=list(hand),
        commander_zone=list(commanders),
    )

    game_log = {
        'mulligans': mulligan_count,
        'opening_hand': [c.name for c in hand],
        'opening_lands': sum(1 for c in hand if c.is_land),
        'turns': [],
        'commander_cast_turn': None,
    }

    for turn in range(1, num_turns + 1):
        turn_log = {
            'turn': turn,
            'drawn': None,
            'land_played': None,
            'spells': [],
            'mana_after': 0,
            'hand_size': 0,
            'lands_on_field': 0,
        }

        # Draw (skip turn 1 — on the play)
        if turn > 1 and state.library:
            drawn = state.library.pop(0)
            state.hand.append(drawn)
            turn_log['drawn'] = drawn.name

        # === LAND DROP ===
        hand_lands = [c for c in state.hand if c.is_land]
        if hand_lands:
            hand_lands.sort(key=lambda l: -land_priority(l, state))
            chosen = hand_lands[0]
            state.hand.remove(chosen)
            state.battlefield_lands.append(chosen)
            turn_log['land_played'] = chosen.name

        mana_left = state.total_mana

        # === CAST SPELLS FROM HAND ===
        max_iterations = 20  # safety against infinite loops
        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            castable = [
                c for c in state.hand
                if not c.is_land
                and c.cmc <= mana_left
                and state.can_cast(c, mana_left)
            ]

            # Filter out sac-draw if nothing to sacrifice
            castable = [
                c for c in castable
                if not c.is_sac_draw or len(state.battlefield_creatures) > 0
                or (c.needs_sac_artifact and len(state.battlefield_other) > 0)
            ]

            # Filter out sac-land costs if no lands to spare
            castable = [
                c for c in castable
                if not c.needs_sac_land or len(state.battlefield_lands) > 1
            ]

            # Filter out spells needing creature targets if none on board
            castable = [
                c for c in castable
                if not c.needs_creature_target or len(state.battlefield_creatures) > 0
            ]

            if not castable:
                break

            castable.sort(key=lambda c: cast_priority(c, turn))
            card = castable[0]

            state.hand.remove(card)
            mana_left -= card.cmc
            note = card.name

            # === Resolve spell effects ===

            # Sac costs
            sacced_creature = None
            if card.needs_sac_creature and not card.is_sac_draw:
                if state.battlefield_creatures:
                    sacced_creature = state.battlefield_creatures.pop(0)
                    state.graveyard.append(sacced_creature)

            sacced_land = None
            if card.needs_sac_land:
                if state.battlefield_lands:
                    sacced_land = state.battlefield_lands.pop()
                    state.graveyard.append(sacced_land)

            # Sac-draw spells
            if card.is_sac_draw:
                sacced = None
                if state.battlefield_creatures:
                    sacced = state.battlefield_creatures.pop(0)
                elif card.needs_sac_artifact and state.battlefield_other:
                    sacced = state.battlefield_other.pop(0)
                if sacced:
                    state.graveyard.append(sacced)
                    drawn_cards = []
                    for _ in range(card.draw_count):
                        if state.library:
                            d = state.library.pop(0)
                            state.hand.append(d)
                            drawn_cards.append(d.name)
                    note = f"{card.name} (sac {sacced.name}) -> draw {len(drawn_cards)}"
                    # Deadly Dispute creates a treasure
                    if 'treasure' in card.text.lower() or 'create a treasure' in card.text.lower():
                        mana_left += 1  # immediate treasure
                        state.ramp_mana += 1
                        note += " + Treasure"

            # Land ramp
            elif card.is_land_ramp:
                actual_to_field = card.lands_to_field
                actual_to_hand = card.lands_to_hand

                # Check for kicker with sac creature
                if 'kicker' in card.text.lower() and 'sacrifice a creature' in card.text.lower():
                    if sacced_creature or (state.battlefield_creatures and not card.needs_sac_creature):
                        # Kicked!
                        if not sacced_creature and state.battlefield_creatures:
                            sacced_creature = state.battlefield_creatures.pop(0)
                            state.graveyard.append(sacced_creature)
                        if re.search(r'kicked.{0,30}two basic land cards', card.text.lower()):
                            actual_to_field = 2
                            note = f"{card.name} (KICKED, sac {sacced_creature.name}) -> {actual_to_field} lands to field"
                        else:
                            note = f"{card.name} (kicked) -> lands to field"
                    else:
                        note = f"{card.name} -> {actual_to_field} land to field"
                elif sacced_land:
                    note = f"{card.name} (sac {sacced_land.name}) -> {actual_to_field} lands to field"
                else:
                    parts = []
                    if actual_to_field:
                        parts.append(f"{actual_to_field} to field")
                    if actual_to_hand:
                        parts.append(f"{actual_to_hand} to hand")
                    note = f"{card.name} -> {', '.join(parts)}"

                # Add generic lands to battlefield
                for _ in range(actual_to_field):
                    # Create a basic land token (Forest as default)
                    fetched = Card(
                        name="(fetched land)",
                        cmc=0, types=['Land'], supertypes=['Basic'], subtypes=[],
                        text="", mana_cost="", mana_production={'W': None, 'U': None, 'B': 1, 'R': None, 'G': 1, 'C': None},
                        keywords=[], categories=['Land'],
                    )
                    state.battlefield_lands.append(fetched)

                for _ in range(actual_to_hand):
                    fetched = Card(
                        name="(fetched land)",
                        cmc=0, types=['Land'], supertypes=['Basic'], subtypes=[],
                        text="", mana_cost="", mana_production={'W': None, 'U': None, 'B': 1, 'R': None, 'G': 1, 'C': None},
                        keywords=[], categories=['Land'],
                    )
                    state.hand.append(fetched)

            # Mana rocks / dorks / enchantment ramp
            elif card.is_mana_rock or card.is_mana_dork or (card.is_ramp and card.extra_mana > 0 and not card.is_land_ramp):
                state.ramp_mana += card.extra_mana
                if card.is_creature:
                    state.battlefield_creatures.append(card)
                else:
                    state.battlefield_other.append(card)
                note = f"{card.name} (+{card.extra_mana} mana)"

            # Non-sac draw spells
            elif card.is_draw and not card.is_sac_draw:
                drawn_cards = []
                for _ in range(card.draw_count):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn_cards.append(d.name)
                note = f"{card.name} -> draw {len(drawn_cards)}"

            # Creatures (just enter battlefield)
            elif card.is_creature:
                state.battlefield_creatures.append(card)

            # Other permanents
            elif card.is_artifact or card.is_enchantment or card.is_planeswalker:
                state.battlefield_other.append(card)

            # Instants/sorceries with no modeled effect -> just cast
            # (removal, protection, recursion, etc.)

            turn_log['spells'].append(note)
            # Only instants/sorceries go to graveyard; permanents stay on field
            if card.is_instant or card.is_sorcery:
                state.graveyard.append(card)

            # Recalculate mana available (ramp may have changed it)
            mana_left = state.total_mana - (state.total_mana - mana_left) if mana_left >= 0 else 0
            # Simpler: just track spending
            # mana_left stays as decremented

        # === TRY CASTING COMMANDER ===
        for cmdr in list(state.commander_zone):
            min_mana_needed = max(cmdr.color_costs.values(), default=0)
            base_cost = sum(cmdr.color_costs.values())
            # For X spells: need base colored cost + minimum X
            if cmdr.has_x_cost:
                min_needed = base_cost + commander_min_x
                if mana_left >= min_needed and state.can_cast(cmdr, mana_left):
                    x_val = mana_left - base_cost
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    game_log['commander_cast_turn'] = turn

                    # Model X-cost ETB/cast triggers (milling, etc.)
                    revealed_cards = []
                    creatures_milled = []
                    non_creatures_to_bottom = []
                    if 'reveal cards from the top of your library' in cmdr.text.lower() and 'creature' in cmdr.text.lower():
                        # Stickfingers-style: reveal until X creatures found
                        # Creatures go to graveyard, rest go to bottom of library
                        creatures_found = 0
                        while creatures_found < x_val and state.library:
                            revealed = state.library.pop(0)
                            revealed_cards.append(revealed.name)
                            if revealed.is_creature:
                                creatures_found += 1
                                creatures_milled.append(revealed.name)
                                state.graveyard.append(revealed)
                            else:
                                non_creatures_to_bottom.append(revealed)
                        # Put non-creature cards on bottom of library in random order
                        rng.shuffle(non_creatures_to_bottom)
                        state.library.extend(non_creatures_to_bottom)

                    note = f"{cmdr.name} (X={x_val})"
                    if revealed_cards:
                        note += f" -> revealed {len(revealed_cards)} cards, {', '.join(creatures_milled)} to graveyard"
                    turn_log['spells'].append(note)
                    mana_left = 0
            else:
                if mana_left >= cmdr.cmc and state.can_cast(cmdr, mana_left):
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    game_log['commander_cast_turn'] = turn
                    turn_log['spells'].append(cmdr.name)
                    mana_left -= cmdr.cmc

        turn_log['mana_after'] = state.total_mana
        turn_log['hand_size'] = len(state.hand)
        turn_log['lands_on_field'] = len(state.battlefield_lands)
        game_log['turns'].append(turn_log)

    game_log['final_mana'] = state.total_mana
    game_log['final_lands'] = len(state.battlefield_lands)
    game_log['final_hand'] = len(state.hand)
    game_log['board_creatures'] = [c.name for c in state.battlefield_creatures]
    game_log['board_other'] = [c.name for c in state.battlefield_other]
    game_log['graveyard'] = [c.name for c in state.graveyard]

    return game_log


# =============================================================================
# Output
# =============================================================================

def print_game(game, game_num, is_land_fn):
    """Print a single game log."""
    mul = f"  (mulligan to {7 - game['mulligans']})" if game['mulligans'] else ""
    print(f"\n{'=' * 65}")
    print(f"GAME {game_num}{mul}")
    print(f"Hand: {', '.join(game['opening_hand'])}")
    print(f"  ({game['opening_lands']} lands, {len(game['opening_hand']) - game['opening_lands']} spells)")

    for t in game['turns']:
        draw_str = f"Draw: {t['drawn']}" if t['drawn'] else "(no draw)"
        print(f"\n  Turn {t['turn']}: {draw_str}")
        if t['land_played']:
            print(f"    Play land: {t['land_played']}")
        else:
            print(f"    *** MISSED LAND DROP ***")
        if t['spells']:
            for s in t['spells']:
                print(f"    Cast: {s}")
        else:
            print(f"    (no spells cast)")
        ramp_extra = t['mana_after'] - t['lands_on_field']
        ramp_str = f" + {ramp_extra} ramp" if ramp_extra else ""
        print(f"    -> {t['mana_after']} mana ({t['lands_on_field']} lands{ramp_str}), {t['hand_size']} in hand")

    print(f"\n  === End state ===")
    ramp = game['final_mana'] - game['final_lands']
    print(f"  Mana: {game['final_mana']} ({game['final_lands']} lands + {ramp} ramp)")
    print(f"  Hand: {game['final_hand']} cards")
    board = game['board_creatures'] + game['board_other']
    print(f"  Board: {', '.join(board) if board else '(empty)'}")
    if game['commander_cast_turn']:
        print(f"  Commander cast: Turn {game['commander_cast_turn']}")
    else:
        print(f"  Commander: NOT CAST")


def print_aggregate(games, num_turns, commanders):
    """Print aggregate statistics."""
    n = len(games)
    print(f"\n{'=' * 65}")
    print(f"AGGREGATE ANALYSIS ({n} games, {num_turns} turns each)")
    if commanders:
        print(f"Commander: {', '.join(c.name for c in commanders)}")
    print(f"{'=' * 65}")

    # Mulligans
    mull_count = sum(1 for g in games if g['mulligans'] > 0)
    print(f"\nMulligans: {mull_count}/{n} games")

    # Missed land drops
    print(f"\nMissed land drops:")
    any_missed = False
    for turn in range(1, num_turns + 1):
        missed = sum(1 for g in games if not g['turns'][turn - 1]['land_played'])
        if missed:
            print(f"  Turn {turn}: {missed}/{n} games")
            any_missed = True
    if not any_missed:
        print(f"  None!")

    # Mana progression
    print(f"\nMana available (end of turn):")
    for turn in range(1, num_turns + 1):
        manas = [g['turns'][turn - 1]['mana_after'] for g in games]
        avg = sum(manas) / len(manas)
        print(f"  Turn {turn}: avg {avg:.1f}  (min {min(manas)}, max {max(manas)})")

    # Ramp by turn 3
    ramp_t3_games = 0
    ramp_t3_total = 0
    print(f"\nRamp cast by turn 3:")
    for i, g in enumerate(games):
        ramps = []
        for t in g['turns'][:3]:
            for s in t['spells']:
                # Simple heuristic: if the spell note contains mana/land keywords
                spell_name = s.split(' (')[0].split(' ->')[0].split(' +')[0]
                # Check if it was a ramp spell by looking at the note
                if any(x in s for x in ['mana)', 'to field', 'to hand', 'Treasure']):
                    ramps.append(spell_name)
        if ramps:
            ramp_t3_games += 1
            ramp_t3_total += len(ramps)
            print(f"  Game {i + 1}: {', '.join(ramps)}")
        else:
            print(f"  Game {i + 1}: NONE")
    print(f"  -> {ramp_t3_games}/{n} games had ramp by T3 (avg {ramp_t3_total / n:.1f} ramp spells)")

    # Commander timing
    cmd_turns = [g['commander_cast_turn'] for g in games if g['commander_cast_turn']]
    if cmd_turns:
        print(f"\nCommander cast: {len(cmd_turns)}/{n} games")
        print(f"  Average turn: {sum(cmd_turns) / len(cmd_turns):.1f}")
        for i, g in enumerate(games):
            if g['commander_cast_turn']:
                print(f"  Game {i + 1}: Turn {g['commander_cast_turn']}")
    else:
        print(f"\nCommander: never cast in {num_turns} turns across all games")

    # Hand size
    avg_hand = sum(g['final_hand'] for g in games) / n
    print(f"\nAvg cards in hand at end: {avg_hand:.1f}")

    # Color availability by turn 2
    print(f"\nColor availability by turn 2:")
    # Determine commander colors
    cmd_colors = set()
    for c in commanders:
        cmd_colors.update(c.color_costs.keys())
        # Also check color identity from mana cost
        for color in 'WUBRG':
            if '{' + color + '}' in c.mana_cost:
                cmd_colors.add(color)

    color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
    for color in sorted(cmd_colors, key=lambda x: 'WUBRG'.index(x)):
        count = 0
        for g in games:
            # Check lands played in first 2 turns
            # This is approximate since we only stored land names
            has_color = False
            for t in g['turns'][:2]:
                if t['land_played']:
                    # We'd need card data to check this properly
                    has_color = True  # simplified
            if has_color:
                count += 1
        # This is approximate - just note it
        # print(f"  {color_names.get(color, color)}: {count}/{n}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Commander deck goldfish simulator')
    parser.add_argument('--games', type=int, default=10)
    parser.add_argument('--turns', type=int, default=6)
    parser.add_argument('--commander-min-x', type=int, default=0)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()

    data = json.load(sys.stdin)
    deck_name, deck_cards, commanders = parse_deck(data)

    land_count = sum(1 for c in deck_cards if c.is_land)
    commander_count = len(commanders)
    total = len(deck_cards) + commander_count

    print(f"{'=' * 65}")
    print(f"GOLDFISH SIMULATOR")
    print(f"{'=' * 65}")
    print(f"Deck:       {deck_name}")
    if commanders:
        print(f"Commander:  {', '.join(c.name for c in commanders)}")
    print(f"Cards:      {total} ({land_count} lands, {total - land_count} nonlands)")
    print(f"Games:      {args.games}")
    print(f"Turns:      {args.turns}")
    if args.commander_min_x > 0:
        print(f"Cmdr min X: {args.commander_min_x}")
    print(f"{'=' * 65}")

    # Classify some cards for info
    ramp_cards = [c for c in deck_cards if c.is_ramp]
    draw_cards = [c for c in deck_cards if c.is_draw]
    creature_cards = [c for c in deck_cards if c.is_creature]
    print(f"\nDetected: {len(ramp_cards)} ramp, {len(draw_cards)} draw, {len(creature_cards)} creatures, {land_count} lands")

    if args.seed is not None:
        base_seed = args.seed
    else:
        base_seed = random.randint(0, 999999)
        print(f"Random seed: {base_seed} (use --seed {base_seed} to reproduce)")

    games = []
    for i in range(args.games):
        rng = random.Random(base_seed + i * 7919)
        game = simulate_game(deck_cards, commanders, rng, args.turns, args.commander_min_x)
        games.append(game)

    # Print per-game logs
    if not args.quiet:
        for i, game in enumerate(games):
            print_game(game, i + 1, lambda c: c.is_land)

    # Print aggregate
    print_aggregate(games, args.turns, commanders)


if __name__ == '__main__':
    main()
