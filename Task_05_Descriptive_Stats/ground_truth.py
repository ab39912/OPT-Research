#!/usr/bin/env python3
"""
eval_harness.py  (Bonus: evaluation harness)
--------------------------------------------
Automates the LLM experiment against the ground-truth answer key so it can be
re-run as models change. Three modes:

  --list
      Print the question bank as a clean prompt block you can paste into any
      chat model (Claude, ChatGPT, Copilot), along with the dataset.

  --score responses.json
      Score a model's answers against ground truth. `responses.json` maps
      question id -> the model's answer string, e.g. {"A1": "They played 19..."}.
      Factual/trap questions are auto-graded by checking that every required
      token in the question's `match` list appears in the answer. Judgment
      questions are printed with their ground-truth anchors for you to grade,
      since they have no single correct string.

  --ask MODEL
      Optional: actually call the Anthropic API to answer every question, given
      the dataset, and write the responses to logs/responses_<model>.json. Needs
      ANTHROPIC_API_KEY in the environment and the `anthropic` package. This lets
      you generate a real transcript automatically. (ChatGPT/Copilot must be run
      by hand and their answers pasted into a responses file for --score.)

Usage:
    python eval_harness.py --list
    python eval_harness.py --score logs/responses_claude.json
    python eval_harness.py --ask claude-opus-4-8      # optional, needs API key
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_questions():
    with open(os.path.join(HERE, "questions.json"), encoding="utf-8") as fh:
        return json.load(fh)


def read_dataset_text():
    """Return the two CSVs as text, for pasting into a model prompt."""
    out = []
    for name in ("su_wlax_2025_players.csv", "su_wlax_2025_games.csv"):
        path = os.path.join(HERE, "data", name)
        if os.path.exists(path):
            out.append(f"### {name}\n```\n{open(path).read().strip()}\n```")
        else:
            out.append(f"### {name}\n(run prepare_data.py first)")
    return "\n\n".join(out)


def cmd_list(q):
    print("=" * 70)
    print("DATASET (paste this, then the questions, into your model)")
    print("=" * 70)
    print(read_dataset_text())
    print("\n" + "=" * 70)
    print("QUESTIONS")
    print("=" * 70)
    for item in q["questions"]:
        print(f'[{item["id"]}] ({item["phase"]}/{item["type"]}) {item["prompt"]}')


def grade_factual(answer, match_tokens):
    a = answer.lower()
    missing = [t for t in match_tokens if t.lower() not in a]
    return (len(missing) == 0, missing)


def cmd_score(q, responses_path):
    with open(responses_path, encoding="utf-8") as fh:
        responses = json.load(fh)
    auto_total = auto_correct = 0
    print(f"Scoring {responses_path}\n" + "=" * 70)
    for item in q["questions"]:
        qid = item["id"]
        ans = responses.get(qid)
        if ans is None:
            print(f"[{qid}] (no response)")
            continue
        if item["type"] in ("factual", "trap"):
            ok, missing = grade_factual(ans, item.get("match", []))
            auto_total += 1
            auto_correct += int(ok)
            verdict = "CORRECT" if ok else f"WRONG (missing {missing})"
            print(f"[{qid}] {verdict}")
            print(f"      GT: {item['ground_truth']}")
            print(f"      model: {ans.strip()[:120]}")
        else:
            print(f"[{qid}] JUDGMENT — grade manually")
            print(f"      GT: {item['ground_truth'][:160]}")
            if "anchors" in item:
                print(f"      anchors: {item['anchors']}")
            print(f"      model: {ans.strip()[:160]}")
        print()
    if auto_total:
        print("=" * 70)
        print(f"Auto-graded factual/trap: {auto_correct}/{auto_total} "
              f"({auto_correct / auto_total * 100:.0f}%)")


def cmd_ask(q, model):
    try:
        import anthropic
    except ImportError:
        sys.exit("The 'anthropic' package is required for --ask. "
                 "pip install anthropic, and set ANTHROPIC_API_KEY.")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY to use --ask.")
    client = anthropic.Anthropic()
    dataset = read_dataset_text()
    responses = {}
    for item in q["questions"]:
        prompt = (f"You are given a dataset of the 2025 Syracuse Women's "
                  f"Lacrosse season.\n\n{dataset}\n\nQuestion: {item['prompt']}\n"
                  f"Answer using only the data above. Show your reasoning.")
        msg = client.messages.create(
            model=model, max_tokens=1000,
            messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in msg.content if b.type == "text")
        responses[item["id"]] = text
        print(f"[{item['id']}] asked.")
    out = os.path.join(HERE, "logs", f"responses_{model}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(responses, fh, indent=2)
    print(f"\nWrote {out}. Now run: python eval_harness.py --score {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--score", metavar="RESPONSES_JSON")
    g.add_argument("--ask", metavar="MODEL")
    args = ap.parse_args()

    q = load_questions()
    if args.list:
        cmd_list(q)
    elif args.score:
        cmd_score(q, args.score)
    elif args.ask:
        cmd_ask(q, args.ask)


if __name__ == "__main__":
    main()
