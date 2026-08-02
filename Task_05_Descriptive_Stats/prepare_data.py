# Derived Metrics (Phase B)

Fuzzy questions have no answer until the terms are defined. These are the
operational definitions used in this project. Each is a plain function of a
player's season totals (see `metrics.py`), so the ground truth and the LLM are
held to the *same* definition. The point of writing them down is that a model
cannot reason about a metric you have not articulated — and that you can check
whether it applied your definition or quietly substituted its own.

## game_changer_index = points + 2 × game_winning_goals
An attacker's total offensive output (points already fold in goals and assists)
plus a bonus for goals that actually decided games. Transparent and hand-checkable.
**2025 top:** Emma Ward (78), then Trinkaus (51), Muchnick (45).

## points_per_game = points ÷ games_played (qualified: gp ≥ 5)
Rate rather than volume, with a games floor so a 3-game player on a hot streak
doesn't top the list. **2025 top:** Emma Ward (4.0).

## two_way_impact = points + ground_balls + caused_turnovers + draw_controls − turnovers
Rewards scoring *and* winning possessions (ground balls, caused turnovers, draw
controls) while penalizing giveaways. Deliberately surfaces defenders and draw
specialists a pure-scoring metric misses. **2025 top:** Joely Caramelli (85),
then Rode (73), Vandiver (72) — none of them the leading scorers.

## shooting_efficiency = shot % (qualified: ≥ 20 shots)
Shot percentage with a volume floor, so tiny-sample rates (a player 1-for-1 at
1.000) don't win. **2025 top:** Gracie Britton (.488), just over Muchnick (.479).

## most_improved — NOT computable from this source
The natural definition ("largest positive change in points-per-game between the
first and second half of the season") needs per-player, per-game data. The
public cumulative page provides per-player *season* totals and per-game *team*
totals only. Computing this would require pulling the 19 individual box scores
and rebuilding a player-by-game table. Flagged here rather than faked — knowing
what the data *cannot* answer is part of trustworthy ground truth.

## Offense-vs-defense diagnosis (for the advisory question)
Not a per-player metric but the analysis behind the "coach" question, computed
in `ground_truth.py` from the game log:

| split | goals for / game | goals against / game | shot % |
|---|---:|---:|---:|
| in wins | 15.70 | 10.20 | .491 |
| in losses | 8.67 | 13.22 | .374 |

The offensive swing between wins and losses (−7.0 goals/game) is more than twice
the defensive swing (+3.0). With three one-goal losses, the data points to
**finishing/offense** as the higher-leverage place to find two more wins.
