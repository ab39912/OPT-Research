{
  "phase_a": {
    "games_played": 19,
    "record": "10-9",
    "total_goals_for": 235,
    "total_goals_against": 221,
    "top_scorer": "Muchnick, Emma (34 goals)",
    "most_assists": "Ward, Emma (46 assists)",
    "most_points": "Ward, Emma (76 points)",
    "avg_margin_in_wins": 5.5,
    "avg_margin_in_losses": -4.56,
    "highest_combined_score_game": "UAlbany (2025-02-07), 30 combined (21-9)",
    "biggest_win": "UAlbany 21-9",
    "worst_loss": "Boston College 2-17",
    "players_with_a_goal": 17,
    "roster_size": 32,
    "sum_player_goals": 234
  },
  "phase_b": {
    "game_changer_index_top5": [
      [
        78,
        "Ward, Emma"
      ],
      [
        51,
        "Trinkaus, Caroline"
      ],
      [
        45,
        "Muchnick, Emma"
      ],
      [
        30,
        "Britton, Gracie"
      ],
      [
        27,
        "Vogelman, Alexa"
      ]
    ],
    "points_per_game_top5": [
      [
        4.0,
        "Ward, Emma"
      ],
      [
        2.263,
        "Trinkaus, Caroline"
      ],
      [
        2.158,
        "Muchnick, Emma"
      ],
      [
        1.579,
        "Britton, Gracie"
      ],
      [
        1.421,
        "Vogelman, Alexa"
      ]
    ],
    "two_way_impact_top5": [
      [
        85,
        "Caramelli, Joely"
      ],
      [
        73,
        "Rode, Meghan"
      ],
      [
        72,
        "Vandiver, Coco"
      ],
      [
        69,
        "Vogelman, Alexa"
      ],
      [
        59,
        "Muchnick, Emma"
      ]
    ],
    "shooting_efficiency_top5": [
      [
        0.488,
        "Britton, Gracie"
      ],
      [
        0.479,
        "Muchnick, Emma"
      ],
      [
        0.457,
        "Vogelman, Alexa"
      ],
      [
        0.452,
        "Volpe, Ashlee"
      ],
      [
        0.444,
        "Trinkaus, Caroline"
      ]
    ],
    "offense_defense_diagnosis": {
      "gf_per_game_overall": 12.37,
      "ga_per_game_overall": 11.63,
      "gf_per_game_in_wins": 15.7,
      "gf_per_game_in_losses": 8.67,
      "ga_per_game_in_wins": 10.2,
      "ga_per_game_in_losses": 13.22,
      "one_goal_losses": 3,
      "sh_pct_in_wins": 0.491,
      "sh_pct_in_losses": 0.374
    }
  },
  "data_quality_note": "Player goals sum to 234, but the team scored 235 (per both the published Total row and the game-by-game log). The per-player table is internally off by one goal \u2014 a real quirk in the published data. We treat the game log's 235 as team truth and flag the discrepancy rather than silently reconciling it. This is a useful ground-truth trap to see whether an LLM notices or papers over it."
}