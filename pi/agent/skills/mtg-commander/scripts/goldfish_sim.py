#!/usr/bin/env python3
"""
Generic Commander deck goldfish (solitaire) simulator.

Reads Archidekt deck JSON from stdin and simulates N games of M turns each.
Uses card types, oracle text, mana production, and Archidekt categories
to heuristically resolve spells without hardcoding card names.

Features:
- Draws opening hands with mulligan logic (keeps 2-5 lands)
- Plays lands with color priority
- Tries to cast the commander FIRST each turn if castable at --commander-min-x
  (models real-play decision of holding ramp when commander is castable this turn)
- After commander attempt, casts spells by priority: ramp > draw > creatures > other
- Resolves spell effects: land ramp, mana rocks, draw, sac-draw, kicker
- Resolves draw-then-discard spells (tracks discards)
- Detects and creates tokens from ETB/cast triggers
- Detects and uses activated abilities on permanents (discard outlets, tap
  abilities, token makers) with remaining mana after spell casting
- Resolves upkeep triggers (forced discard, draw-discard wheels)
- Tracks commander casting with optional minimum X value
- Reports per-game logs + aggregate stats including token and discard counts
"""

import json
import sys
import re
import argparse
import random
from dataclasses import dataclass, field
from typing import Optional, List

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
    discard_count: int = 0           # how many cards this spell forces you to discard
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

    # Token creation on ETB/cast
    etb_token_count: int = 0         # number of creature tokens created on ETB
    etb_token_power: int = 0         # power of created tokens
    etb_token_toughness: int = 0
    etb_token_type: str = ""         # e.g. "Zombie", "Soldier"

    # Non-creature artifact token creation on ETB/cast
    etb_clue_count: int = 0          # Clue tokens ({2}, Sac: Draw a card)
    etb_treasure_count: int = 0      # Treasure tokens (Sac: Add one mana)
    etb_blood_count: int = 0         # Blood tokens ({1}, Discard, Sac: Draw a card)
    etb_food_count: int = 0          # Food tokens ({2}, Sac: Gain 3 life)
    etb_powerstone_count: int = 0    # Powerstone tokens (nonartifact restricted mana)
    etb_map_count: int = 0           # Map tokens ({1}, Sac: explore)

    # Activated abilities (parsed from oracle text)
    activated_abilities: list = field(default_factory=list)
    # Each entry: {'type': str, 'mana_cost': int, 'needs_tap': bool,
    #              'needs_discard': int, 'effect': str, ...}

    # Upkeep triggers
    has_upkeep_draw: bool = False
    upkeep_draw_count: int = 0
    has_upkeep_discard: bool = False
    upkeep_discard_count: int = 0
    has_upkeep_discard_draw: bool = False  # "discard hand, draw that many"
    has_upkeep_forced_discard: bool = False  # Bottomless Pit style

    # Attack triggers
    attack_token_count: int = 0
    attack_token_type: str = ""

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
        self._parse_etb_tokens()
        self._parse_noncreature_tokens()
        self._parse_attack_tokens()
        self._parse_activated_abilities()
        self._parse_upkeep_triggers()
        self._parse_discard_effect()

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
            if re.search(r'\{t\}:\s*add\s+\{', text_lower) or self.produces_colors:
                self.is_ramp = True
                self.extra_mana = max(
                    (v for v in self.mana_production.values() if v is not None), default=1
                )

        # Land ramp: search library for land/forest/etc, put onto battlefield
        if re.search(r'search your library for .{0,40}(basic )?(land|forest|plains|island|swamp|mountain) cards?.{0,40}put .{0,30}onto the battlefield', text_lower):
            self.is_land_ramp = True
            self.is_ramp = True

            if re.search(r'up to two basic land cards.{0,60}(put one onto the battlefield|one onto the battlefield).{0,40}(other|the other) into your hand', text_lower):
                self.lands_to_field = 1
                self.lands_to_hand = 1
            elif re.search(r'up to two basic land cards.{0,30}put them onto the battlefield', text_lower):
                self.lands_to_field = 2
            elif re.search(r'search your library for .{0,50}(basic land|forest|plains|island|swamp|mountain) card.{0,10}put .{0,15}onto the battlefield', text_lower):
                self.lands_to_field = 1

            if 'kicker' in text_lower and re.search(r'kicked.{0,50}two basic land cards', text_lower):
                self.lands_to_field = 1

        # Category-based ramp fallback
        if is_ramp_category and not self.is_ramp:
            self.is_ramp = True
            if self.is_land_ramp or self.lands_to_field > 0:
                pass
            elif self.extra_mana == 0:
                self.extra_mana = 1

        # Additional cost detection
        if re.search(r'(additional cost|as an additional cost|kicker).{0,30}sacrifice a creature', text_lower):
            self.needs_sac_creature = True
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice a land', text_lower):
            self.needs_sac_land = True
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice an? artifact', text_lower):
            self.needs_sac_artifact = True
        if re.search(r'(additional cost|as an additional cost).{0,30}sacrifice an? (artifact or creature|creature or artifact)', text_lower):
            self.needs_sac_creature = True
            self.needs_sac_artifact = True

        # Draw detection
        draw_text = text_lower
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment or self.is_planeswalker

        if is_permanent:
            lines = text_lower.split('\n')
            etb_draw_lines = []
            for line in lines:
                if re.match(r'^\{.*\}.*:', line):
                    continue
                if re.match(r'^[^:]+,\s*\{.*\}.*:', line):
                    continue
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
            if self.needs_sac_creature or self.needs_sac_artifact:
                self.is_sac_draw = True

        if 'draw' in cats_lower and not self.is_draw:
            if not is_permanent:
                self.is_draw = True
                self.draw_count = max(self.draw_count, 1)

        if re.search(r'choose three', text_lower) and self.draw_count == 1:
            self.draw_count = 3

        # Harrow special case
        if self.needs_sac_land and self.is_land_ramp:
            if re.search(r'up to two basic land cards.{0,30}put them onto the battlefield', text_lower):
                self.lands_to_field = 2

        # Spells that need a creature target
        if (self.is_instant or self.is_sorcery) and not self.needs_sac_creature:
            if re.search(r'target creature (gets|you control)', text_lower):
                if not re.search(r'choose (one|two|three|four|five)', text_lower):
                    self.needs_creature_target = True

    def _parse_discard_effect(self):
        """Detect how many cards a spell forces you to discard on resolution."""
        if self.is_land:
            return
        text_lower = self.text.lower()
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment or self.is_planeswalker

        # Only parse discard effects on instants/sorceries (not activated abilities)
        if is_permanent:
            return

        word_to_num = {'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4}

        # "draw X cards, then discard Y cards" pattern
        m = re.search(r'then discard (\w+) cards?', text_lower)
        if m:
            val = m.group(1).lower()
            self.discard_count = word_to_num.get(val, int(val) if val.isdigit() else 1)
            return

        # "discard a card" at end (e.g. Pull from Tomorrow)
        m = re.search(r'then discard a card', text_lower)
        if m:
            self.discard_count = 1
            return

        # "draws three cards. Then that player discards two cards" (Compulsive Research)
        m = re.search(r'discards? (\w+) cards?', text_lower)
        if m and 'draw' in text_lower:
            val = m.group(1).lower()
            self.discard_count = word_to_num.get(val, int(val) if val.isdigit() else 1)

    def _parse_etb_tokens(self):
        """Parse 'enters' + 'create' token patterns from oracle text."""
        text_lower = self.text.lower()
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment or self.is_planeswalker
        if not is_permanent and not self.is_sorcery and not self.is_instant:
            return

        # Match: "when ... enters" or "enters the battlefield" combined with "create" tokens
        # Also match cast triggers on instants/sorceries
        lines = text_lower.split('\n')
        for line in lines:
            # Skip activated abilities
            if re.match(r'^\{.*\}.*:', line):
                continue
            if re.match(r'^[^:]+,\s*\{.*\}.*:', line):
                continue

            # Check for enters/cast trigger with token creation
            if not (('enters' in line or 'when you cast' in line) and 'create' in line):
                # Also check instants/sorceries that just create tokens
                if not ((self.is_instant or self.is_sorcery) and 'create' in line):
                    continue

            # Parse: "create [a/an/two/three] X/Y [color] [Type] creature token[s]"
            token_match = re.search(
                r'create (\w+) (\d+)/(\d+) .{0,30}?(\w+) creature tokens?',
                line
            )
            if token_match:
                word_to_num = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
                count_word = token_match.group(1).lower()
                self.etb_token_count = word_to_num.get(count_word, int(count_word) if count_word.isdigit() else 1)
                self.etb_token_power = int(token_match.group(2))
                self.etb_token_toughness = int(token_match.group(3))
                self.etb_token_type = token_match.group(4).capitalize()
                break

    def _parse_noncreature_tokens(self):
        """Parse non-creature artifact token creation (Clue, Treasure, Blood, Food, Powerstone, Map).
        
        Detects:
        - 'investigate' keyword or 'create a Clue token' in ETB/cast triggers
        - 'create a Treasure token' / 'create two Treasure tokens' etc.
        - 'create a Blood token' / 'create a Food token'
        - 'create a Powerstone token' / 'create a Map token'
        Also detects instant/sorcery token creation.
        """
        text_lower = self.text.lower()
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment or self.is_planeswalker
        if not is_permanent and not self.is_sorcery and not self.is_instant:
            return

        # Check for 'Investigate' keyword (always means create a Clue on ETB/trigger)
        if 'Investigate' in self.keywords:
            self.etb_clue_count = max(self.etb_clue_count, 1)

        word_to_num = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}

        # Token types to detect: (field_name, pattern_name)
        token_types = [
            ('etb_clue_count', 'clue'),
            ('etb_treasure_count', 'treasure'),
            ('etb_blood_count', 'blood'),
            ('etb_food_count', 'food'),
            ('etb_powerstone_count', 'powerstone'),
            ('etb_map_count', 'map'),
        ]

        lines = text_lower.split('\n')
        for line in lines:
            # Skip activated abilities
            if re.match(r'^\{.*\}.*:', line):
                continue
            if re.match(r'^[^:]+,\s*\{.*\}.*:', line):
                continue

            # Must be an ETB/cast trigger, or instant/sorcery
            is_trigger = ('enters' in line or 'when you cast' in line
                         or 'enters the battlefield' in line)
            is_spell = (self.is_instant or self.is_sorcery)
            if not is_trigger and not is_spell:
                continue

            # Also detect 'investigate' in trigger lines
            if 'investigate' in line:
                self.etb_clue_count = max(self.etb_clue_count, 1)

            for field_name, token_name in token_types:
                # Match: "create [a/an/two/three] [Token_type] token[s]"
                pattern = rf'create (\w+) {token_name} tokens?'
                match = re.search(pattern, line)
                if match:
                    count_word = match.group(1).lower()
                    count = word_to_num.get(count_word, int(count_word) if count_word.isdigit() else 1)
                    current = getattr(self, field_name)
                    setattr(self, field_name, max(current, count))

    def _parse_attack_tokens(self):
        """Parse 'attacks' + 'create' token patterns."""
        text_lower = self.text.lower()
        if not self.is_creature:
            return

        lines = text_lower.split('\n')
        for line in lines:
            if 'attacks' in line and 'create' in line:
                token_match = re.search(
                    r'create (\w+) (\d+)/(\d+) .{0,30}?(\w+) creature tokens?',
                    line
                )
                if token_match:
                    word_to_num = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3}
                    count_word = token_match.group(1).lower()
                    self.attack_token_count = word_to_num.get(count_word, int(count_word) if count_word.isdigit() else 1)
                    self.attack_token_type = token_match.group(4).capitalize()
                    break

    def _parse_activated_abilities(self):
        """Parse activated abilities from oracle text lines.
        
        Detects patterns like:
        - "{2}, {T}: Create a 1/1 token"
        - "Discard two cards: Create a 2/2 token"
        - "{1}{B}, {T}, Discard a card: Create a 2/2 token"
        - "{B}, {T}, Discard a card: Add {B}{B}{B}"
        """
        self.activated_abilities = []
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment
        if not is_permanent:
            return

        text_lower = self.text.lower()
        lines = text_lower.split('\n')

        for line in lines:
            # Activated abilities have a colon separating cost from effect
            if ':' not in line:
                continue

            # Split on first colon that's part of activated ability syntax
            # (not mana symbols like {B}: which are within the cost)
            # Heuristic: find the main cost:effect separator
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            cost_part = parts[0].strip()
            effect_part = parts[1].strip()

            # Skip triggered abilities ("when", "whenever", "at the beginning")
            if cost_part.startswith(('when', 'whenever', 'at the')):
                continue

            # Parse mana cost from the cost part
            mana_symbols = re.findall(r'\{([^}]+)\}', cost_part)
            needs_tap = 't' in mana_symbols
            mana_symbols_no_tap = [s for s in mana_symbols if s.lower() != 't']

            # Calculate total mana cost
            total_mana = 0
            color_requirements = {}
            for sym in mana_symbols_no_tap:
                if sym.isdigit():
                    total_mana += int(sym)
                elif sym in 'WUBRG':
                    total_mana += 1
                    color_requirements[sym] = color_requirements.get(sym, 0) + 1

            # Parse discard cost
            discard_cost = 0
            word_to_num = {'a': 1, 'one': 1, 'two': 2, 'three': 3}
            disc_match = re.search(r'discard (\w+) cards?', cost_part)
            if disc_match:
                val = disc_match.group(1).lower()
                discard_cost = word_to_num.get(val, int(val) if val.isdigit() else 1)
            elif 'discard a card' in cost_part:
                discard_cost = 1

            ability = {
                'line': line,
                'mana_cost': total_mana,
                'needs_tap': needs_tap,
                'discard_cost': discard_cost,
                'color_requirements': color_requirements,
                'effect': effect_part,
                'type': 'unknown',
            }

            # Classify the effect
            # Token creation
            token_match = re.search(
                r'create (\w+) (\d+)/(\d+) .{0,30}?(\w+) creature tokens?',
                effect_part
            )
            if token_match:
                count_word = token_match.group(1).lower()
                ability['type'] = 'create_token'
                ability['token_count'] = word_to_num.get(count_word, int(count_word) if count_word.isdigit() else 1)
                ability['token_power'] = int(token_match.group(2))
                ability['token_type'] = token_match.group(4).capitalize()

            # Mana production (e.g., "add {B}{B}{B}")
            elif re.search(r'add \{', effect_part):
                add_match = re.findall(r'\{([WUBRGC])\}', effect_part)
                ability['type'] = 'add_mana'
                ability['mana_produced'] = len(add_match)

            # Draw
            elif 'draw' in effect_part:
                draw_match = re.search(r'draw (\w+) cards?', effect_part)
                if draw_match:
                    val = draw_match.group(1).lower()
                    ability['type'] = 'draw'
                    ability['draw_count'] = word_to_num.get(val, int(val) if val.isdigit() else 1)
                elif 'draw a card' in effect_part:
                    ability['type'] = 'draw'
                    ability['draw_count'] = 1

            # Only add abilities we understand
            if ability['type'] != 'unknown':
                self.activated_abilities.append(ability)

    def _parse_upkeep_triggers(self):
        """Detect upkeep triggers from oracle text."""
        text_lower = self.text.lower()
        is_permanent = self.is_creature or self.is_artifact or self.is_enchantment
        if not is_permanent:
            return

        lines = text_lower.split('\n')
        for line in lines:
            if 'beginning of' not in line or 'upkeep' not in line:
                continue

            # "discard a card at random" (Bottomless Pit)
            if re.search(r'discard.{0,10}card.{0,10}random', line):
                self.has_upkeep_forced_discard = True

            # "you may discard all the cards in your hand. If you do, draw that many"
            if re.search(r'discard all.{0,20}cards.{0,20}hand.{0,40}draw that many', line):
                self.has_upkeep_discard_draw = True

            # "draw a card" at upkeep
            if re.search(r'draw (\w+) cards?', line) and 'discard' not in line:
                m = re.search(r'draw (\w+) cards?', line)
                word_to_num = {'a': 1, 'one': 1, 'two': 2, 'three': 3}
                if m:
                    val = m.group(1).lower()
                    self.has_upkeep_draw = True
                    self.upkeep_draw_count = word_to_num.get(val, int(val) if val.isdigit() else 1)

    def produces_color(self, color):
        """Check if this permanent can produce a specific color."""
        if color in self.produces_colors:
            return True
        return False

    def __repr__(self):
        return self.name

    def __hash__(self):
        return id(self)


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
    tokens: int = 0  # total creature tokens on battlefield
    clue_tokens: int = 0      # Clue tokens ({2}, Sac: Draw a card)
    treasure_tokens: int = 0  # Treasure tokens (Sac: Add one mana of any color)
    blood_tokens: int = 0     # Blood tokens ({1}, Discard, Sac: Draw a card)
    food_tokens: int = 0      # Food tokens ({2}, Sac: Gain 3 life)
    powerstone_tokens: int = 0  # Powerstone tokens (restricted mana)
    map_tokens: int = 0       # Map tokens ({1}, Sac: explore)
    total_discards: int = 0  # total cards discarded this game
    turn_discards: int = 0  # cards discarded this turn
    creatures_entered_this_turn: set = field(default_factory=set)  # for summoning sickness
    tapped_creatures: set = field(default_factory=set)  # tapped creature ids

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

    def can_tap_creature(self, card):
        """Check if a specific creature card can be tapped (not sick, not already tapped)."""
        return (id(card) not in self.tapped_creatures and
                id(card) not in self.creatures_entered_this_turn)

    def tap_creature(self, card):
        """Mark a creature as tapped."""
        self.tapped_creatures.add(id(card))


# =============================================================================
# Simulation helpers
# =============================================================================

def land_priority(card, game_state):
    """Score a land for play priority. Higher = play first."""
    score = 0
    color_count = sum(1 for c in 'WUBRG' if card.produces_color(c))
    score += color_count * 5
    for c in 'WUBRG':
        if card.produces_color(c) and not game_state.color_available(c):
            score += 20
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


def choose_discards(hand, count):
    """Choose cards to discard from hand. Prefers non-lands, higher CMC first."""
    if len(hand) <= count:
        return list(hand)
    # Score: higher = discard first
    def score(c):
        s = 0
        if c.is_land:
            s -= 10  # prefer keeping lands
        s += c.cmc  # discard expensive stuff we can't cast
        return s
    sorted_hand = sorted(hand, key=lambda c: -score(c))
    return sorted_hand[:count]


# =============================================================================
# Simulation
# =============================================================================

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
        state.turn_discards = 0
        state.creatures_entered_this_turn = set()
        state.tapped_creatures = set()

        turn_log = {
            'turn': turn,
            'drawn': None,
            'land_played': None,
            'spells': [],
            'activations': [],
            'mana_after': 0,
            'hand_size': 0,
            'lands_on_field': 0,
            'tokens': 0,
            'total_discards': 0,
        }

        # =================================================================
        # UPKEEP PHASE — resolve upkeep triggers on permanents
        # =================================================================
        for perm in state.battlefield_creatures + state.battlefield_other:
            # Forced random discard (Bottomless Pit)
            if perm.has_upkeep_forced_discard and state.hand:
                victim = rng.choice(state.hand)
                state.hand.remove(victim)
                state.graveyard.append(victim)
                state.total_discards += 1
                state.turn_discards += 1
                turn_log['spells'].append(f"Upkeep: {perm.name} -> discard {victim.name}")

            # Discard-hand-draw-that-many (Forgotten Creation)
            if perm.has_upkeep_discard_draw and len(state.hand) > 0:
                hand_size = len(state.hand)
                discarded_names = [c.name for c in state.hand[:3]]
                suffix = '...' if hand_size > 3 else ''
                old_hand = list(state.hand)
                state.hand.clear()
                for card in old_hand:
                    state.graveyard.append(card)
                    state.total_discards += 1
                    state.turn_discards += 1
                drawn = []
                for _ in range(hand_size):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn.append(d.name)
                turn_log['spells'].append(
                    f"Upkeep: {perm.name} -> discarded {hand_size} "
                    f"({', '.join(discarded_names)}{suffix}) -> drew {len(drawn)}"
                )

            # Upkeep draw
            if perm.has_upkeep_draw:
                drawn = []
                for _ in range(perm.upkeep_draw_count):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn.append(d.name)
                if drawn:
                    turn_log['spells'].append(f"Upkeep: {perm.name} -> draw {len(drawn)}")

        # Graveyard recursion heuristic: cards with "beginning of your upkeep"
        # + "return ... to your hand" (e.g. Master of Death, Bloodghast)
        for card in list(state.graveyard):
            text_lower = card.text.lower()
            if ('beginning of your upkeep' in text_lower and
                    re.search(r'return (it|this card) to (your|its owner.s) hand', text_lower)):
                state.graveyard.remove(card)
                state.hand.append(card)
                turn_log['spells'].append(f"Upkeep: {card.name} returned from graveyard")

        # =================================================================
        # DRAW PHASE
        # =================================================================
        if turn > 1 and state.library:
            drawn = state.library.pop(0)
            state.hand.append(drawn)
            turn_log['drawn'] = drawn.name

        # =================================================================
        # LAND DROP
        # =================================================================
        hand_lands = [c for c in state.hand if c.is_land]
        if hand_lands:
            hand_lands.sort(key=lambda l: -land_priority(l, state))
            chosen = hand_lands[0]
            state.hand.remove(chosen)
            state.battlefield_lands.append(chosen)
            turn_log['land_played'] = chosen.name

        mana_left = state.total_mana

        # =================================================================
        # TRY CASTING COMMANDER FIRST (if castable at min_x)
        # This models the real-play decision of holding ramp when you could cast commander instead.
        # =================================================================
        for cmdr in list(state.commander_zone):
            base_cost = sum(cmdr.color_costs.values())
            if cmdr.has_x_cost:
                min_needed = base_cost + commander_min_x
                if mana_left >= min_needed and state.can_cast(cmdr, mana_left):
                    x_val = mana_left - base_cost
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    state.creatures_entered_this_turn.add(id(cmdr))
                    game_log['commander_cast_turn'] = turn
                    revealed_cards = []
                    creatures_milled = []
                    non_creatures_to_bottom = []
                    if 'reveal cards from the top of your library' in cmdr.text.lower() and 'creature' in cmdr.text.lower():
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
                        rng.shuffle(non_creatures_to_bottom)
                        state.library.extend(non_creatures_to_bottom)
                    note = f"{cmdr.name} (X={x_val}) [cast-first]"
                    if revealed_cards:
                        note += f" -> revealed {len(revealed_cards)} cards, {', '.join(creatures_milled)} to graveyard"
                    turn_log['spells'].append(note)
                    mana_left = 0
                    if cmdr.etb_token_count > 0:
                        state.tokens += cmdr.etb_token_count
            else:
                if mana_left >= cmdr.cmc and state.can_cast(cmdr, mana_left):
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    state.creatures_entered_this_turn.add(id(cmdr))
                    game_log['commander_cast_turn'] = turn
                    turn_log['spells'].append(cmdr.name + " [cast-first]")
                    mana_left -= cmdr.cmc

        # =================================================================
        # CAST SPELLS FROM HAND
        # =================================================================
        max_iterations = 20
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
                    if 'treasure' in card.text.lower() or 'create a treasure' in card.text.lower():
                        mana_left += 1
                        state.ramp_mana += 1
                        note += " + Treasure"

            # Land ramp
            elif card.is_land_ramp:
                actual_to_field = card.lands_to_field
                actual_to_hand = card.lands_to_hand

                if 'kicker' in card.text.lower() and 'sacrifice a creature' in card.text.lower():
                    if sacced_creature or (state.battlefield_creatures and not card.needs_sac_creature):
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

                for _ in range(actual_to_field):
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
                    state.creatures_entered_this_turn.add(id(card))
                else:
                    state.battlefield_other.append(card)
                note = f"{card.name} (+{card.extra_mana} mana)"

            # Non-sac draw spells (with possible discard)
            elif card.is_draw and not card.is_sac_draw:
                drawn_cards = []
                for _ in range(card.draw_count):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn_cards.append(d.name)

                # Handle discard portion of draw-discard spells
                if card.discard_count > 0 and state.hand:
                    discards = choose_discards(state.hand, card.discard_count)
                    actual_discarded = []
                    for dc in discards:
                        if dc in state.hand:
                            state.hand.remove(dc)
                            state.graveyard.append(dc)
                            state.total_discards += 1
                            state.turn_discards += 1
                            actual_discarded.append(dc.name)
                    note = f"{card.name} -> draw {len(drawn_cards)}, discard {len(actual_discarded)} ({', '.join(actual_discarded)})"

                    # Frantic Search untap lands
                    if 'untap' in card.text.lower() and 'land' in card.text.lower():
                        untap_match = re.search(r'untap up to (\w+) lands', card.text.lower())
                        if untap_match:
                            word_to_num = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
                            val = untap_match.group(1).lower()
                            untap_count = word_to_num.get(val, int(val) if val.isdigit() else 3)
                            mana_left += untap_count
                            note += f", untap {untap_count} lands"
                else:
                    note = f"{card.name} -> draw {len(drawn_cards)}"

            # Creatures (enter battlefield + ETB tokens)
            elif card.is_creature:
                state.battlefield_creatures.append(card)
                state.creatures_entered_this_turn.add(id(card))

                if card.etb_token_count > 0:
                    state.tokens += card.etb_token_count
                    note = f"{card.name} -> ETB: {card.etb_token_count}x {card.etb_token_power}/{card.etb_token_toughness} {card.etb_token_type} token(s)"

            # Other permanents
            elif card.is_artifact or card.is_enchantment or card.is_planeswalker:
                state.battlefield_other.append(card)

            # Instants/sorceries that create tokens
            if (card.is_instant or card.is_sorcery) and card.etb_token_count > 0:
                state.tokens += card.etb_token_count
                note = f"{card.name} -> {card.etb_token_count}x {card.etb_token_power}/{card.etb_token_toughness} {card.etb_token_type} token(s)"

            # Non-creature artifact tokens (Clue, Treasure, Blood, Food, Powerstone, Map)
            noncreature_token_notes = []
            if card.etb_clue_count > 0:
                state.clue_tokens += card.etb_clue_count
                noncreature_token_notes.append(f"{card.etb_clue_count} Clue")
            if card.etb_treasure_count > 0:
                state.treasure_tokens += card.etb_treasure_count
                mana_left += card.etb_treasure_count  # Treasures are immediate mana
                noncreature_token_notes.append(f"{card.etb_treasure_count} Treasure")
            if card.etb_blood_count > 0:
                state.blood_tokens += card.etb_blood_count
                noncreature_token_notes.append(f"{card.etb_blood_count} Blood")
            if card.etb_food_count > 0:
                state.food_tokens += card.etb_food_count
                noncreature_token_notes.append(f"{card.etb_food_count} Food")
            if card.etb_powerstone_count > 0:
                state.powerstone_tokens += card.etb_powerstone_count
                state.ramp_mana += card.etb_powerstone_count  # Powerstones are persistent ramp
                noncreature_token_notes.append(f"{card.etb_powerstone_count} Powerstone")
            if card.etb_map_count > 0:
                state.map_tokens += card.etb_map_count
                noncreature_token_notes.append(f"{card.etb_map_count} Map")
            if noncreature_token_notes:
                note += f" + {', '.join(noncreature_token_notes)} token(s)"

            turn_log['spells'].append(note)
            if card.is_instant or card.is_sorcery:
                state.graveyard.append(card)

            mana_left = state.total_mana - (state.total_mana - mana_left) if mana_left >= 0 else 0

        # =================================================================
        # TRY CASTING COMMANDER
        # =================================================================
        for cmdr in list(state.commander_zone):
            min_mana_needed = max(cmdr.color_costs.values(), default=0)
            base_cost = sum(cmdr.color_costs.values())
            if cmdr.has_x_cost:
                min_needed = base_cost + commander_min_x
                if mana_left >= min_needed and state.can_cast(cmdr, mana_left):
                    x_val = mana_left - base_cost
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    state.creatures_entered_this_turn.add(id(cmdr))
                    game_log['commander_cast_turn'] = turn

                    revealed_cards = []
                    creatures_milled = []
                    non_creatures_to_bottom = []
                    if 'reveal cards from the top of your library' in cmdr.text.lower() and 'creature' in cmdr.text.lower():
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
                        rng.shuffle(non_creatures_to_bottom)
                        state.library.extend(non_creatures_to_bottom)

                    note = f"{cmdr.name} (X={x_val})"
                    if revealed_cards:
                        note += f" -> revealed {len(revealed_cards)} cards, {', '.join(creatures_milled)} to graveyard"
                    turn_log['spells'].append(note)
                    mana_left = 0

                    # ETB tokens on commander
                    if cmdr.etb_token_count > 0:
                        state.tokens += cmdr.etb_token_count
                        turn_log['spells'].append(
                            f"  -> ETB: {cmdr.etb_token_count}x {cmdr.etb_token_type} token(s)"
                        )
            else:
                if mana_left >= cmdr.cmc and state.can_cast(cmdr, mana_left):
                    state.commander_zone.remove(cmdr)
                    state.battlefield_creatures.append(cmdr)
                    state.creatures_entered_this_turn.add(id(cmdr))
                    game_log['commander_cast_turn'] = turn
                    turn_log['spells'].append(cmdr.name)
                    mana_left -= cmdr.cmc

                    if cmdr.etb_token_count > 0:
                        state.tokens += cmdr.etb_token_count
                        turn_log['spells'].append(
                            f"  -> ETB: {cmdr.etb_token_count}x {cmdr.etb_token_type} token(s)"
                        )

        # =================================================================
        # ACTIVATED ABILITIES PHASE
        # Use activated abilities on permanents with remaining mana/cards.
        # Prioritizes: token creation > draw > mana production
        # =================================================================
        max_ability_iter = 10
        ability_iter = 0
        while ability_iter < max_ability_iter:
            ability_iter += 1
            best_ability = None
            best_card = None
            best_priority = 999

            for perm in state.battlefield_creatures + state.battlefield_other:
                for ability in perm.activated_abilities:
                    # Check mana
                    if ability['mana_cost'] > mana_left:
                        continue
                    # Check color requirements
                    can_pay = True
                    for color, cnt in ability.get('color_requirements', {}).items():
                        if not state.color_available(color):
                            can_pay = False
                            break
                    if not can_pay:
                        continue
                    # Check tap requirement
                    if ability['needs_tap']:
                        if not perm.is_creature:
                            pass  # artifacts/enchantments don't have summoning sickness
                        elif not state.can_tap_creature(perm):
                            continue
                    # Check discard requirement
                    if ability['discard_cost'] > 0:
                        non_land_hand = [c for c in state.hand if not c.is_land]
                        if len(state.hand) < ability['discard_cost']:
                            continue
                        # Keep at least 1 card in hand unless we have lots
                        if len(state.hand) - ability['discard_cost'] < 1 and len(state.hand) < 4:
                            continue

                    # Priority: tokens (0) > draw (1) > mana (2)
                    prio = {'create_token': 0, 'draw': 1, 'add_mana': 2}.get(ability['type'], 3)
                    if prio < best_priority:
                        best_priority = prio
                        best_ability = ability
                        best_card = perm

            if best_ability is None:
                break

            # Execute the ability
            ability = best_ability
            perm = best_card

            # Pay costs
            mana_left -= ability['mana_cost']
            if ability['needs_tap'] and perm.is_creature:
                state.tap_creature(perm)
            if ability['needs_tap'] and not perm.is_creature:
                # Mark non-creature as tapped (simplified: allow once per turn)
                # Remove from available abilities by tracking
                perm.activated_abilities = [a for a in perm.activated_abilities if a is not ability]

            # Pay discard cost
            if ability['discard_cost'] > 0:
                discards = choose_discards(state.hand, ability['discard_cost'])
                discarded_names = []
                for dc in discards:
                    if dc in state.hand:
                        state.hand.remove(dc)
                        state.graveyard.append(dc)
                        state.total_discards += 1
                        state.turn_discards += 1
                        discarded_names.append(dc.name)

            # Resolve effect
            if ability['type'] == 'create_token':
                count = ability.get('token_count', 1)
                state.tokens += count
                ttype = ability.get('token_type', 'creature')
                disc_str = f" (discard: {', '.join(discarded_names)})" if ability['discard_cost'] > 0 else ""
                turn_log['activations'].append(
                    f"{perm.name}{disc_str} -> {count}x {ttype} token(s)"
                )
            elif ability['type'] == 'draw':
                draw_count = ability.get('draw_count', 1)
                drawn = []
                for _ in range(draw_count):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn.append(d.name)
                disc_str = f" (discard: {', '.join(discarded_names)})" if ability['discard_cost'] > 0 else ""
                turn_log['activations'].append(
                    f"{perm.name}{disc_str} -> draw {len(drawn)}"
                )
            elif ability['type'] == 'add_mana':
                produced = ability.get('mana_produced', 1)
                mana_left += produced
                disc_str = f" (discard: {', '.join(discarded_names)})" if ability['discard_cost'] > 0 else ""
                turn_log['activations'].append(
                    f"{perm.name}{disc_str} -> +{produced} mana"
                )

        # =================================================================
        # CRACK TOKENS PHASE — spend remaining mana on Clue/Blood tokens
        # =================================================================
        # Crack Clue tokens: {2}, Sacrifice: Draw a card
        while state.clue_tokens > 0 and mana_left >= 2:
            state.clue_tokens -= 1
            mana_left -= 2
            if state.library:
                d = state.library.pop(0)
                state.hand.append(d)
                turn_log['activations'].append(f"Crack Clue -> draw ({d.name})")

        # Crack Blood tokens: {1}, Discard a card, Sacrifice: Draw a card
        while state.blood_tokens > 0 and mana_left >= 1 and len(state.hand) >= 2:
            state.blood_tokens -= 1
            mana_left -= 1
            discards = choose_discards(state.hand, 1)
            if discards:
                dc = discards[0]
                state.hand.remove(dc)
                state.graveyard.append(dc)
                state.total_discards += 1
                state.turn_discards += 1
            if state.library:
                d = state.library.pop(0)
                state.hand.append(d)
                turn_log['activations'].append(f"Crack Blood (discard {dc.name}) -> draw ({d.name})")

        # Crack Treasure tokens for mana (already counted as immediate mana above,
        # but unspent Treasures persist — track for reporting)
        # Note: Treasures are consumed when used for mana during casting.
        # Here we just track remaining ones.

        # =================================================================
        # COMBAT PHASE — attack triggers for creatures not sick
        # =================================================================
        for perm in state.battlefield_creatures:
            if perm.attack_token_count > 0 and id(perm) not in state.creatures_entered_this_turn:
                state.tokens += perm.attack_token_count
                turn_log['spells'].append(
                    f"Combat: {perm.name} attacks -> {perm.attack_token_count}x {perm.attack_token_type} token(s)"
                )

        turn_log['mana_after'] = state.total_mana
        turn_log['hand_size'] = len(state.hand)
        turn_log['lands_on_field'] = len(state.battlefield_lands)
        turn_log['tokens'] = state.tokens
        turn_log['clue_tokens'] = state.clue_tokens
        turn_log['treasure_tokens'] = state.treasure_tokens
        turn_log['blood_tokens'] = state.blood_tokens
        turn_log['food_tokens'] = state.food_tokens
        turn_log['total_discards'] = state.total_discards
        game_log['turns'].append(turn_log)

    game_log['final_mana'] = state.total_mana
    game_log['final_lands'] = len(state.battlefield_lands)
    game_log['final_hand'] = len(state.hand)
    game_log['board_creatures'] = [c.name for c in state.battlefield_creatures]
    game_log['board_other'] = [c.name for c in state.battlefield_other]
    game_log['graveyard'] = [c.name for c in state.graveyard]
    game_log['final_tokens'] = state.tokens
    game_log['final_clue_tokens'] = state.clue_tokens
    game_log['final_treasure_tokens'] = state.treasure_tokens
    game_log['final_blood_tokens'] = state.blood_tokens
    game_log['final_food_tokens'] = state.food_tokens
    game_log['final_discards'] = state.total_discards

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
        if t.get('activations'):
            for a in t['activations']:
                print(f"    Activate: {a}")
        if not t['spells'] and not t.get('activations'):
            print(f"    (no spells cast)")
        ramp_extra = t['mana_after'] - t['lands_on_field']
        ramp_str = f" + {ramp_extra} ramp" if ramp_extra else ""
        tokens_parts = []
        if t['tokens']:
            tokens_parts.append(f"{t['tokens']} creature")
        if t.get('clue_tokens'):
            tokens_parts.append(f"{t['clue_tokens']} Clue")
        if t.get('treasure_tokens'):
            tokens_parts.append(f"{t['treasure_tokens']} Treasure")
        if t.get('blood_tokens'):
            tokens_parts.append(f"{t['blood_tokens']} Blood")
        if t.get('food_tokens'):
            tokens_parts.append(f"{t['food_tokens']} Food")
        tokens_str = f", tokens: {', '.join(tokens_parts)}" if tokens_parts else ""
        disc_str = f", {t['total_discards']} discards" if t['total_discards'] else ""
        print(f"    -> {t['mana_after']} mana ({t['lands_on_field']} lands{ramp_str}), {t['hand_size']} in hand{tokens_str}{disc_str}")

    print(f"\n  === End state ===")
    ramp = game['final_mana'] - game['final_lands']
    print(f"  Mana: {game['final_mana']} ({game['final_lands']} lands + {ramp} ramp)")
    print(f"  Hand: {game['final_hand']} cards")
    board = game['board_creatures'] + game['board_other']
    print(f"  Board: {', '.join(board) if board else '(empty)'}")
    token_parts = []
    if game['final_tokens']:
        token_parts.append(f"{game['final_tokens']} creature")
    if game.get('final_clue_tokens'):
        token_parts.append(f"{game['final_clue_tokens']} Clue")
    if game.get('final_treasure_tokens'):
        token_parts.append(f"{game['final_treasure_tokens']} Treasure")
    if game.get('final_blood_tokens'):
        token_parts.append(f"{game['final_blood_tokens']} Blood")
    if game.get('final_food_tokens'):
        token_parts.append(f"{game['final_food_tokens']} Food")
    if token_parts:
        print(f"  Tokens: {', '.join(token_parts)}")
    if game['final_discards']:
        print(f"  Total discards: {game['final_discards']}")
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
                spell_name = s.split(' (')[0].split(' ->')[0].split(' +')[0]
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

    # Token count (creature)
    token_games = [g['final_tokens'] for g in games]
    if any(t > 0 for t in token_games):
        print(f"\nCreature tokens on battlefield:")
        print(f"  Average: {sum(token_games) / n:.1f}")
        print(f"  Min: {min(token_games)}, Max: {max(token_games)}")
        print(f"\n  Token progression:")
        for turn in range(1, num_turns + 1):
            avg = sum(g['turns'][turn - 1]['tokens'] for g in games) / n
            if avg > 0:
                print(f"    Turn {turn}: avg {avg:.1f}")

    # Non-creature artifact tokens
    for token_key, token_name in [('final_clue_tokens', 'Clue'), ('final_treasure_tokens', 'Treasure'),
                                   ('final_blood_tokens', 'Blood'), ('final_food_tokens', 'Food')]:
        vals = [g.get(token_key, 0) for g in games]
        if any(v > 0 for v in vals):
            print(f"\n{token_name} tokens (remaining at end):")
            print(f"  Average: {sum(vals) / n:.1f}, Max: {max(vals)}")

    # Discard count
    disc_games = [g['final_discards'] for g in games]
    if any(d > 0 for d in disc_games):
        print(f"\nTotal discards:")
        print(f"  Average: {sum(disc_games) / n:.1f}")
        print(f"  Min: {min(disc_games)}, Max: {max(disc_games)}")
        print(f"\n  Discard progression:")
        for turn in range(1, num_turns + 1):
            avg = sum(g['turns'][turn - 1]['total_discards'] for g in games) / n
            if avg > 0:
                print(f"    Turn {turn}: avg {avg:.1f}")

    # Color availability by turn 2
    print(f"\nColor availability by turn 2:")
    cmd_colors = set()
    for c in commanders:
        cmd_colors.update(c.color_costs.keys())
        for color in 'WUBRG':
            if '{' + color + '}' in c.mana_cost:
                cmd_colors.add(color)

    color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
    for color in sorted(cmd_colors, key=lambda x: 'WUBRG'.index(x)):
        count = 0
        for g in games:
            has_color = False
            for t in g['turns'][:2]:
                if t['land_played']:
                    has_color = True
            if has_color:
                count += 1


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
    token_makers = [c for c in deck_cards if c.etb_token_count > 0 or c.attack_token_count > 0]
    noncreature_token_makers = [c for c in deck_cards if c.etb_clue_count > 0 or c.etb_treasure_count > 0
                                or c.etb_blood_count > 0 or c.etb_food_count > 0
                                or c.etb_powerstone_count > 0 or c.etb_map_count > 0]
    discard_outlets = [c for c in deck_cards if any(a.get('discard_cost', 0) > 0 for a in c.activated_abilities)]
    activated_cards = [c for c in deck_cards if c.activated_abilities]

    print(f"\nDetected: {len(ramp_cards)} ramp, {len(draw_cards)} draw, {len(creature_cards)} creatures, {land_count} lands")
    if token_makers:
        print(f"  Token makers: {len(token_makers)} ({', '.join(c.name for c in token_makers[:5])}{'...' if len(token_makers) > 5 else ''})")
    if noncreature_token_makers:
        print(f"  Artifact token makers (Clue/Treasure/Blood/Food/Powerstone/Map): {len(noncreature_token_makers)} ({', '.join(c.name for c in noncreature_token_makers[:5])}{'...' if len(noncreature_token_makers) > 5 else ''})"    )
    if activated_cards:
        print(f"  Activated abilities: {len(activated_cards)} ({', '.join(c.name for c in activated_cards[:5])}{'...' if len(activated_cards) > 5 else ''})")
    if discard_outlets:
        print(f"  Discard outlets: {len(discard_outlets)} ({', '.join(c.name for c in discard_outlets[:5])}{'...' if len(discard_outlets) > 5 else ''})")

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
