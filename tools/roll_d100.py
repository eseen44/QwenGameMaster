"""Create one immutable d100 roll record and append it to the campaign journal."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JOURNAL = ROOT / "campaigns" / "lucan" / "journal" / "rolls.jsonl"


def character_modifier(score: int) -> int:
    if score >= 9:
        return 15
    if score >= 7:
        return 10
    if score >= 5:
        return 0
    if score >= 3:
        return -5
    if score >= 1:
        return -15
    return -30


def parse_modifier(value: str) -> dict[str, int | str]:
    try:
        source, raw_number = value.rsplit("=", 1)
        number = int(raw_number)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "modifier must have the form source=integer"
        ) from exc
    if not source.strip():
        raise argparse.ArgumentTypeError("modifier source cannot be empty")
    return {"source": source.strip(), "value": number}


def existing_ids(journal: Path) -> set[str]:
    if not journal.exists():
        return set()
    result: set[str] = set()
    for line_number, raw_line in enumerate(
        journal.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid journal JSON on line {line_number}: {exc}") from exc
        if isinstance(record, dict) and isinstance(record.get("id"), str):
            result.add(record["id"])
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Roll d100 and append the immutable result to rolls.jsonl."
    )
    parser.add_argument("--id", required=True, help="Stable unique roll id.")
    parser.add_argument("--scene-id", default=None)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument(
        "--scope", required=True, choices=("execution", "reaction", "arrangement")
    )
    parser.add_argument("--stakes", required=True)
    parser.add_argument("--difficulty", type=int, required=True)
    parser.add_argument("--character-score", type=int, choices=range(0, 11))
    parser.add_argument(
        "--modifier", action="append", default=[], type=parse_modifier,
        help="Additional modifier in source=integer form; repeat when needed.",
    )
    parser.add_argument("--event-id", default=None)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    journal = args.journal.resolve()
    if args.difficulty < 1 or args.difficulty > 100:
        raise SystemExit("difficulty must be between 1 and 100")
    try:
        ids = existing_ids(journal)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.id in ids:
        raise SystemExit(f"roll id already exists: {args.id}")

    modifiers = list(args.modifier)
    if args.character_score is not None:
        modifiers.append(
            {
                "source": "in_character_score",
                "value": character_modifier(args.character_score),
            }
        )

    natural = secrets.randbelow(100) + 1
    modified = natural + sum(int(item["value"]) for item in modifiers)
    critical = "critical_low" if natural == 1 else "critical_high" if natural == 100 else None
    record = {
        "id": args.id,
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "scene_id": args.scene_id,
        "subject": args.subject,
        "intent": args.intent,
        "scope": args.scope,
        "stakes": args.stakes,
        "difficulty": args.difficulty,
        "natural_roll": natural,
        "character_score": args.character_score,
        "modifiers": modifiers,
        "modified_result": modified,
        "passes_threshold": modified >= args.difficulty,
        "critical": critical,
        "interpretation": None,
        "event_id": args.event_id,
    }
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

