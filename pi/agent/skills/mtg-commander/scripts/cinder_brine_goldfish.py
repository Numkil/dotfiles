#!/usr/bin/env python3
"""
cinder_brine_goldfish.py
Tailored goldfish simulator for the Cinder & Brine / Rielle, the Everwise deck.
Archidekt: https://archidekt.com/decks/21998868/cinder_brine

Extends the generic goldfish with mechanics specific to this deck:
  - Rielle's triggered draw: whenever you discard N cards, draw N cards
  - Wheel spell modeling with proper Rielle interaction
  - Hand color composition: blue cards = Brine Seer fuel, red cards = Cinder Seer fuel
  - Cinder Seer damage potential per turn (red_in_hand × seer_activations)
  - Brine Seer counter potential per turn (blue_in_hand × seer_activations)
  - Untapper & Rings of Brighthearth interaction for activation count
  - Per-game: Rielle timing, Seer timing, wheels fired, total Rielle draws

Usage:
  # Via the shell wrapper (recommended):
  ./deck-goldfish-cinder-brine.sh 21998868
  ./deck-goldfish-cinder-brine.sh 21998868 --games 50 --turns 8 --quiet

  # Or direct from Archidekt JSON:
  curl -s https://archidekt.com/api/decks/21998868/ | python3 cinder_brine_goldfish.py

Key metrics reported:
  - Rielle cast turn (avg + distribution)
  - Cinder/Brine Seer cast turn (avg + distribution)
  - Wheels fired per game (avg)
  - Rielle draws per game (avg)
  - Hand size by turn
  - Blue/red cards in hand by turn
  - Cinder Seer damage potential by turn (when Seer is on board)
  - Brine Seer counter value by turn (when Seer is on board)
  - Mana curve, missed land drops
"""

import json
import sys
import re
import argparse
import random
import os
from dataclasses import dataclass, field
from typing import Optional, List

# Import card-parsing infrastructure from the generic goldfish sim
_skill_scripts = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _skill_scripts)
from goldfish_sim import Card, parse_deck, choose_discards, land_priority, cast_priority


# ===========================================================================
# Deck-specific detection helpers
# ===========================================================================

def _card_has_color(card: Card, color: str) -> bool:
    """Does this card have <color> in its casting cost?"""
    return '{' + color + '}' in card.mana_cost


def blue_card_count(cards: list) -> int:
    return sum(1 for c in cards if _card_has_color(c, 'U'))


def red_card_count(cards: list) -> int:
    return sum(1 for c in cards if _card_has_color(c, 'R'))


# Cards that can untap Seers (add here as deck grows)
_UNTAPPER_NAMES = frozenset({
    'cerulean wisps',
    'aphetto alchemist',
    'fatestitcher',
    'captain of the mists',
    'galvanic alchemist',
    'forensic researcher',
    'vizier of tumbling sands',
})


def _is_rielle(card: Card) -> bool:
    return 'rielle' in card.name.lower()


def _is_cinder_seer(card: Card) -> bool:
    return card.name.lower() == 'cinder seer'


def _is_brine_seer(card: Card) -> bool:
    return card.name.lower() == 'brine seer'


def _is_rings(card: Card) -> bool:
    return 'rings of brighthearth' in card.name.lower()


def _is_untapper(card: Card) -> bool:
    if card.name.lower() in _UNTAPPER_NAMES:
        return True
    # Also detect by oracle text pattern
    text = card.text.lower()
    return bool(re.search(r'\{t\}[^:]*:.*untap target (creature|permanent)', text))


def _is_wheel_spell(card: Card) -> bool:
    """
    Wheel spells: non-creature cards in the 'Wheel' category whose primary
    effect is to discard and draw (instants/sorceries/planeswalkers).

    Excludes:
    - Creatures: they enter the battlefield; any wheel ability fires through
      activated/triggered ability logic (Jace's Archivist, Magus of the Wheel)
    - Cards where 'discard' only appears in a triggered ability condition
      (e.g. "Whenever you discard...") rather than as the spell's effect
    """
    if card.is_creature:
        return False
    cats_lower = [c.lower() for c in card.categories]
    if 'wheel' not in cats_lower:
        return False
    text = card.text.lower()
    if not ('discard' in text and 'draw' in text):
        return False
    # Exclude cards where 'discard' only appears in "Whenever you discard" triggers
    # (those are draw-replacement triggers, not wheel spells)
    non_trigger_lines = [
        line for line in text.split('\n')
        if not line.startswith('whenever you discard')
        and not line.startswith('whenever one or more cards')
    ]
    return any('discard' in line for line in non_trigger_lines)


# Cards that grant "no maximum hand size" — detected by name in case oracle text
# uses class-level or leveled formatting that varies by printing.
_NO_MAX_HAND_SIZE_NAMES = frozenset({
    'thought vessel',
    'reliquary tower',
    'decanter of endless water',
    "proft's eidetic memory",
    'wizard class',
    'spellbook',
    'library of leng',
})

# Cards with Rielle-like "whenever you discard, draw" triggered abilities.
_RIELLE_LIKE_NAMES: frozenset = frozenset()  # none currently in the deck


def _is_rielle_like(card: Card) -> bool:
    """Cards that give a persistent 'draw on discard' trigger, like Rielle."""
    if card.name.lower() in _RIELLE_LIKE_NAMES:
        return True
    text = card.text.lower()
    return bool(re.search(r'whenever you discard.{0,30}draw that many', text))


def _is_battlemage_bracers(card: Card) -> bool:
    return "battlemage's bracers" in card.name.lower()


def _is_fiery_emancipation(card: Card) -> bool:
    return 'fiery emancipation' in card.name.lower()


def _is_magmakin_artillerist(card: Card) -> bool:
    return 'magmakin artillerist' in card.name.lower()


def _is_intruder_alarm(card: Card) -> bool:
    return 'intruder alarm' in card.name.lower()


# Creatures with an ETB wheel: "When ~ enters, you may discard any number of
# cards from your hand, then draw that many cards." (Battlewing Mystic)
_ETB_WHEEL_CREATURES = frozenset({
    'battlewing mystic',
})


def _is_wheel_activated_ability(line: str) -> bool:
    """
    Does this activated ability line represent a full wheel?
    e.g. Jace's Archivist: "{U}, {T}: Each player discards their hand, then draws that many cards."
    Magus of the Wheel: "{T}, Sacrifice ...: Each player discards their hand, then draws seven cards."
    """
    return 'discard' in line and ('hand' in line) and 'draw' in line


# ===========================================================================
# Extended game state
# ===========================================================================

@dataclass
class CBState:
    """Game state for the Cinder & Brine tailored goldfish."""
    library: list = field(default_factory=list)
    hand: list = field(default_factory=list)
    battlefield_lands: list = field(default_factory=list)
    battlefield_creatures: list = field(default_factory=list)
    battlefield_other: list = field(default_factory=list)
    graveyard: list = field(default_factory=list)
    commander_zone: list = field(default_factory=list)
    ramp_mana: int = 0
    total_discards: int = 0
    turn_discards: int = 0
    creatures_entered_this_turn: set = field(default_factory=set)
    tapped_creatures: set = field(default_factory=set)

    # Deck-specific board state flags
    rielle_on_board: bool = False
    cinder_seer_on_board: bool = False
    brine_seer_on_board: bool = False
    rings_on_board: bool = False
    untapper_count: int = 0         # creatures/permanents that can untap a Seer
    rielle_like_count: int = 0      # Rielle-like draw triggers on board (Battlewing Mystic etc.)
    has_no_max_hand_size: bool = False  # Thought Vessel / Reliquary Tower / etc.
    rielle_triggered_this_turn: bool = False  # Rielle fires at most once per turn

    # Damage multiplier permanents
    battlemage_bracers_on_board: bool = False
    fiery_emancipation_on_board: bool = False
    magmakin_on_board: bool = False
    intruder_alarm_on_board: bool = False

    # Cumulative tracking for this game
    rielle_draws_total: int = 0    # total extra cards drawn via Rielle/Battlewing trigger
    wheels_fired: int = 0          # times a wheel spell resolved
    artillerist_damage_total: int = 0  # cumulative Magmakin Artillerist damage (3 opponents)

    @property
    def total_mana(self) -> int:
        return len(self.battlefield_lands) + self.ramp_mana

    @property
    def all_permanents(self) -> list:
        return self.battlefield_lands + self.battlefield_creatures + self.battlefield_other

    def color_available(self, color: str) -> bool:
        for card in self.all_permanents:
            if card.produces_color(color):
                return True
        return False

    def can_cast(self, card: Card, mana_available: int) -> bool:
        if card.cmc > mana_available:
            return False
        for color in card.color_costs:
            if not self.color_available(color):
                return False
        return True

    def can_tap_creature(self, card: Card) -> bool:
        return (id(card) not in self.tapped_creatures and
                id(card) not in self.creatures_entered_this_turn)

    def tap_creature(self, card: Card):
        self.tapped_creatures.add(id(card))

    def enter_permanent(self, card: Card):
        """Put a non-land permanent onto the battlefield, updating special tracking."""
        if card.is_creature:
            self.battlefield_creatures.append(card)
            self.creatures_entered_this_turn.add(id(card))
        else:
            self.battlefield_other.append(card)
        # Update board presence flags
        if _is_rielle(card):
            self.rielle_on_board = True
        if _is_cinder_seer(card):
            self.cinder_seer_on_board = True
        if _is_brine_seer(card):
            self.brine_seer_on_board = True
        if _is_rings(card):
            self.rings_on_board = True
        if _is_untapper(card):
            self.untapper_count += 1
        if _is_rielle_like(card):
            self.rielle_like_count += 1
        if ('no maximum hand size' in card.text.lower()
                or card.name.lower() in _NO_MAX_HAND_SIZE_NAMES):
            self.has_no_max_hand_size = True
        if _is_battlemage_bracers(card):
            self.battlemage_bracers_on_board = True
        if _is_fiery_emancipation(card):
            self.fiery_emancipation_on_board = True
        if _is_magmakin_artillerist(card):
            self.magmakin_on_board = True
        if _is_intruder_alarm(card):
            self.intruder_alarm_on_board = True

    def do_discard(self, cards_to_discard: list) -> int:
        """
        Discard given cards from hand. Triggers Rielle if she's on board.
        Returns number of cards Rielle drew.
        """
        count = 0
        for c in list(cards_to_discard):
            if c in self.hand:
                self.hand.remove(c)
                self.graveyard.append(c)
                count += 1
        self.total_discards += count
        self.turn_discards += count

        # Rielle's ability: "Whenever you discard one or more cards, draw that many cards.
        # This ability triggers only once each turn."
        rielle_drew = 0
        if self.rielle_on_board and count > 0 and not self.rielle_triggered_this_turn:
            self.rielle_triggered_this_turn = True
            for _ in range(count):
                if self.library:
                    d = self.library.pop(0)
                    self.hand.append(d)
                    rielle_drew += 1
            self.rielle_draws_total += rielle_drew
        # Magmakin Artillerist: deal N damage to each of 3 opponents on discard
        if self.magmakin_on_board and count > 0:
            self.artillerist_damage_total += count * 3
        return rielle_drew

    def seer_activation_potential(self) -> tuple:
        """
        Calculate Seer activation potential for this turn's end state.

        Accounts for:
        - Base cost: {2}{R} or {2}{U} = 3 mana per activation
        - Rings of Brighthearth: copy each activation for {2} extra mana
        - Untappers: each gives one additional activation (also with Rings copies)

        Returns (cinder_acts, brine_acts, cinder_damage, brine_counter)
          cinder_damage = red_cards_in_hand × cinder_acts
          brine_counter = blue_cards_in_hand × brine_acts (opponent must pay this total)
        """
        mana = self.total_mana
        seer_cost = 3  # {2}{R} or {2}{U}

        def count_activations(seer_present: bool) -> int:
            if not seer_present or mana < seer_cost:
                return 0
            remaining = mana - seer_cost
            acts = 1
            # Rings of Brighthearth copies each activation for {2}
            if self.rings_on_board and remaining >= 2:
                copies = remaining // 2
                acts += copies
                remaining -= copies * 2
            # Each untapper gives another activation of the Seer
            for _ in range(self.untapper_count):
                if remaining >= seer_cost:
                    acts += 1
                    remaining -= seer_cost
                    if self.rings_on_board and remaining >= 2:
                        copies = remaining // 2
                        acts += copies
                        remaining -= copies * 2
            return acts

        cinder_acts = count_activations(self.cinder_seer_on_board)
        brine_acts = count_activations(self.brine_seer_on_board)
        blue = blue_card_count(self.hand)
        red = red_card_count(self.hand)

        # Apply damage multipliers
        # Battlemage's Bracers: copies each activation → ×2 damage per activation
        bracers_mult = 2 if self.battlemage_bracers_on_board else 1
        # Fiery Emancipation: triples all damage → ×3
        emancipation_mult = 3 if self.fiery_emancipation_on_board else 1
        total_mult = bracers_mult * emancipation_mult

        cinder_raw = red * cinder_acts
        return cinder_acts, brine_acts, cinder_raw, cinder_raw * total_mult, blue * brine_acts, total_mult


# ===========================================================================
# Wheel spell resolution
# ===========================================================================

_WORD_TO_NUM = {
    'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
}


def _resolve_wheel(card: Card, state: CBState) -> str:
    """
    Resolve a wheel spell with proper Rielle trigger handling.

    Two wheel types:
      Type A (discard first): "discard your/all hand, then draw that many / 7"
        - Discard hand → Rielle draws N → Wheel draws M
        - With Rielle: net hand = Rielle_drew + wheel_drew cards
      Type B (draw first): "draw N cards, then discard N cards" (Flux)
        - Draw N → Discard N → Rielle draws N
        - With Rielle: net hand = start + N

    Returns a log string.
    """
    text = card.text.lower()
    notes = []

    # Detect type B: "draw N cards, then discard N cards"
    draw_first_match = re.match(r'draw (\w+) cards?, then discard', text)
    # Also handle "each player draws N cards, then each player discards N cards"

    if draw_first_match:
        # Type B: draw first, discard second
        val = draw_first_match.group(1).lower()
        draw_n = _WORD_TO_NUM.get(val, int(val) if val.isdigit() else 3)
        drawn = 0
        for _ in range(draw_n):
            if state.library:
                state.hand.append(state.library.pop(0))
                drawn += 1
        notes.append(f"drew {drawn}")

        disc_match = re.search(r'then discard (\w+) cards?', text)
        disc_n = draw_n
        if disc_match:
            v = disc_match.group(1).lower()
            disc_n = _WORD_TO_NUM.get(v, int(v) if v.isdigit() else draw_n)
        to_discard = choose_discards(state.hand, disc_n)
        rielle_drew = state.do_discard(to_discard)
        notes.append(f"discarded {len(to_discard)}")
        if rielle_drew:
            notes.append(f"Rielle +{rielle_drew}")
    else:
        # Type A: discard hand first, then draw
        hand_size_before = len(state.hand)
        rielle_drew = state.do_discard(list(state.hand))  # discard all
        notes.append(f"discarded {hand_size_before}")
        if rielle_drew:
            notes.append(f"Rielle +{rielle_drew}")

        # Determine how many the wheel draws
        # "draw that many" → draw equal to what was discarded (before Rielle)
        if 'draw that many' in text:
            wheel_draw = hand_size_before
        else:
            # "draw seven cards" or similar
            draw_match = re.search(r'draws? (\w+) cards?', text)
            wheel_draw = 7
            if draw_match:
                v = draw_match.group(1).lower()
                wheel_draw = _WORD_TO_NUM.get(v, int(v) if v.isdigit() else 7)

        drawn = 0
        for _ in range(wheel_draw):
            if state.library:
                state.hand.append(state.library.pop(0))
                drawn += 1
        notes.append(f"drew {drawn}")

    state.wheels_fired += 1
    return f"{card.name} [wheel] ({', '.join(notes)})"


# ===========================================================================
# Main simulation
# ===========================================================================

def simulate_game(deck_cards: list, commanders: list, rng: random.Random,
                  num_turns: int) -> dict:
    """Simulate one goldfish game. Returns a game log dict."""

    library = deck_cards.copy()
    rng.shuffle(library)

    hand = library[:7]
    library = library[7:]

    # Mulligan: keep if 2–5 lands
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

    state = CBState(
        library=library,
        hand=list(hand),
        commander_zone=list(commanders),
    )

    game_log = {
        'mulligans': mulligan_count,
        'opening_hand': [c.name for c in hand],
        'opening_lands': sum(1 for c in hand if c.is_land),
        'turns': [],
        'commander_cast_turn': None,     # Rielle
        'cinder_seer_cast_turn': None,
        'brine_seer_cast_turn': None,
    }

    for turn in range(1, num_turns + 1):
        state.turn_discards = 0
        state.creatures_entered_this_turn = set()
        state.tapped_creatures = set()
        state.rielle_triggered_this_turn = False  # reset once-per-turn gate

        turn_log = {
            'turn': turn,
            'drawn': None,
            'land_played': None,
            'spells': [],
            'mana_after': 0,
            'hand_size': 0,
            'lands_on_field': 0,
            'blue_in_hand': 0,
            'red_in_hand': 0,
            'cinder_acts': 0,
            'brine_acts': 0,
            'cinder_damage_potential': 0,
            'cinder_damage_multiplied': 0,
            'damage_multiplier': 1,
            'brine_counter_potential': 0,
            'wheels_fired': 0,
            'rielle_draws': 0,
        }

        # =================================================================
        # UPKEEP — check for upkeep triggers on permanents
        # =================================================================
        for perm in state.battlefield_creatures + state.battlefield_other:
            text_lower = perm.text.lower()
            if 'beginning of your upkeep' not in text_lower:
                continue
            # Magus of the Jar style: discard hand, draw that many at upkeep
            if re.search(r'discard all.{0,20}(cards.{0,20}hand|hand)', text_lower) and 'draw that many' in text_lower:
                h = len(state.hand)
                rielle_drew = state.do_discard(list(state.hand))
                drawn = 0
                for _ in range(h):
                    if state.library:
                        state.hand.append(state.library.pop(0))
                        drawn += 1
                note = f"Upkeep: {perm.name} -> discarded {h}, drew {drawn}"
                if rielle_drew:
                    note += f", Rielle +{rielle_drew}"
                turn_log['spells'].append(note)
                state.wheels_fired += 1

        # =================================================================
        # DRAW PHASE
        # =================================================================
        if turn > 1 and state.library:
            drawn_card = state.library.pop(0)
            state.hand.append(drawn_card)
            turn_log['drawn'] = drawn_card.name

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
            # Check if this land grants no maximum hand size (Reliquary Tower)
            if ('no maximum hand size' in chosen.text.lower()
                    or chosen.name.lower() in _NO_MAX_HAND_SIZE_NAMES):
                state.has_no_max_hand_size = True

        mana_left = state.total_mana

        # =================================================================
        # CAST COMMANDER FIRST (Rielle, the Everwise)
        # Rielle is 3 CMC — cast her as soon as we can so her trigger is active
        # =================================================================
        for cmdr in list(state.commander_zone):
            if mana_left >= cmdr.cmc and state.can_cast(cmdr, mana_left):
                state.commander_zone.remove(cmdr)
                state.enter_permanent(cmdr)
                mana_left -= cmdr.cmc
                game_log['commander_cast_turn'] = turn
                turn_log['spells'].append(f"{cmdr.name} [commander — cast-first]")

        # =================================================================
        # CAST SPELLS FROM HAND
        # =================================================================
        max_iter = 25
        for _ in range(max_iter):
            # Build castable list (exclude lands and sac-draw with no valid sac targets)
            castable = [
                c for c in state.hand
                if not c.is_land
                and c.cmc <= mana_left
                and state.can_cast(c, mana_left)
                and not (c.needs_sac_creature and not state.battlefield_creatures)
                and not (c.needs_sac_land and len(state.battlefield_lands) <= 1)
                and not (c.needs_creature_target and not state.battlefield_creatures)
            ]
            if not castable:
                break

            castable.sort(key=lambda c: cast_priority(c, turn))
            card = castable[0]
            state.hand.remove(card)
            mana_left -= card.cmc
            note = card.name

            # --- Wheel spells: special handling ---
            if _is_wheel_spell(card):
                rielle_draws_before = state.rielle_draws_total
                wheels_before = state.wheels_fired
                note = _resolve_wheel(card, state)
                turn_log['rielle_draws'] += state.rielle_draws_total - rielle_draws_before
                turn_log['wheels_fired'] += state.wheels_fired - wheels_before
                turn_log['spells'].append(note)
                # Wheels put card into graveyard
                state.graveyard.append(card)
                # mana_left is already correct (decremented by card.cmc before this branch).
                # Just continue the loop — the fresh hand may have castable spells
                # within the remaining mana budget.
                continue

            # --- Ramp: land search ---
            if card.is_land_ramp:
                for _ in range(card.lands_to_field):
                    # Create a generic dual-ish land (fetches the color we need)
                    fetched = Card(
                        name="(fetched land)", cmc=0, types=['Land'],
                        supertypes=['Basic'], subtypes=[],
                        text="", mana_cost="",
                        mana_production={'U': 1, 'R': 1},
                        keywords=[], categories=['Land'],
                    )
                    state.battlefield_lands.append(fetched)
                for _ in range(card.lands_to_hand):
                    fetched = Card(
                        name="(fetched land)", cmc=0, types=['Land'],
                        supertypes=['Basic'], subtypes=[],
                        text="", mana_cost="",
                        mana_production={'U': 1, 'R': 1},
                        keywords=[], categories=['Land'],
                    )
                    state.hand.append(fetched)
                note = f"{card.name} -> {card.lands_to_field} land(s) to field"
                if card.needs_sac_land and state.battlefield_lands:
                    sacced = state.battlefield_lands.pop()
                    state.graveyard.append(sacced)
                    note += f" (sac {sacced.name})"
                state.graveyard.append(card)

            # --- Mana rocks / dorks ---
            elif card.is_mana_rock or card.is_mana_dork:
                state.ramp_mana += card.extra_mana
                state.enter_permanent(card)
                note = f"{card.name} (+{card.extra_mana} mana)"

            # --- Non-sac draw spells ---
            elif card.is_draw and not card.is_sac_draw:
                drawn_cards = []
                for _ in range(card.draw_count):
                    if state.library:
                        d = state.library.pop(0)
                        state.hand.append(d)
                        drawn_cards.append(d.name)

                # Handle discard portion (rummage/loot effects)
                if card.discard_count > 0:
                    to_discard = choose_discards(state.hand, card.discard_count)
                    rielle_drew = state.do_discard(to_discard)
                    discarded_names = [c.name for c in to_discard if c in state.graveyard[-len(to_discard):]]
                    note = f"{card.name} -> drew {len(drawn_cards)}, discarded {card.discard_count}"
                    if rielle_drew:
                        note += f", Rielle +{rielle_drew}"
                        turn_log['rielle_draws'] += rielle_drew
                    # Frantic Search: untap lands
                    if 'untap' in card.text.lower() and 'land' in card.text.lower():
                        untap_match = re.search(r'untap up to (\w+) lands?', card.text.lower())
                        if untap_match:
                            val = untap_match.group(1).lower()
                            n = _WORD_TO_NUM.get(val, int(val) if val.isdigit() else 2)
                            mana_left += n
                            note += f", untap {n} lands"
                else:
                    note = f"{card.name} -> drew {len(drawn_cards)}"

                state.graveyard.append(card)

            # --- Sac-draw ---
            elif card.is_sac_draw:
                if state.battlefield_creatures:
                    sacced = state.battlefield_creatures.pop(0)
                    state.graveyard.append(sacced)
                    drawn_cards = []
                    for _ in range(card.draw_count):
                        if state.library:
                            d = state.library.pop(0)
                            state.hand.append(d)
                            drawn_cards.append(d.name)
                    note = f"{card.name} (sac {sacced.name}) -> drew {len(drawn_cards)}"
                state.graveyard.append(card)

            # --- Creatures ---
            elif card.is_creature:
                state.enter_permanent(card)
                # Update game_log for Seer timing
                if _is_cinder_seer(card) and game_log['cinder_seer_cast_turn'] is None:
                    game_log['cinder_seer_cast_turn'] = turn
                    note = f"{card.name} [Cinder Seer — ONLINE]"
                elif _is_brine_seer(card) and game_log['brine_seer_cast_turn'] is None:
                    game_log['brine_seer_cast_turn'] = turn
                    note = f"{card.name} [Brine Seer — ONLINE]"

                # ETB wheel creatures (Battlewing Mystic): discard hand, draw that many
                # Always fires — in this deck you always want to discard into Rielle
                if card.name.lower() in _ETB_WHEEL_CREATURES and len(state.hand) > 0:
                    rielle_before = state.rielle_draws_total
                    h = len(state.hand)
                    rd = state.do_discard(list(state.hand))
                    drawn_etb = 0
                    for _x in range(h):
                        if state.library:
                            state.hand.append(state.library.pop(0))
                            drawn_etb += 1
                    state.wheels_fired += 1
                    rielle_drew = state.rielle_draws_total - rielle_before
                    note = f"{card.name} [ETB wheel] discarded {h}, drew {drawn_etb}"
                    if rielle_drew:
                        note += f", Rielle +{rielle_drew}"
                        turn_log['rielle_draws'] += rielle_drew
                    turn_log['wheels_fired'] = state.wheels_fired

            # --- Other permanents (artifacts, enchantments) ---
            elif card.is_artifact or card.is_enchantment or card.is_planeswalker:
                state.enter_permanent(card)

            # --- Instants and sorceries ---
            else:
                state.graveyard.append(card)
                # Handle discard effects on burn/utility spells
                if card.discard_count > 0:
                    to_discard = choose_discards(state.hand, card.discard_count)
                    rielle_drew = state.do_discard(to_discard)
                    if rielle_drew:
                        note += f" [Rielle +{rielle_drew}]"
                        turn_log['rielle_draws'] += rielle_drew

            turn_log['spells'].append(note)

        # =================================================================
        # ACTIVATED ABILITIES — wheel abilities (Jace's Archivist etc.)
        # then draw abilities; one activation per permanent per turn
        # =================================================================
        max_ab_iter = 8
        used_perms = set()  # track which permanents already activated this turn
        for _ in range(max_ab_iter):
            used_ability = False
            for perm in state.battlefield_creatures + state.battlefield_other:
                if id(perm) in used_perms:
                    continue
                for ability in perm.activated_abilities:
                    if ability['mana_cost'] > mana_left:
                        continue
                    ok = all(state.color_available(col)
                             for col in ability.get('color_requirements', {}))
                    if not ok:
                        continue
                    if ability['needs_tap']:
                        if perm.is_creature and not state.can_tap_creature(perm):
                            continue

                    # ---- Wheel activated abilities (Jace's Archivist, Magus of Wheel) ----
                    if _is_wheel_activated_ability(ability['line']):
                        mana_left -= ability['mana_cost']
                        if ability['needs_tap'] and perm.is_creature:
                            state.tap_creature(perm)
                        if ability['needs_tap'] and not perm.is_creature:
                            perm.activated_abilities = [
                                a for a in perm.activated_abilities if a is not ability
                            ]
                        # "sacrifice" clause — remove the permanent if it sacrifices itself
                        if 'sacrifice' in ability['line'] and 'sacrifice ' + perm.name.lower() in ability['line']:
                            if perm in state.battlefield_creatures:
                                state.battlefield_creatures.remove(perm)
                            elif perm in state.battlefield_other:
                                state.battlefield_other.remove(perm)
                            state.graveyard.append(perm)

                        rielle_before = state.rielle_draws_total
                        # Resolve as a wheel (discard hand first, Rielle trigger, draw 7 or equal)
                        _text = ability['line'].lower()
                        h = len(state.hand)
                        rd = state.do_discard(list(state.hand))
                        if 'draw that many' in _text:
                            draw_n = h
                        else:
                            draw_n = 7
                        drawn_wheel = 0
                        for _x in range(draw_n):
                            if state.library:
                                state.hand.append(state.library.pop(0))
                                drawn_wheel += 1
                        state.wheels_fired += 1
                        rielle_drew = state.rielle_draws_total - rielle_before
                        note = f"[wheel ability] {perm.name} -> discarded {h}, drew {drawn_wheel}"
                        if rielle_drew:
                            note += f", Rielle +{rielle_drew}"
                            turn_log['rielle_draws'] += rielle_drew
                        turn_log['spells'].append(note)
                        turn_log['wheels_fired'] = state.wheels_fired
                        used_perms.add(id(perm))
                        used_ability = True
                        break

                    # ---- Normal draw abilities ----
                    if ability['type'] != 'draw':
                        continue
                    if ability['discard_cost'] > 0:
                        if len(state.hand) < ability['discard_cost'] + 1:
                            continue

                    mana_left -= ability['mana_cost']
                    if ability['needs_tap'] and perm.is_creature:
                        state.tap_creature(perm)
                    if ability['needs_tap'] and not perm.is_creature:
                        perm.activated_abilities = [
                            a for a in perm.activated_abilities if a is not ability
                        ]
                    if ability['discard_cost'] > 0:
                        to_disc = choose_discards(state.hand, ability['discard_cost'])
                        rielle_drew = state.do_discard(to_disc)
                        turn_log['rielle_draws'] += rielle_drew

                    draw_n = ability.get('draw_count', 1)
                    drawn = []
                    for _x in range(draw_n):
                        if state.library:
                            d = state.library.pop(0)
                            state.hand.append(d)
                            drawn.append(d.name)
                    turn_log['spells'].append(
                        f"[ability] {perm.name} -> drew {len(drawn)}"
                    )
                    used_perms.add(id(perm))
                    used_ability = True
                    break
                if used_ability:
                    break
            if not used_ability:
                break

        # =================================================================
        # CLEANUP — discard down to maximum hand size (default 7)
        #
        # With no-max-hand-size (Thought Vessel / Reliquary Tower / etc.): skip.
        # Without: discard excess → Rielle draws back → loop until library empty.
        # Rielle triggers once per turn, so cleanup can only draw once via Rielle.
        #
        # Discard priority: prefer lands over colored spells.
        # Colored cards = Seer fuel; lands are less valuable in hand mid-game.
        # =================================================================
        def _cleanup_choose_discards(hand, count):
            """For end-of-turn cleanup: discard lands first, then non-blue/red, then high CMC."""
            if len(hand) <= count:
                return list(hand)
            def score(c):
                if c.is_land:
                    return 3   # discard lands first in cleanup (not Seer fuel)
                if not (_card_has_color(c, 'U') or _card_has_color(c, 'R')):
                    return 2   # discard colorless/off-color next
                return 1       # keep blue and red cards (Seer fuel)
            return sorted(hand, key=lambda c: -score(c))[:count]

        if not state.has_no_max_hand_size:
            MAX_HAND = 7
            cleanup_discards = 0
            cleanup_rielle = 0
            loop_limit = len(state.library) + len(state.hand) + 2
            for _ in range(loop_limit):
                if len(state.hand) <= MAX_HAND:
                    break
                if not state.library and not state.rielle_on_board:
                    break
                excess = len(state.hand) - MAX_HAND
                to_discard = _cleanup_choose_discards(state.hand, excess)
                rielle_before = state.rielle_draws_total
                state.do_discard(to_discard)
                cleanup_discards += excess
                drew = state.rielle_draws_total - rielle_before
                cleanup_rielle += drew
                if drew == 0:
                    break
            if cleanup_discards:
                note_parts = [f"discard {cleanup_discards} to hand limit"]
                if cleanup_rielle:
                    note_parts.append(f"Rielle +{cleanup_rielle}")
                turn_log['spells'].append(f"[cleanup] {', '.join(note_parts)}")
                turn_log['rielle_draws'] += cleanup_rielle

        # =================================================================
        # END-OF-TURN METRICS — Seer activation potential
        # =================================================================
        cinder_acts, brine_acts, cinder_dmg, cinder_dmg_final, brine_ctr, dmg_mult = state.seer_activation_potential()

        turn_log['mana_after'] = state.total_mana
        turn_log['hand_size'] = len(state.hand)
        turn_log['lands_on_field'] = len(state.battlefield_lands)
        turn_log['blue_in_hand'] = blue_card_count(state.hand)
        turn_log['red_in_hand'] = red_card_count(state.hand)
        turn_log['cinder_acts'] = cinder_acts
        turn_log['brine_acts'] = brine_acts
        turn_log['cinder_damage_potential'] = cinder_dmg
        turn_log['cinder_damage_multiplied'] = cinder_dmg_final
        turn_log['damage_multiplier'] = dmg_mult
        turn_log['brine_counter_potential'] = brine_ctr
        turn_log['wheels_fired'] = state.wheels_fired  # cumulative
        turn_log['rielle_on_board'] = state.rielle_on_board
        turn_log['cinder_seer_on_board'] = state.cinder_seer_on_board
        turn_log['brine_seer_on_board'] = state.brine_seer_on_board
        turn_log['bracers_on_board'] = state.battlemage_bracers_on_board
        turn_log['emancipation_on_board'] = state.fiery_emancipation_on_board
        turn_log['magmakin_on_board'] = state.magmakin_on_board

        game_log['turns'].append(turn_log)

    # Final state summary
    game_log['final_mana'] = state.total_mana
    game_log['final_hand'] = len(state.hand)
    game_log['final_lands'] = len(state.battlefield_lands)
    game_log['final_rielle_draws'] = state.rielle_draws_total
    game_log['final_wheels'] = state.wheels_fired
    game_log['final_artillerist_damage'] = state.artillerist_damage_total
    game_log['board_creatures'] = [c.name for c in state.battlefield_creatures]
    game_log['board_other'] = [c.name for c in state.battlefield_other]

    return game_log


# ===========================================================================
# Output
# ===========================================================================

def print_game(game: dict, game_num: int):
    mul = f"  (mulligan to {7 - game['mulligans']})" if game['mulligans'] else ""
    print(f"\n{'=' * 65}")
    print(f"GAME {game_num}{mul}")
    hand_str = ", ".join(game['opening_hand'])
    print(f"Hand ({game['opening_lands']} lands): {hand_str}")

    for t in game['turns']:
        draw_str = f"Draw: {t['drawn']}" if t['drawn'] else "(no draw)"
        print(f"\n  Turn {t['turn']}: {draw_str}")

        if t['land_played']:
            print(f"    Land: {t['land_played']}")
        else:
            print(f"    *** MISSED LAND DROP ***")

        for s in t['spells']:
            print(f"    Cast: {s}")

        # Seer status
        seer_parts = []
        if t['cinder_seer_on_board']:
            mult = t.get('damage_multiplier', 1)
            raw = t['cinder_damage_potential']
            final = t['cinder_damage_multiplied']
            mult_str = f" ×{mult}={final}" if mult > 1 else f"={raw}"
            buffs = []
            if t.get('bracers_on_board'):
                buffs.append('Bracers')
            if t.get('emancipation_on_board'):
                buffs.append('Emancipation')
            buff_str = f" [{'+'.join(buffs)}]" if buffs else ""
            seer_parts.append(f"Cinder({t['cinder_acts']} acts, {t['red_in_hand']}R in hand → {raw}{mult_str} dmg{buff_str})")
        if t['brine_seer_on_board']:
            seer_parts.append(f"Brine({t['brine_acts']} acts → {t['brine_counter_potential']} ctr)")

        ramp_extra = t['mana_after'] - t['lands_on_field']
        ramp_str = f" +{ramp_extra} ramp" if ramp_extra else ""
        rielle_str = f", Rielle: {t['rielle_draws']} draws this turn" if t.get('rielle_draws') else ""
        seer_str = f"  | {', '.join(seer_parts)}" if seer_parts else ""
        hand_colors = f"(hand: {t['blue_in_hand']}U {t['red_in_hand']}R, {t['hand_size']} cards)"

        print(f"    → {t['mana_after']} mana ({t['lands_on_field']} lands{ramp_str}){rielle_str}")
        print(f"    → {hand_colors}{seer_str}")

    print(f"\n  === End state ===")
    board = game['board_creatures'] + game['board_other']
    print(f"  Board:  {', '.join(board) if board else '(empty)'}")
    print(f"  Mana:   {game['final_mana']} ({game['final_lands']} lands)")
    print(f"  Hand:   {game['final_hand']} cards")
    rielle_t = game.get('commander_cast_turn')
    cinder_t = game.get('cinder_seer_cast_turn')
    brine_t  = game.get('brine_seer_cast_turn')
    print(f"  Rielle: {'T' + str(rielle_t) if rielle_t else 'NOT CAST'}")
    print(f"  Cinder: {'T' + str(cinder_t) if cinder_t else 'not cast'}")
    print(f"  Brine:  {'T' + str(brine_t) if brine_t else 'not cast'}")
    print(f"  Wheels: {game['final_wheels']}  |  Rielle draws: {game['final_rielle_draws']}")


def print_aggregate(games: list, num_turns: int, commanders: list):
    n = len(games)
    print(f"\n{'=' * 65}")
    print(f"AGGREGATE ANALYSIS  ({n} games, {num_turns} turns each)")
    if commanders:
        print(f"Commander: {', '.join(c.name for c in commanders)}")
    print(f"{'=' * 65}")

    # Mulligans
    mull_n = sum(1 for g in games if g['mulligans'] > 0)
    print(f"\nMulligans: {mull_n}/{n} games ({100*mull_n//n}%)")

    # Missed land drops
    any_miss = False
    for t in range(1, num_turns + 1):
        missed = sum(1 for g in games if not g['turns'][t-1]['land_played'])
        if missed:
            if not any_miss:
                print(f"\nMissed land drops:")
                any_miss = True
            print(f"  Turn {t}: {missed}/{n} ({100*missed//n}%)")
    if not any_miss:
        print(f"\nMissed land drops: none!")

    # Mana progression
    print(f"\nMana available (end of turn):")
    for t in range(1, num_turns + 1):
        manas = [g['turns'][t-1]['mana_after'] for g in games]
        avg = sum(manas) / n
        print(f"  T{t}: avg {avg:.1f}  (min {min(manas)}, max {max(manas)})")

    # Commander timing
    rielle_turns = [g['commander_cast_turn'] for g in games if g['commander_cast_turn']]
    print(f"\n--- RIELLE, THE EVERWISE ---")
    if rielle_turns:
        print(f"Cast in {len(rielle_turns)}/{n} games ({100*len(rielle_turns)//n}%)")
        print(f"Average cast turn: {sum(rielle_turns)/len(rielle_turns):.1f}")
        for cutoff in [3, 4, 5, 6]:
            by = sum(1 for t in rielle_turns if t <= cutoff)
            print(f"  By turn {cutoff}: {by}/{n} ({100*by//n}%)")
    else:
        print(f"Never cast in {num_turns} turns.")

    # Cinder Seer timing
    cinder_turns = [g['cinder_seer_cast_turn'] for g in games if g['cinder_seer_cast_turn']]
    print(f"\n--- CINDER SEER ---")
    if cinder_turns:
        print(f"Cast in {len(cinder_turns)}/{n} games ({100*len(cinder_turns)//n}%)")
        print(f"Average cast turn: {sum(cinder_turns)/len(cinder_turns):.1f}")
        for cutoff in [4, 5, 6, 7]:
            by = sum(1 for t in cinder_turns if t <= cutoff)
            print(f"  By turn {cutoff}: {by}/{n} ({100*by//n}%)")
    else:
        print(f"Never cast in {num_turns} turns.")

    # Brine Seer timing
    brine_turns = [g['brine_seer_cast_turn'] for g in games if g['brine_seer_cast_turn']]
    print(f"\n--- BRINE SEER ---")
    if brine_turns:
        print(f"Cast in {len(brine_turns)}/{n} games ({100*len(brine_turns)//n}%)")
        print(f"Average cast turn: {sum(brine_turns)/len(brine_turns):.1f}")
        for cutoff in [4, 5, 6, 7]:
            by = sum(1 for t in brine_turns if t <= cutoff)
            print(f"  By turn {cutoff}: {by}/{n} ({100*by//n}%)")
    else:
        print(f"Never cast in {num_turns} turns.")

    # Wheel stats
    print(f"\n--- WHEEL ENGINE ---")
    total_wheels = [g['final_wheels'] for g in games]
    avg_wheels = sum(total_wheels) / n
    print(f"Wheels per game: avg {avg_wheels:.1f}  (min {min(total_wheels)}, max {max(total_wheels)})")
    games_0_wheels = sum(1 for w in total_wheels if w == 0)
    print(f"Games with 0 wheels: {games_0_wheels}/{n}")

    # Rielle draw stats
    rielle_draws = [g['final_rielle_draws'] for g in games]
    avg_rd = sum(rielle_draws) / n
    print(f"\nRielle draws per game: avg {avg_rd:.1f}  (min {min(rielle_draws)}, max {max(rielle_draws)})")
    games_no_rd = sum(1 for d in rielle_draws if d == 0)
    print(f"Games where Rielle drew 0 cards: {games_no_rd}/{n}")

    # Hand size by turn
    print(f"\n--- HAND COMPOSITION (end of turn avg) ---")
    print(f"{'Turn':<6} {'Hand':>6} {'Blue(U)':>8} {'Red(R)':>8} {'Blue%':>7} {'Red%':>7}")
    for t in range(1, num_turns + 1):
        hands = [g['turns'][t-1]['hand_size'] for g in games]
        blues = [g['turns'][t-1]['blue_in_hand'] for g in games]
        reds  = [g['turns'][t-1]['red_in_hand'] for g in games]
        avg_h = sum(hands) / n
        avg_b = sum(blues) / n
        avg_r = sum(reds) / n
        pct_b = (avg_b / avg_h * 100) if avg_h > 0 else 0
        pct_r = (avg_r / avg_h * 100) if avg_h > 0 else 0
        print(f"  T{t:<4} {avg_h:>6.1f} {avg_b:>8.1f} {avg_r:>8.1f} {pct_b:>6.0f}% {pct_r:>6.0f}%")

    # Seer potential by turn
    print(f"\n--- CINDER SEER DAMAGE POTENTIAL (when on board) ---")
    print(f"  Raw = red_in_hand × activations | Multiplied = raw × Bracers(×2) × Emancipation(×3)")
    for t in range(1, num_turns + 1):
        seer_games = [g for g in games if g['turns'][t-1]['cinder_seer_on_board']]
        if not seer_games:
            continue
        acts  = [g['turns'][t-1]['cinder_acts'] for g in seer_games]
        dmg   = [g['turns'][t-1]['cinder_damage_potential'] for g in seer_games]
        dmg_m = [g['turns'][t-1]['cinder_damage_multiplied'] for g in seer_games]
        red_h = [g['turns'][t-1]['red_in_hand'] for g in seer_games]
        mults = [g['turns'][t-1]['damage_multiplier'] for g in seer_games]
        max_mult = max(mults)
        mult_note = f" [max mult ×{max_mult}]" if max_mult > 1 else ""
        print(f"  T{t}: {len(seer_games)}/{n} games | "
              f"avg acts={sum(acts)/len(acts):.1f}, "
              f"avg {sum(red_h)/len(red_h):.1f}R in hand → "
              f"raw {sum(dmg)/len(dmg):.1f} (max {max(dmg)}) | "
              f"multiplied {sum(dmg_m)/len(dmg_m):.1f} (max {max(dmg_m)}){mult_note}")

    print(f"\n--- BRINE SEER COUNTER POTENTIAL (when on board) ---")
    for t in range(1, num_turns + 1):
        seer_games = [g for g in games if g['turns'][t-1]['brine_seer_on_board']]
        if not seer_games:
            continue
        acts = [g['turns'][t-1]['brine_acts'] for g in seer_games]
        ctr  = [g['turns'][t-1]['brine_counter_potential'] for g in seer_games]
        blue_h = [g['turns'][t-1]['blue_in_hand'] for g in seer_games]
        print(f"  T{t}: {len(seer_games)}/{n} games have Seer | "
              f"avg acts={sum(acts)/len(acts):.1f}, "
              f"avg blue_in_hand={sum(blue_h)/len(blue_h):.1f}, "
              f"avg ctr_value={sum(ctr)/len(ctr):.1f}  (max {max(ctr)})")

    # Magmakin Artillerist damage
    art_dmg = [g['final_artillerist_damage'] for g in games]
    if any(d > 0 for d in art_dmg):
        print(f"\n--- MAGMAKIN ARTILLERIST (total damage across 3 opponents) ---")
        avg_art = sum(art_dmg) / n
        print(f"  Avg per game: {avg_art:.1f}  (min {min(art_dmg)}, max {max(art_dmg)})")
        games_with_art = sum(1 for d in art_dmg if d > 0)
        print(f"  Games where Artillerist dealt damage: {games_with_art}/{n}")
        print(f"  Note: does not include Fiery Emancipation multiplier (add ×3 if on board)")

    print(f"\n{'=' * 65}")


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Cinder & Brine tailored goldfish simulator'
    )
    parser.add_argument('--games', type=int, default=20,
                        help='Number of games to simulate (default: 20)')
    parser.add_argument('--turns', type=int, default=8,
                        help='Turns per game (default: 8)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--quiet', action='store_true',
                        help='Skip per-game logs, only show aggregate stats')
    args = parser.parse_args()

    data = json.load(sys.stdin)
    deck_name, deck_cards, commanders = parse_deck(data)

    land_count = sum(1 for c in deck_cards if c.is_land)
    total = len(deck_cards) + len(commanders)

    print(f"{'=' * 65}")
    print(f"CINDER & BRINE — TAILORED GOLDFISH SIMULATOR")
    print(f"{'=' * 65}")
    print(f"Deck:        {deck_name}")
    if commanders:
        print(f"Commander:   {', '.join(c.name for c in commanders)}")
    print(f"Cards:       {total} ({land_count} lands, {total - land_count - len(commanders)} nonland spells)")
    print(f"Games:       {args.games}")
    print(f"Turns:       {args.turns}")

    # Detect relevant cards for info summary
    wheel_cards = [c for c in deck_cards if _is_wheel_spell(c)]
    seer_cards  = [c for c in deck_cards if _is_cinder_seer(c) or _is_brine_seer(c)]
    ramp_cards  = [c for c in deck_cards if c.is_ramp]
    draw_cards  = [c for c in deck_cards if c.is_draw]
    untappers   = [c for c in deck_cards if _is_untapper(c)]
    rings_cards = [c for c in deck_cards if _is_rings(c)]

    print(f"\nDetected in deck:")
    etb_wheel_cards = [c for c in deck_cards if c.name.lower() in _ETB_WHEEL_CREATURES]
    print(f"  Wheel spells ({len(wheel_cards)}): {', '.join(c.name for c in wheel_cards)}")
    if etb_wheel_cards:
        print(f"  ETB wheel creatures ({len(etb_wheel_cards)}): {', '.join(c.name for c in etb_wheel_cards)}")
    print(f"  Seers ({len(seer_cards)}): {', '.join(c.name for c in seer_cards)}")
    print(f"  Ramp ({len(ramp_cards)}): {', '.join(c.name for c in ramp_cards[:8])}{'...' if len(ramp_cards) > 8 else ''}")
    if untappers:
        print(f"  Untappers ({len(untappers)}): {', '.join(c.name for c in untappers)}")
    if rings_cards:
        print(f"  Rings of Brighthearth: YES")
    print(f"{'=' * 65}")

    if args.seed is not None:
        base_seed = args.seed
    else:
        base_seed = random.randint(0, 999999)
        print(f"Random seed: {base_seed}  (use --seed {base_seed} to reproduce)")

    games = []
    for i in range(args.games):
        rng = random.Random(base_seed + i * 7919)
        game = simulate_game(deck_cards, commanders, rng, args.turns)
        games.append(game)

    if not args.quiet:
        for i, game in enumerate(games):
            print_game(game, i + 1)

    print_aggregate(games, args.turns, commanders)


if __name__ == '__main__':
    main()
