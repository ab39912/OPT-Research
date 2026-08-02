# Task_05_Descriptive_Stats

This project gives a small, clean dataset to a large language model and asks it
questions in plain English. I use my own descriptive statistics as the answer
key to check the model. Phase A tests factual questions. Phase B defines custom
metrics and pushes the model to an advisory "coach" question, and I check every
answer against the numbers.

## Dataset

2025 Syracuse University Women's Lacrosse (10-9 record), from the official
cumulative statistics page:
<https://cuse.com/sports/womens-lacrosse/stats/2025/>

Two small tables:
- `data/su_wlax_2025_players.csv`: 32 players, season totals (goals, assists,
  points, shots, ground balls, draw controls, and more)
- `data/su_wlax_2025_games.csv`: 19 games, per-game team totals (result, goals
  for and against, shooting, possession stats)

The dataset is not committed to the repo (per the task). Regenerate it with:

```bash
python prepare_data.py     # writes both CSVs into data/
```

`prepare_data.py` holds the values taken from the public page and lists the
source URL. You can also download the page yourself and put the CSVs in `data/`.

### A real data-quality quirk (kept, not fixed)
The player goal column adds up to 234, but the team scored 235 (both the
published total row and the game log say 235). So the player table is off by one
goal. I treat 235 as the team truth and flag the gap. It also works as a trap
(question A10) to see whether a model notices it or skips over it.

## Reproduce the ground truth

```bash
python prepare_data.py
python ground_truth.py     # prints the answer key; writes logs/ground_truth.md
                           # and logs/questions_with_answers.json
```

`ground_truth.py` reuses `datakit.py` (the engine from Tasks 2 and 3) for the
descriptive stats, and `metrics.py` for the Phase B definitions.

## Run the LLM experiment

The question bank is in `questions.json` (10 factual/trap and 5 judgment).

```bash
# Print the dataset and questions to paste into any model (Claude/ChatGPT/Copilot):
python eval_harness.py --list

# Score a model's answers against ground truth (auto-grades factual/trap):
python eval_harness.py --score logs/responses_claude-opus-4-8.json

# Optional: auto-query the Anthropic API to generate a run (needs ANTHROPIC_API_KEY):
python eval_harness.py --ask claude-opus-4-8
```

Log each model's run in a copy of `PROMPT_LOG_TEMPLATE.md`, plus a
`logs/responses_<model>.json` file that maps each question id to the answer (used
for auto-grading).

## Metrics (Phase B)

Full definitions are in [`METRICS.md`](METRICS.md). In short: `game_changer_index`
= points + 2 x GWG; `points_per_game` (min 5 games); `two_way_impact` = points +
ground balls + caused turnovers + draw controls - turnovers; `shooting_efficiency`
= shot % (min 20 shots). "Most improved" is flagged as not computable from season
totals, because it needs per-game player data from the box scores.

## Experiment narrative and findings

I ran two Claude models on the same question bank. Both transcripts are in
`logs/`. Main points:

- On a small, clean table that fits fully in context, the models were reliable
  across the board, including the arithmetic items and the metric questions, and
  did not make up any numbers.
- They caught both traps: the goals that do not add up (234 vs 235) and the
  small-sample shooting rate (they left out a player who was 1 for 1).
- They used the metric definitions I gave them instead of switching to their own
  idea of "game changer" or "efficient."
- The advisory answers were backed by the data. Both picked offense/finishing
  (goals for dropped by 7.0 per game in losses versus a 3.0 drop on defense; shot
  % was .491 in wins and .374 in losses; three losses were by one goal) and both
  named a defensible player (Emma Ward, the offensive engine).

### Multi-model comparison (bonus)

I ran two Claude models on the same question bank:

| | Claude Opus 4.8 | Claude Haiku 4.5 |
|---|---|---|
| Factual/trap (auto-graded) | 10/10 | 10/10 |
| Caught the A10 goals trap (234 vs 235) | yes | yes |
| Respected the B4 shot-volume floor | yes | yes |
| Judgment answers vs anchors (B1-B5) | all match | all match |
| Advisory (B5) survives validation | yes | yes |

On this small, clean table the two models were basically the same: same factual
score, same metric rankings, same coach recommendation (offense; Emma Ward). The
smaller and faster Haiku matched the larger Opus, and even added full top-5
lists without being asked. This is expected, since this is the setting LLMs do
best in. The harder tests would be a bigger or messier context, undefined
metrics, or a weaker non-Claude model, where wrong answers are more likely.
Transcripts: `logs/transcript_claude-opus-4-8.md`,
`logs/transcript_claude-haiku-4-5.md`.

### Where an LLM should be trusted here, and where not
This is the setting LLMs handle best: a small, clean table that fits in context.
The failures are more likely to show up (a) with weaker models, (b) with a bigger
or messier context, and (c) on the judgment question when the metric is left
undefined. Those are what the ChatGPT/Copilot comparison, the context-size test,
and the undefined-metric test are meant to check. The takeaway: trust the model
for lookups and well-defined math on small clean data, but define the metrics
yourself and check every recommendation against numbers you computed.

## Repository layout

```
prepare_data.py        rebuilds the CSVs from the public source (no deps)
datakit.py             reused stats engine from Tasks 2-3
metrics.py             Phase-B metric definitions
ground_truth.py        computes and writes the answer key (no deps)
questions.json         the question bank with the ground truth
eval_harness.py        list / score / (optional) API-ask; auto-grades factual
METRICS.md             metric write-up
PROMPT_LOG_TEMPLATE.md blank log for ChatGPT/Copilot/other runs
logs/
  ground_truth.md                generated answer key
  questions_with_answers.json    generated machine-readable key
  transcript_claude-opus-4-8.md  one real, validated model run (10/10)
  responses_claude-opus-4-8.json machine-gradeable answers for that run
  transcript_claude-haiku-4-5.md second model run (10/10)
  responses_claude-haiku-4-5.json machine-gradeable answers for that run
```

## Reproducibility
- No hardcoded paths. Scripts take file arguments or sensible defaults.
- `prepare_data.py`, `ground_truth.py`, and the core harness use only the
  standard library. The dataset can be regenerated and is not committed.