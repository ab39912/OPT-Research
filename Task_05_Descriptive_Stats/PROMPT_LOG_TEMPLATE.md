#!/usr/bin/env python3
"""
prepare_data.py
---------------
Reconstructs the two CSVs used in this project from the public 2025 Syracuse
University Women's Lacrosse cumulative statistics page:

    https://cuse.com/sports/womens-lacrosse/stats/2025/

The values below were transcribed from that page's "Players" table (season
totals per player) and its "Team" game-by-game table (per-game team totals).
Running this script writes:

    data/su_wlax_2025_players.csv   (31 rows, one per player)
    data/su_wlax_2025_games.csv     (19 rows, one per game)

The dataset itself is NOT committed to the repo (see .gitignore); this script is
how you regenerate it. If cuse.com updates the page, re-transcribe or scrape it.

No third-party dependencies.
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

SOURCE_URL = "https://cuse.com/sports/womens-lacrosse/stats/2025/"

# --------------------------------------------------------------------------- #
# Players: season totals. Columns match the site's glossary.
# number, player, gp, gs, g, a, pts, sh, sh_pct, sog, sog_pct, gwg, fpg, fps,
# gb, to, ct, dc, fouls, rc, yc, gc
# --------------------------------------------------------------------------- #
PLAYER_HEADER = ["number", "player", "gp", "gs", "g", "a", "pts", "sh",
                 "sh_pct", "sog", "sog_pct", "gwg", "fpg", "fps", "gb", "to",
                 "ct", "dc", "fouls", "rc", "yc", "gc"]

PLAYERS = [
    [44, "Ward, Emma", 19, 19, 30, 46, 76, 77, .390, 55, .714, 1, 3, 9, 6, 41, 2, 0, 9, 0, 1, 0],
    [24, "Trinkaus, Caroline", 19, 18, 32, 11, 43, 72, .444, 57, .792, 4, 9, 11, 6, 16, 5, 8, 6, 0, 3, 7],
    [5, "Muchnick, Emma", 19, 18, 34, 7, 41, 71, .479, 55, .775, 2, 12, 24, 27, 31, 9, 13, 8, 0, 1, 1],
    [19, "Britton, Gracie", 19, 14, 20, 10, 30, 41, .488, 33, .805, 0, 3, 7, 8, 16, 0, 1, 2, 0, 0, 1],
    [11, "Vogelman, Alexa", 19, 10, 21, 6, 27, 46, .457, 35, .761, 0, 9, 14, 25, 27, 13, 31, 26, 0, 3, 0],
    [47, "Cotter, Mileena", 19, 13, 21, 2, 23, 50, .420, 38, .760, 1, 4, 10, 11, 26, 10, 24, 29, 0, 0, 5],
    [33, "Caramelli, Joely", 19, 13, 16, 4, 20, 46, .348, 29, .630, 0, 0, 5, 23, 8, 11, 39, 30, 0, 2, 4],
    [22, "Guzik, Molly", 19, 0, 14, 5, 19, 34, .412, 23, .676, 0, 0, 0, 15, 14, 8, 13, 15, 0, 2, 1],
    [1, "Adamson, Olivia", 3, 3, 10, 6, 16, 18, .556, 13, .722, 1, 1, 1, 2, 7, 1, 5, 1, 0, 0, 1],
    [21, "Volpe, Ashlee", 12, 8, 14, 2, 16, 31, .452, 22, .710, 0, 2, 4, 5, 10, 1, 0, 2, 0, 1, 2],
    [18, "Desimone, Carlie", 15, 5, 3, 9, 12, 12, .250, 9, .750, 0, 0, 1, 8, 7, 2, 0, 4, 0, 0, 1],
    [72, "Devito, Sam", 19, 13, 8, 2, 10, 12, .667, 11, .917, 0, 1, 2, 22, 11, 13, 11, 14, 0, 0, 4],
    [12, "Parker, Annie", 15, 0, 6, 1, 7, 13, .462, 9, .692, 1, 0, 1, 1, 4, 0, 1, 0, 0, 0, 3],
    [2, "Peters, Bri", 3, 0, 2, 1, 3, 3, .667, 3, 1.000, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 3],
    [6, "Rowley, Payton", 6, 0, 1, 0, 1, 3, .333, 2, .667, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
    [20, "Rich, Mackenzie", 5, 0, 1, 0, 1, 1, 1.000, 1, 1.000, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0],
    [28, "Rode, Meghan", 17, 9, 1, 0, 1, 3, .333, 2, .667, 0, 0, 0, 1, 4, 0, 75, 17, 0, 0, 1],
    [0, "Guyette, Daniella", 19, 19, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 28, 8, 2, 0, 0, 0, 0, 0],
    [4, "Benoit, Kaci", 19, 19, 0, 0, 0, 2, .000, 1, .500, 0, 0, 0, 34, 5, 12, 13, 51, 0, 1, 3],
    [7, "Horvit, Ana", 12, 3, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 6, 2, 2, 0, 15, 0, 0, 1],
    [8, "Reber, Lexi", 8, 8, 0, 0, 0, 1, .000, 1, 1.000, 0, 0, 0, 5, 2, 1, 1, 16, 0, 2, 0],
    [9, "Basciano, Julia", 2, 2, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [15, "Boggs, Kendall", 5, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [16, "Vandiver, Coco", 19, 18, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 34, 3, 40, 1, 51, 0, 1, 0],
    [17, "Olsen, McKenzie", 2, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [25, "Blesi, Ella", 5, 1, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 2, 2, 0, 0, 3, 0, 1, 0],
    [27, "Lahah, Izzy", 6, 2, 0, 0, 0, 2, .000, 2, 1.000, 0, 0, 0, 7, 1, 8, 1, 9, 0, 1, 1],
    [30, "Clark, Superia", 16, 13, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 14, 7, 13, 2, 46, 0, 1, 0],
    [34, "Bethea-jones, Chloe", 4, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    [35, "Nash, Alice", 1, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [45, "Peers, Ava", 1, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [88, "Hanlon, Allie", 3, 0, 0, 0, 0, 0, .000, 0, .000, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
]

# --------------------------------------------------------------------------- #
# Games: per-game team totals. goals_for/goals_against come from the score.
# date, opponent, result, goals_for, goals_against, team_assists, shots,
# sh_pct, sog, ground_balls, turnovers, caused_turnovers, draw_controls
# --------------------------------------------------------------------------- #
GAME_HEADER = ["date", "opponent", "result", "goals_for", "goals_against",
               "team_assists", "shots", "sh_pct", "sog", "ground_balls",
               "turnovers", "caused_turnovers", "draw_controls"]

GAMES = [
    ["2025-02-07", "UAlbany", "W", 21, 9, 14, 34, .618, 26, 20, 17, 14, 19],
    ["2025-02-15", "Maryland", "W", 15, 9, 9, 26, .577, 19, 13, 15, 9, 12],
    ["2025-02-18", "Cornell", "W", 18, 10, 12, 31, .581, 24, 16, 20, 10, 16],
    ["2025-02-22", "North Carolina", "L", 8, 16, 4, 27, .296, 17, 11, 15, 3, 9],
    ["2025-02-25", "Northwestern", "L", 8, 12, 3, 22, .364, 15, 10, 14, 4, 6],
    ["2025-03-01", "Clemson", "L", 8, 9, 2, 17, .471, 14, 17, 16, 8, 4],
    ["2025-03-07", "Stanford", "W", 14, 13, 7, 28, .500, 23, 17, 17, 10, 17],
    ["2025-03-10", "Johns Hopkins", "L", 13, 14, 4, 27, .481, 22, 16, 13, 9, 16],
    ["2025-03-15", "Pitt", "W", 17, 11, 6, 36, .472, 31, 22, 15, 12, 13],
    ["2025-03-19", "Loyola", "W", 14, 12, 5, 35, .400, 27, 23, 8, 8, 10],
    ["2025-03-23", "Notre Dame", "W", 12, 11, 7, 31, .387, 24, 13, 12, 8, 15],
    ["2025-03-29", "Virginia", "W", 13, 12, 8, 30, .433, 21, 16, 12, 5, 13],
    ["2025-04-02", "Yale", "L", 10, 13, 5, 20, .500, 19, 11, 8, 5, 7],
    ["2025-04-05", "California", "W", 18, 6, 7, 41, .439, 31, 13, 10, 7, 14],
    ["2025-04-12", "Virginia Tech", "L", 11, 14, 4, 36, .306, 24, 15, 14, 7, 16],
    ["2025-04-17", "Boston College", "L", 2, 17, 0, 23, .087, 14, 18, 14, 5, 10],
    ["2025-04-22", "Stanford", "L", 10, 15, 6, 28, .357, 19, 18, 22, 10, 18],
    ["2025-05-09", "Brown", "W", 15, 9, 4, 30, .500, 20, 17, 14, 10, 15],
    ["2025-05-11", "Yale", "L", 8, 9, 5, 16, .500, 12, 9, 14, 9, 10],
]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main():
    os.makedirs(DATA, exist_ok=True)
    p_path = os.path.join(DATA, "su_wlax_2025_players.csv")
    g_path = os.path.join(DATA, "su_wlax_2025_games.csv")
    write_csv(p_path, PLAYER_HEADER, PLAYERS)
    write_csv(g_path, GAME_HEADER, GAMES)
    print(f"Source: {SOURCE_URL}")
    print(f"Wrote {len(PLAYERS)} players -> {p_path}")
    print(f"Wrote {len(GAMES)} games   -> {g_path}")


if __name__ == "__main__":
    main()
