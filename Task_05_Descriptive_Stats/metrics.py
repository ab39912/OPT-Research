#!/usr/bin/env python3
"""
ground_truth.py
---------------
Computes the trustworthy answer key for the 2025 SU Women's Lacrosse dataset:
dataset-level descriptive stats, the Phase-A factual answers, and the Phase-B
derived-metric rankings. Prints a readable report and writes:

    logs/ground_truth.md            human-readable answer key
    logs/questions_with_answers.json machine-readable key for the eval harness

Reuses datakit.py (the engine from Tasks 2-3) for the descriptive-stats layer.
Run prepare_data.py first to create the CSVs.

Usage:
    python ground_truth.py [--players data/su_wlax_2025_players.csv]
                           [--games   data/su_wlax_2025_games.csv]
"""

import argparse
import csv
import json
import os

import metrics as M

HERE = os.path.dirname(os.path.abspath(__file__))
NUMERIC_PLAYER = ["gp", "gs", "g", "a", "pts", "sh", "sh_pct", "sog", "sog_pct",
                  "gwg", "fpg", "fps", "gb", "to", "ct", "dc", "fouls",
                  "rc", "yc", "gc"]
NUMERIC_GAME = ["goals_for", "goals_against", "team_assists", "shots", "sh_pct",
                "sog", "ground_balls", "turnovers", "caused_turnovers",
                "draw_controls"]


def load(path, numeric):
    rows = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        for k in numeric:
            if k in r and r[k] != "":
                r[k] = float(r[k]) if "." in r[k] else int(r[k])
        rows.append(r)
    return rows


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


# --------------------------------------------------------------------------- #
# Phase A: factual answers
# --------------------------------------------------------------------------- #
def phase_a(players, games):
    wins = [g for g in games if g["result"] == "W"]
    losses = [g for g in games if g["result"] == "L"]
    scorers = sorted(players, key=lambda p: p["g"], reverse=True)
    passers = sorted(players, key=lambda p: p["a"], reverse=True)
    pointers = sorted(players, key=lambda p: p["pts"], reverse=True)
    combined = [(g["goals_for"] + g["goals_against"], g) for g in games]
    hi_combined = max(combined, key=lambda t: t[0])
    biggest_win = max(wins, key=lambda g: g["goals_for"] - g["goals_against"])
    worst_loss = min(losses, key=lambda g: g["goals_for"] - g["goals_against"])

    a = {}
    a["games_played"] = len(games)
    a["record"] = f'{len(wins)}-{len(losses)}'
    a["total_goals_for"] = sum(g["goals_for"] for g in games)
    a["total_goals_against"] = sum(g["goals_against"] for g in games)
    a["top_scorer"] = f'{scorers[0]["player"]} ({scorers[0]["g"]} goals)'
    a["most_assists"] = f'{passers[0]["player"]} ({passers[0]["a"]} assists)'
    a["most_points"] = f'{pointers[0]["player"]} ({pointers[0]["pts"]} points)'
    a["avg_margin_in_wins"] = round(
        mean(g["goals_for"] - g["goals_against"] for g in wins), 2)
    a["avg_margin_in_losses"] = round(
        mean(g["goals_for"] - g["goals_against"] for g in losses), 2)
    a["highest_combined_score_game"] = (
        f'{hi_combined[1]["opponent"]} ({hi_combined[1]["date"]}), '
        f'{hi_combined[0]} combined '
        f'({hi_combined[1]["goals_for"]}-{hi_combined[1]["goals_against"]})')
    a["biggest_win"] = (f'{biggest_win["opponent"]} '
                        f'{biggest_win["goals_for"]}-{biggest_win["goals_against"]}')
    a["worst_loss"] = (f'{worst_loss["opponent"]} '
                       f'{worst_loss["goals_for"]}-{worst_loss["goals_against"]}')
    a["players_with_a_goal"] = sum(1 for p in players if p["g"] > 0)
    a["roster_size"] = len(players)
    # Data-quality note: player goals vs team goals.
    a["sum_player_goals"] = sum(p["g"] for p in players)
    return a


# --------------------------------------------------------------------------- #
# Phase B: derived-metric rankings
# --------------------------------------------------------------------------- #
def rank(players, fn, qualify=None, top=5):
    pool = [p for p in players if (qualify(p) if qualify else True)]
    scored = [(fn(p), p) for p in pool if fn(p) is not None]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [(round(s, 3), p["player"]) for s, p in scored[:top]]


def phase_b(players, games):
    b = {}
    b["game_changer_index_top5"] = rank(players, M.game_changer_index, top=5)
    b["points_per_game_top5"] = rank(players, M.points_per_game,
                                     qualify=M.qualifies_rate, top=5)
    b["two_way_impact_top5"] = rank(players, M.two_way_impact, top=5)
    b["shooting_efficiency_top5"] = rank(players, M.shooting_efficiency, top=5)

    # Offense-vs-defense diagnosis for the "coach" question.
    wins = [g for g in games if g["result"] == "W"]
    losses = [g for g in games if g["result"] == "L"]
    b["offense_defense_diagnosis"] = {
        "gf_per_game_overall": round(mean(g["goals_for"] for g in games), 2),
        "ga_per_game_overall": round(mean(g["goals_against"] for g in games), 2),
        "gf_per_game_in_wins": round(mean(g["goals_for"] for g in wins), 2),
        "gf_per_game_in_losses": round(mean(g["goals_for"] for g in losses), 2),
        "ga_per_game_in_wins": round(mean(g["goals_against"] for g in wins), 2),
        "ga_per_game_in_losses": round(mean(g["goals_against"] for g in losses), 2),
        "one_goal_losses": sum(1 for g in losses
                               if g["goals_against"] - g["goals_for"] == 1),
        "sh_pct_in_wins": round(mean(g["sh_pct"] for g in wins), 3),
        "sh_pct_in_losses": round(mean(g["sh_pct"] for g in losses), 3),
    }
    return b


def render_markdown(a, b, dq_note):
    L = ["# Ground-Truth Answer Key — 2025 SU Women's Lacrosse\n",
         "Computed by `ground_truth.py` from the CSVs built by `prepare_data.py`.\n",
         "## Phase A — factual\n"]
    for k, v in a.items():
        L.append(f"- **{k}**: {v}")
    L.append("\n## Phase B — derived metrics\n")
    L.append(f"Metric definitions (see `metrics.py`):")
    for k, v in M.DEFINITIONS.items():
        L.append(f"- `{k}`: {v}")
    L.append("")
    for key in ["game_changer_index_top5", "points_per_game_top5",
                "two_way_impact_top5", "shooting_efficiency_top5"]:
        L.append(f"**{key}**")
        for score, name in b[key]:
            L.append(f"  - {name}: {score}")
        L.append("")
    L.append("**offense_defense_diagnosis**")
    for k, v in b["offense_defense_diagnosis"].items():
        L.append(f"  - {k}: {v}")
    L.append("\n## Data-quality note\n")
    L.append(dq_note)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--players", default=os.path.join(HERE, "data",
                                                      "su_wlax_2025_players.csv"))
    ap.add_argument("--games", default=os.path.join(HERE, "data",
                                                    "su_wlax_2025_games.csv"))
    args = ap.parse_args()

    players = load(args.players, NUMERIC_PLAYER)
    games = load(args.games, NUMERIC_GAME)

    a = phase_a(players, games)
    b = phase_b(players, games)

    dq_note = (
        f"Player goals sum to {a['sum_player_goals']}, but the team scored "
        f"{a['total_goals_for']} (per both the published Total row and the "
        f"game-by-game log). The per-player table is internally off by one "
        f"goal — a real quirk in the published data. We treat the game log's "
        f"{a['total_goals_for']} as team truth and flag the discrepancy rather "
        f"than silently reconciling it. This is a useful ground-truth trap to "
        f"see whether an LLM notices or papers over it.")

    print(render_markdown(a, b, dq_note))

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "ground_truth.md"), "w",
              encoding="utf-8") as fh:
        fh.write(render_markdown(a, b, dq_note))
    with open(os.path.join(HERE, "logs", "questions_with_answers.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"phase_a": a, "phase_b": b, "data_quality_note": dq_note},
                  fh, indent=2)
    print("\n[wrote logs/ground_truth.md and logs/questions_with_answers.json]")


if __name__ == "__main__":
    main()
