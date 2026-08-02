#!/usr/bin/env python3
"""
metrics.py
----------
Explicit, defensible definitions for the fuzzy Phase-B concepts. Each metric is
a plain function of a player's season-total row, so the ground truth and the LLM
are held to the SAME definition. Writing these down is the whole point of Phase
B: the model cannot reason about a metric you have not articulated.

Every function takes a dict `p` with numeric fields already coerced.

IMPORTANT LIMITATION: the public 2025 cumulative page gives per-player SEASON
totals and per-game TEAM totals, but not per-player per-game splits. So a
literal "most improved = change in points-per-game between the first and second
half of the season" is NOT computable from this source. Where a metric needs
per-game player data we say so; the metrics below are the ones the available
data actually supports. (Pulling the 19 individual box scores would enable the
split-half version.)
"""

MIN_GP = 5          # minimum games played to qualify for rate-based metrics
MIN_SHOTS = 20      # minimum shots to qualify for a shooting-efficiency ranking


def points_per_game(p):
    return p["pts"] / p["gp"] if p["gp"] else 0.0


def game_changer_index(p):
    """Offensive game-changer: total scoring output plus a clutch bonus.

    GCI = points + 2 * game_winning_goals

    Rationale: points capture goals+assists (total offensive production); the
    game-winning-goal bonus rewards production that actually decided games,
    which is what "changes a game" means for an attacker. Deliberately simple
    and transparent so it can be checked by hand and stated to the model.
    """
    return p["pts"] + 2 * p["gwg"]


def two_way_impact(p):
    """Holistic contribution on both ends, per the box score's possession stats.

    TWI = points + ground_balls + caused_turnovers + draw_controls - turnovers

    Rewards scoring and possession-winning (GBs, caused TOs, draw controls),
    penalizes giving the ball away. Surfaces defenders/draw specialists that a
    pure-scoring metric misses.
    """
    return (p["pts"] + p["gb"] + p["ct"] + p["dc"] - p["to"])


def shooting_efficiency(p):
    """Shot percentage, but only meaningful above a shot-volume floor.

    Returns None for players below MIN_SHOTS so tiny-sample .000/1.000 rates
    don't win the ranking.
    """
    if p["sh"] < MIN_SHOTS:
        return None
    return p["sh_pct"]


def qualifies_rate(p):
    return p["gp"] >= MIN_GP


# Registry so other scripts / the harness can list and apply metrics uniformly.
METRICS = {
    "points_per_game": points_per_game,
    "game_changer_index": game_changer_index,
    "two_way_impact": two_way_impact,
    "shooting_efficiency": shooting_efficiency,
}

DEFINITIONS = {
    "points_per_game": "points / games_played (qualified: gp >= %d)" % MIN_GP,
    "game_changer_index": "points + 2 * game_winning_goals",
    "two_way_impact": "points + ground_balls + caused_turnovers + draw_controls - turnovers",
    "shooting_efficiency": "shot_percentage, among players with >= %d shots" % MIN_SHOTS,
    "most_improved": "NOT computable from season totals; would require per-game "
                     "player data (box scores) to compare first-half vs "
                     "second-half points-per-game.",
}
