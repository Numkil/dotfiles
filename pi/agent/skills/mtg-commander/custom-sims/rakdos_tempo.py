#!/usr/bin/env python3
"""
Monte Carlo goldfish sim for the Rakdos (mono-B) Pauper tempo deck.
Archidekt: https://archidekt.com/decks/23531288/rakdos_tempo

Core engine (oracle text verified via Scryfall, 2026-06):
  - Fear of Lost Teeth  (B, 1/1)  : dies -> 1 dmg any target + gain 1 life
  - Footlight Fiend     (B, 1/1)  : dies -> 1 dmg any target
  - Cuombajj Witches    (BB,1/3)  : {T}: 1 dmg any target (+1 dmg opp's choice)
  - Raven of Fell Omens (1B,1/2 fly): when you COMMIT A CRIME -> each opp loses 1, you gain 1 (once/turn)
  - You Are Already Dead(B inst)  : destroy a creature dealt damage this turn; draw
  - Village Rites / Corrupted Conviction (B inst): sac a creature, draw 2  (sac outlets)
  - Soul Reap (1B sorc): destroy target nongreen creature (-3 life if 2nd black spell)
  - Jarl of the Forsaken (3B / foretell 1B, flash 3/2): ETB destroy a DAMAGED opp creature
  - Jagged Barrens (tapland): ETB deal 1 to target OPPONENT (a crime, hits face not a creature)

A "crime" = targeting an opponent, their permanents, or cards in their graveyard.

THREE METRICS measured per turn (capability, i.e. "could we do it this turn"):
  1. ENGINE ONLINE   : a Raven in play AND we can commit >=1 crime this turn.
  2. FULL VALUE LOOP  : Raven in play AND a sac outlet in hand AND a Fear/Footlight
                        on board (sac -> death-ping crime + draw 2).
  3. YAAD LIVE        : You Are Already Dead in hand AND we can damage an opp creature
                        this turn (Cuombajj tap or death-ping) AND have mana to also cast YAAD.

Opponent model: deploys ~1 creature per turn ("creature on curve"), so removal /
YAAD / Jarl have a realistic target most turns.

Mana model tracks total + black; nonbasics enter TAPPED. Rakdos Carnarium = bounce land
(enters tapped, returns a land, then taps for 2). Tapped lands are unavailable the turn played.

Heuristics are intentionally transparent; see play_turn(). Run with --verbose N to trace games.
"""

import argparse
import random
from collections import defaultdict

# ---------------------------------------------------------------------------
# Card definitions. cmc/black = casting needs; 'roles' drives sim logic.
# ---------------------------------------------------------------------------
# Land identifiers
SWAMP, BARREN_MOOR, JAGGED_BARRENS, CARNARIUM = "Swamp", "Barren Moor", "Jagged Barrens", "Rakdos Carnarium"
LANDS = {SWAMP, BARREN_MOOR, JAGGED_BARRENS, CARNARIUM}
TAPLANDS = {BARREN_MOOR, JAGGED_BARRENS, CARNARIUM}

# Spell roles
FEAR = "Fear of Lost Teeth"          # death-ping creature (sac fodder)
FOOTLIGHT = "Footlight Fiend"        # death-ping creature (sac fodder)
CUOMBAJJ = "Cuombajj Witches"        # tap-ping creature (repeatable crime/dmg), BB
RAVEN = "Raven of Fell Omens"        # payoff
CORRUPTED = "Corrupted Conviction"   # sac outlet, draw 2
VILLAGE = "Village Rites"            # sac outlet, draw 2
THORN = "Thorn of the Black Rose"    # 4-drop monarch
BLADE = "Blade Juggler"              # 5 / spectacle 3, ETB draw
SIGN = "Sign in Blood"               # BB sorcery, draw 2 lose 2 (no body)
VAULT = "Vault Plunderer"            # 2B, 3/1, ETB draw 1 lose 1 (reliable flat-3 body)
FAKE = "Fake Your Own Death"         # 1B instant: +2/0 + "dies -> return tapped + Treasure" (no body)
CRYPT = "Crypt Rats"                 # 2B 1/1, {X}: X to each creature+player (symmetric sweeper)
CHAOS = "Chaos Spewer"               # 2{B/R}=3 5/4 (casts off black); ETB pay 2 or blight 2
CUTTHROAT = "Cindering Cutthroat"    # 2{B/R}=3; 4/3 if an opp lost life this turn else 3/2; menace for 1
MOURNERS = "Mourner's Surprise"      # 2-drop regrowth + token
PERIGEE = "Perigee Beckoner"         # 5 / warp 2
SCARBLADE = "Scarblade's Malice"     # combat trick (targets own creature -> NOT a crime)
YAAD = "You Are Already Dead"        # destroy damaged creature + draw
SOUL_REAP = "Soul Reap"              # removal (crime vs opp creature)
JARL = "Jarl of the Forsaken"        # flash, destroy damaged opp creature

DEATH_PINGERS = {FEAR, FOOTLIGHT}    # creatures whose death deals dmg (sac -> crime + dmg)
SAC_OUTLETS = {CORRUPTED, VILLAGE}

# CMC / black-pip requirement for casting (effective cheapest mode used by sim)
COST = {
    FEAR: (1, 1), FOOTLIGHT: (1, 1), CUOMBAJJ: (2, 2), RAVEN: (2, 1),
    CORRUPTED: (1, 1), VILLAGE: (1, 1), THORN: (4, 1), MOURNERS: (2, 1),
    SCARBLADE: (1, 1), YAAD: (1, 1), SOUL_REAP: (2, 1), JARL: (4, 1),
    # Perigee via Warp 1B = (2,1); Blade via Spectacle 2B = (3,1) when opp lost life, else (5,1)
    PERIGEE: (2, 1), BLADE: (5, 1), SIGN: (2, 2), VAULT: (3, 1), FAKE: (2, 1), CRYPT: (3, 1),
    CHAOS: (3, 1), CUTTHROAT: (3, 1),   # both {2}{B/R} castable off black
}


def build_deck(fear=3, footlight=3, swamp=10, barren=2, jagged=4, carnarium=4,
               jarl=2, yaad=4, soul_reap=3, scarblade=2, blade=2, sign=0, thorn=1, vault=0,
               perigee=4, fake=0, cuombajj=2, crypt=0, chaos=0, cutthroat=0):
    """Mainboard (must total 60). yaad counts YAAD + its functional reprint Mirrodin Avenged."""
    counts = {
        FEAR: fear, FOOTLIGHT: footlight, CUOMBAJJ: cuombajj, CRYPT: crypt, CHAOS: chaos,
        CUTTHROAT: cutthroat, RAVEN: 4,
        CORRUPTED: 4, VILLAGE: 4, THORN: thorn, BLADE: blade, SIGN: sign, VAULT: vault,
        MOURNERS: 2, PERIGEE: perigee, FAKE: fake, SCARBLADE: scarblade, YAAD: yaad,
        SOUL_REAP: soul_reap, JARL: jarl,
        SWAMP: swamp, BARREN_MOOR: barren, JAGGED_BARRENS: jagged, CARNARIUM: carnarium,
    }
    deck = []
    for card, n in counts.items():
        deck.extend([card] * n)
    nlands = swamp + barren + jagged + carnarium
    assert len(deck) == 60, f"deck is {len(deck)} cards (fodder {fear+footlight}, lands {nlands}), expected 60"
    return deck


# Named configs for A/B testing. Each = kwargs to build_deck.
VARIANTS = {
    # 20-land baselines
    "current":        dict(fear=3, footlight=3, swamp=10, barren=2, jagged=4, carnarium=4),
    "20L-2carn":      dict(fear=3, footlight=3, swamp=12, barren=2, jagged=4, carnarium=2),
    # 18-land + 4/4 fodder (user proposal); different ways to shave 2 lands
    "18L-cut2carn":   dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2),
    "18L-nocarn":     dict(fear=4, footlight=4, swamp=12, barren=2, jagged=4, carnarium=0),
    "18L-cutswamp":   dict(fear=4, footlight=4, swamp=8,  barren=2, jagged=4, carnarium=4),
    # ---- current adopted list + Jarl A/B (built on 18L-cut2carn) ----
    "adopted":          dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, jarl=2, yaad=4),
    "no-jarl-6yaad":    dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, jarl=0, yaad=6),
    "no-jarl-4scarbld": dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, jarl=0, yaad=4, scarblade=4),
    # ---- Blade Juggler (2 draw-creatures) vs Sign in Blood (pure draw) ----
    "blade-to-sign":    dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, sign=2),
    "1blade-1sign":     dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=1, sign=1),
    "blade-to-vault":   dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2),
    # current adopted top end uses Vault now (Blade was swapped out on Archidekt):
    "adopted-v2":       dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2),
    "2perigee-2fyod":   dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, perigee=2, fake=2),
    # Cuombajj-in-main vs the current Crypt-Rats-in / Cuombajj-out build:
    "with-cuombajj":    dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=2, crypt=0),
    "cryptrats-main":   dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=0, crypt=2),
    # Chaos Spewer vs Perigee (built on the current Crypt-Rats-main deck):
    "chaos2":           dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=0, crypt=2, perigee=2, chaos=2),
    "chaos4":           dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=0, crypt=2, perigee=0, chaos=4),
    "cutthroat2":       dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=0, crypt=2, perigee=2, cutthroat=2),
    "cutthroat4":       dict(fear=4, footlight=4, swamp=10, barren=2, jagged=4, carnarium=2, blade=0, vault=2, cuombajj=0, crypt=2, perigee=0, cutthroat=4),
}


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, deck, on_play, rng, verbose=False):
        self.rng = rng
        self.lib = deck[:]
        rng.shuffle(self.lib)
        self.hand = []
        self.lands = []          # list of entered_turn-tagged land dicts: {'type','etb_turn'}
        self.board = defaultdict(int)   # creature name -> count in play
        self.cuombajj_sick_until = 0    # turn until which a freshly-cast Cuombajj is summoning-sick
        self.monarch = False            # Thorn of the Black Rose -> +1 card/turn (never lost in goldfish)
        self.on_play = on_play
        self.verbose = verbose
        self.log_lines = []
        self._mulligan()

    def log(self, msg):
        if self.verbose:
            self.log_lines.append(msg)

    # --- mulligan: London, keep 2-4 lands in a 7 (1 mull max for simplicity) ---
    def _draw(self, n=1):
        for _ in range(n):
            if self.lib:
                self.hand.append(self.lib.pop())

    def _mulligan(self):
        # London mulligan: draw 7, keep first hand with 2-5 lands, bottom `mull` cards.
        # Up to 3 mulligans (keep down to a 4-card hand) before settling.
        best = None
        for mull in range(4):  # 0..3 -> keep 7,6,5,4
            self.lib += self.hand
            self.hand = []
            self.rng.shuffle(self.lib)
            self._draw(7)
            nlands = sum(1 for c in self.hand if c in LANDS)
            if 2 <= nlands <= 5:
                self._bottom(mull)
                return
            best = mull  # remember we had to keep going
        # settled at mull-to-4: accept whatever we have, bottom 3
        self._bottom(3)

    def _bottom(self, n):
        # bottom the least useful: extra lands first, then high-cmc
        for _ in range(n):
            if not self.hand:
                return
            lands = [c for c in self.hand if c in LANDS]
            if len(lands) > 2:
                self.hand.remove(lands[-1])
            else:
                # bottom highest cmc nonland
                nonland = [c for c in self.hand if c not in LANDS]
                if nonland:
                    worst = max(nonland, key=lambda c: COST.get(c, (9, 0))[0])
                    self.hand.remove(worst)
                else:
                    self.hand.pop()

    # --- mana available THIS turn from lands already untapped ---
    def mana(self, turn):
        """(total, black) available this turn. Tapped lands unavailable the turn played."""
        total = black = 0
        for L in self.lands:
            available = (L['etb_turn'] < turn) or (L['type'] == SWAMP and L['etb_turn'] == turn)
            if not available:
                continue
            if L['type'] == CARNARIUM:
                total += 2; black += 1
            else:
                total += 1; black += 1
        return total, black

    # --- land drop with sequencing heuristic ---
    def play_land(self, turn, desired_now):
        hand_lands = [c for c in self.hand if c in LANDS]
        if not hand_lands:
            return
        cur_total, _ = self._mana_from_prior(turn)
        swamps = [c for c in hand_lands if c == SWAMP]
        taps = [c for c in hand_lands if c in TAPLANDS]

        choice = None
        if cur_total >= desired_now:
            # We don't need mana right now -> bank a tapland (Jagged > Moor > Carnarium)
            if JAGGED_BARRENS in taps:
                choice = JAGGED_BARRENS
            elif BARREN_MOOR in taps:
                choice = BARREN_MOOR
            elif CARNARIUM in taps and cur_total >= desired_now + 1:
                choice = CARNARIUM  # only if we have a spare to bounce
            elif swamps:
                choice = SWAMP
            elif taps:
                choice = taps[0]
        else:
            # Need mana now -> prefer an untapped Swamp
            if swamps:
                choice = SWAMP
            elif taps:  # stuck, accept tapped
                choice = JAGGED_BARRENS if JAGGED_BARRENS in taps else (BARREN_MOOR if BARREN_MOOR in taps else taps[0])
        if choice is None:
            choice = hand_lands[0]

        self.hand.remove(choice)
        self.lands.append({'type': choice, 'etb_turn': turn})
        if choice == JAGGED_BARRENS:
            self.log(f"  T{turn}: play Jagged Barrens (tapped) -> ETB 1 dmg to opp = CRIME")
        elif choice == CARNARIUM:
            # bounce a land back to hand: prefer a Swamp already in play (replay untapped later)
            in_play_swamps = [L for L in self.lands if L['type'] == SWAMP and L is not self.lands[-1]]
            bounce = in_play_swamps[0] if in_play_swamps else next((L for L in self.lands if L is not self.lands[-1]), None)
            if bounce:
                self.lands.remove(bounce)
                self.hand.append(bounce['type'])
            self.log(f"  T{turn}: play Rakdos Carnarium (tapped, bounce {bounce['type'] if bounce else '-'})")
        else:
            self.log(f"  T{turn}: play {choice}{' (tapped)' if choice in TAPLANDS else ''}")

    def _mana_from_prior(self, turn):
        total = black = 0
        for L in self.lands:
            if L['etb_turn'] < turn:
                if L['type'] == CARNARIUM:
                    total += 2; black += 1
                else:
                    total += 1; black += 1
        return total, black


# ---------------------------------------------------------------------------
# Opponent model
# ---------------------------------------------------------------------------
def opp_creature_present(turn, on_play):
    # Opponent deploys a creature each of their turns. On the play they've had (turn-1)
    # turns by our turn `turn`; on the draw they've had `turn`.
    deployed = (turn - 1) if on_play else turn
    return deployed >= 1


# ---------------------------------------------------------------------------
# One game
# ---------------------------------------------------------------------------
def simulate_game(deck, on_play, rng, turns, verbose=False):
    g = Game(deck, on_play, rng, verbose)
    # results[turn] = dict of the 3 booleans
    results = {}

    for turn in range(1, turns + 1):
        # untap (implicit), upkeep, draw
        if not (turn == 1 and on_play):
            g._draw(1)

        # ---- decide desired mana for proactive plays, then land drop ----
        ravens_in_play = g.board[RAVEN]
        raven_in_hand = RAVEN in g.hand
        want = 0
        if raven_in_hand and ravens_in_play < 2:
            want = 2
        elif any(c in g.hand for c in (FEAR, FOOTLIGHT, CUOMBAJJ)):
            want = 1
        # if we hold reactive engine pieces, we'd like +1 to hold up
        if any(c in g.hand for c in SAC_OUTLETS | {YAAD, SOUL_REAP}):
            want += 1
        g.play_land(turn, want)

        total, black = g.mana(turn)
        spent = 0

        def afford(card, lost_life_this_turn=False):
            cmc, bp = COST[card]
            if card == BLADE and lost_life_this_turn:
                cmc, bp = 3, 1
            return (total - spent) >= cmc and (black) >= bp

        # ---- MANDATORY board pieces the metrics depend on (deduct mana) ----
        # Correct sequencing = get ONE Raven down ASAP, ensure fodder if we hold an outlet,
        # deploy Cuombajj when BB is up. Extra Ravens / clock come AFTER the snapshot so they
        # don't steal the mana a crime would use this turn.
        # 1) first Raven (the payoff)
        if RAVEN in g.hand and ravens_in_play < 1 and afford(RAVEN):
            g.hand.remove(RAVEN); g.board[RAVEN] += 1; spent += 2
            g.log(f"  T{turn}: cast Raven of Fell Omens (1st)")
        # 2) ensure a Fear/Footlight on board if we have a sac outlet plan
        has_outlet = any(c in g.hand for c in SAC_OUTLETS)
        if has_outlet and not any(g.board[c] for c in DEATH_PINGERS):
            for f in (FEAR, FOOTLIGHT):
                if f in g.hand and afford(f):
                    g.hand.remove(f); g.board[f] += 1; spent += 1
                    g.log(f"  T{turn}: cast {f} (fodder)")
                    break
        # 3) Cuombajj if BB available (repeatable crime engine)
        if CUOMBAJJ in g.hand and (black >= 2) and (total - spent) >= 2 and g.board[CUOMBAJJ] == 0:
            g.hand.remove(CUOMBAJJ); g.board[CUOMBAJJ] += 1; spent += 2
            g.cuombajj_sick_until = turn  # sick this turn
            g.log(f"  T{turn}: cast Cuombajj Witches (summoning sick)")

        # ---- CAPABILITY EVALUATION with remaining mana ----
        rem = total - spent
        opp_creature = opp_creature_present(turn, on_play)
        cuombajj_ready = g.board[CUOMBAJJ] > 0 and g.cuombajj_sick_until < turn
        ravens = g.board[RAVEN]
        fodder = sum(g.board[c] for c in DEATH_PINGERS)
        outlet_in_hand = any(c in g.hand for c in SAC_OUTLETS)
        yaad_in_hand = YAAD in g.hand
        soulreap_in_hand = SOUL_REAP in g.hand
        jagged_in_hand_with_drop = (JAGGED_BARRENS in g.hand)  # could be played as the land drop for a free crime

        # --- can we damage an opp creature this turn? (needs opp_creature) ---
        can_damage_opp_creature = False
        dmg_cost = 0
        if opp_creature:
            if cuombajj_ready:
                can_damage_opp_creature = True; dmg_cost = 0           # tap, free
            elif outlet_in_hand and fodder >= 1 and rem >= 1:
                can_damage_opp_creature = True; dmg_cost = 1           # sac outlet -> death-ping
        # --- can we commit a crime this turn? (face is a valid target too) ---
        crime = False
        if cuombajj_ready:
            crime = True                                              # tap face/creature
        elif outlet_in_hand and fodder >= 1 and rem >= 1:
            crime = True                                              # death-ping face = crime
        elif soulreap_in_hand and opp_creature and rem >= 2:
            crime = True                                              # Soul Reap kills opp creature
        elif yaad_in_hand and can_damage_opp_creature and rem >= (dmg_cost + 1):
            crime = True                                              # damage + YAAD
        # NOTE: Jagged-Barrens-as-land-drop crime is already captured when actually played
        # earlier this turn (we don't double count a hand copy here).

        # --- METRIC 1: engine online ---
        engine_online = (ravens >= 1) and crime

        # --- METRIC 2: full value loop ---
        full_loop = (ravens >= 1) and outlet_in_hand and (fodder >= 1) and (rem >= 1)

        # --- METRIC 3: YAAD live ---
        yaad_live = yaad_in_hand and can_damage_opp_creature and (rem >= dmg_cost + 1)

        results[turn] = {
            'engine': engine_online,
            'loop': full_loop,
            'yaad': yaad_live,
            'ravens': ravens,
            'multi_raven_crime': (ravens >= 2 and crime),
            'mana': total,
            'tapped_drop': 0,
        }
        # tempo: did this turn's land drop come in tapped (no mana from it this turn)?
        this_drop = [L for L in g.lands if L['etb_turn'] == turn]
        if this_drop and this_drop[0]['type'] in (BARREN_MOOR, JAGGED_BARRENS, CARNARIUM):
            results[turn]['tapped_drop'] = 1

        g.log(f"  T{turn}: mana {total} (rem {rem}), ravens={ravens}, fodder={fodder}, "
              f"outlet={outlet_in_hand}, yaad={yaad_in_hand} | "
              f"ENGINE={engine_online} LOOP={full_loop} YAAD_LIVE={yaad_live}")

        # ---- POST-SNAPSHOT development (next-turn board); uses leftover mana ----
        # Priority with surplus mana: monarch engine > extra Ravens > Blade draw > Perigee body
        # > clock. Top-end is the mana sink that tests whether ramp (Carnarium) is cashed in.
        jagged_etb = bool(this_drop) and this_drop[0]['type'] == JAGGED_BARRENS
        spectacle_live = engine_online or jagged_etb   # an opponent lost life this turn?
        deployed_topend = False

        # 1) Thorn -> monarch (recurring card draw; premier sink)
        if THORN in g.hand and not g.monarch and (total - spent) >= 4:
            g.hand.remove(THORN); spent += 4; g.monarch = True; deployed_topend = True
            g.log(f"  T{turn}:   cast Thorn of the Black Rose -> MONARCH")
        # 2) extra Ravens (pure upside)
        while RAVEN in g.hand and g.board[RAVEN] < 3 and (total - spent) >= 2:
            g.hand.remove(RAVEN); g.board[RAVEN] += 1; spent += 2
            g.log(f"  T{turn}:   +extra Raven (now {g.board[RAVEN]})")
        # 3) Blade Juggler -> ETB draw; spectacle {2}{B}=3 if an opp lost life this turn else {4}{B}=5
        bcost = 3 if spectacle_live else 5
        if BLADE in g.hand and (total - spent) >= bcost:
            g.hand.remove(BLADE); spent += bcost; g._draw(1); deployed_topend = True
            g.log(f"  T{turn}:   cast Blade Juggler ({'spectacle' if spectacle_live else 'hardcast'}) -> draw")
        # Sign in Blood (BB) -> pure dig: draw 2, lose 2 life (no body)
        while SIGN in g.hand and black >= 2 and (total - spent) >= 2:
            g.hand.remove(SIGN); spent += 2; g._draw(2)
            g.log(f"  T{turn}:   cast Sign in Blood -> draw 2")
        # Vault Plunderer (2B) -> 3/1 body, draw 1
        while VAULT in g.hand and (total - spent) >= 3:
            g.hand.remove(VAULT); spent += 3; g._draw(1)
            g.log(f"  T{turn}:   cast Vault Plunderer -> draw 1 (body)")
        # 4) Perigee Beckoner -> 4/5; hardcast {4}{B}=5 (warp {1}{B}=2 fallback body)
        if PERIGEE in g.hand and (total - spent) >= 5:
            g.hand.remove(PERIGEE); g.board[PERIGEE] += 1; spent += 5; deployed_topend = True
            g.log(f"  T{turn}:   hardcast Perigee Beckoner (4/5)")
        elif PERIGEE in g.hand and (total - spent) >= 2:
            g.hand.remove(PERIGEE); g.board[PERIGEE] += 1; spent += 2
            g.log(f"  T{turn}:   warp Perigee Beckoner (2)")
        # 5) Clock: extra 1-drops if nothing reactive to hold up
        if not any(c in g.hand for c in SAC_OUTLETS | {YAAD, SOUL_REAP, JARL}):
            for f in (FEAR, FOOTLIGHT):
                while f in g.hand and (total - spent) >= 1:
                    g.hand.remove(f); g.board[f] += 1; spent += 1
                    g.log(f"  T{turn}:   +clock {f}")

        results[turn]['topend'] = 1 if deployed_topend else 0
        results[turn]['monarch'] = 1 if g.monarch else 0

        # monarch draws a card at the beginning of your end step (goldfish: never lose it)
        if g.monarch:
            g._draw(1)
            g.log(f"  T{turn}:   monarch draw")

    return results, g.log_lines


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def run(deck, label, games, turns, on_play, seed, verbose):
    rng = random.Random(seed)
    agg = {t: defaultdict(int) for t in range(1, turns + 1)}
    cum = {t: defaultdict(int) for t in range(1, turns + 1)}  # cumulative "by turn t"

    traced = 0
    for i in range(games):
        v = traced < verbose
        res, lines = simulate_game(deck, on_play, rng, turns, v)
        if v:
            print(f"\n--- {label} :: traced game {traced+1} ({'play' if on_play else 'draw'}) ---")
            for ln in lines:
                print(ln)
            traced += 1
        # per-turn and cumulative (engine/loop/yaad achieved on or before turn t)
        seen = {'engine': False, 'loop': False, 'yaad': False, 'topend': False}
        for t in range(1, turns + 1):
            r = res[t]
            for k in ('engine', 'loop', 'yaad', 'multi_raven_crime', 'tapped_drop', 'topend', 'monarch'):
                agg[t][k] += r[k]
            agg[t]['mana_sum'] += r['mana']
            for k in ('engine', 'loop', 'yaad', 'topend'):
                if r[k]:
                    seen[k] = True
                if seen[k]:
                    cum[t][k] += 1
            if r['monarch']:
                cum[t]['monarch'] += 1  # monarch is sticky once achieved

    print(f"\n================= {label}  ({'ON THE PLAY' if on_play else 'ON THE DRAW'}, {games} games) =================")
    print(f"{'Turn':<5}{'AvgMana':>8}{'Tapped%':>9}{'Engine%':>9}{'Loop%':>8}{'YAAD%':>8}{'2+Rav%':>8}   | cumulative by-turn")
    for t in range(1, turns + 1):
        a = agg[t]
        c = cum[t]
        print(f"{t:<5}{a['mana_sum']/games:>8.2f}{100*a['tapped_drop']/games:>8.0f}%"
              f"{100*a['engine']/games:>8.0f}%{100*a['loop']/games:>7.0f}%{100*a['yaad']/games:>7.0f}%"
              f"{100*a['multi_raven_crime']/games:>7.0f}%   | "
              f"eng {100*c['engine']/games:>3.0f}%  loop {100*c['loop']/games:>3.0f}%  yaad {100*c['yaad']/games:>3.0f}%"
              f"  topend {100*c['topend']/games:>3.0f}%  monarch {100*c['monarch']/games:>3.0f}%")
    return agg, cum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=50000)
    ap.add_argument('--turns', type=int, default=6)
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--verbose', type=int, default=0, help='trace this many games')
    ap.add_argument('--draw', action='store_true', help='simulate on the draw (default: play)')
    ap.add_argument('--variant', default='current',
                    help="comma-separated config names from VARIANTS, or 'all'")
    args = ap.parse_args()

    on_play = not args.draw
    names = list(VARIANTS) if args.variant == 'all' else args.variant.split(',')
    for name in names:
        kw = VARIANTS[name.strip()]
        nlands = kw['swamp'] + kw['barren'] + kw['jagged'] + kw['carnarium']
        label = (f"{name.strip()}  [Fear{kw['fear']}/Foot{kw['footlight']}, "
                 f"{nlands}L: Sw{kw['swamp']}/BM{kw['barren']}/JB{kw['jagged']}/Carn{kw['carnarium']}]")
        run(build_deck(**kw), label, args.games, args.turns, on_play, args.seed, args.verbose)


if __name__ == '__main__':
    main()
