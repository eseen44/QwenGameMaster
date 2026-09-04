"""Dziennik dowiaduje sie, ze jest uchylony.

Pole `superseded_by` istnieje w schemacie wszystkich 235 wpisow events.jsonl i jest
wypelnione w PIECIU, mimo ze retcony wskazuja 57 zdarzen jako uchylone. Skutek: czytajac
dziennik, nie widzi sie, ze wpis jest czesciowo albo calkowicie niewazny - a `recall` i brief
podaja takie wpisy jako zwykly kanon. Retcon jest zrodlem nr 1 (system/canon-policy.md),
wiec kazde uchylenie MUSI byc widoczne z tej strony, ktora sie czyta.

Dane sa juz w repo - w `retcons.jsonl#supersedes`. Ten skrypt tylko je przenosi:
  - `superseded_by`: id retconu (string przy jednym, lista przy wielu - zgodnie z zapisem
    pieciu wpisow, ktore ktos wypelnil recznie),
  - `superseded_aspects`: DOKLADNE wpisy z `supersedes`, ktore nazwaly to zdarzenie.
    To wazne, bo retcon czesto uchyla ASPEKT ("event_turn_interlude_233#summary.1"),
    nie caly wpis, i roznica miedzy "caly wpis niewazny" a "jedno zdanie poprawione"
    jest w tej kampanii istotna.

Nic nie jest nadpisywane: proza, operacje i czas zostaja bez zmiany, dopisywane sa wylacznie
dwa pola ksiegowe (tools/journal_guard.py#BOOKKEEPING_KEYS). Skrypt jest idempotentny.

Uruchomienie:  python tools/backfill_superseded.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "campaigns/lucan/journal/events.jsonl"
RETCONS = ROOT / "campaigns/lucan/journal/retcons.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    events = [json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    retcons = [json.loads(line) for line in RETCONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    known = {event["id"] for event in events}

    by_event: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    unknown: list[tuple[str, str]] = []
    for retcon in retcons:
        for entry in retcon.get("supersedes") or []:
            if not isinstance(entry, str):
                continue
            base = entry.split("#")[0].strip()
            if not base.startswith(("event_", "milestone_")):
                continue          # refy do plikow i sekcji, nie do zdarzen
            if base in known:
                by_event[base].append((retcon["id"], entry))
            else:
                unknown.append((retcon["id"], entry))

    touched = 0
    for event in events:
        pairs = by_event.get(event["id"])
        if not pairs:
            continue
        retcon_ids = sorted({retcon_id for retcon_id, _ in pairs})
        aspects = sorted({aspect for _, aspect in pairs})
        marker = retcon_ids[0] if len(retcon_ids) == 1 else retcon_ids
        # ZAKRES UCHYLENIA. 39 z 57 zdarzen jest wskazanych WYLACZNIE przez zakotwiczenie
        # ("event#summary.1"), czyli poprawione jest jedno zdanie, a nie caly wpis. Plaskie
        # "superseded_by" kazaloby czytelnikowi wyrzucic cala ture - to byloby przeklamanie
        # w druga strone, wiec zakres jest zapisany wprost.
        anchored = [a for _, a in pairs if "#" in a]
        if len(anchored) == len(pairs):
            scope = "aspect"
        elif not anchored:
            scope = "whole"
        else:
            scope = "mixed"
        if (event.get("superseded_by") == marker
                and event.get("superseded_aspects") == aspects
                and event.get("supersession_scope") == scope):
            continue
        event["superseded_by"] = marker
        event["superseded_aspects"] = aspects
        event["supersession_scope"] = scope
        touched += 1

    wielokrotne = {e: len({r for r, _ in p}) for e, p in by_event.items() if len({r for r, _ in p}) > 1}
    print(f"zdarzen wskazanych jako uchylone: {len(by_event)}")
    print(f"wpisow do oznaczenia: {touched}")
    print(f"uchylonych wiecej niz jednym retconem: {len(wielokrotne)} {list(wielokrotne)[:4]}")
    czesciowe = sum(1 for pairs in by_event.values() if all("#" in a for _, a in pairs))
    print(f"uchylonych tylko W ASPEKCIE (kazde wskazanie z zakotwiczeniem): {czesciowe}")
    if unknown:
        print(f"wskazania na zdarzenia, ktorych NIE MA w dzienniku: {len(unknown)}")
        for retcon_id, entry in unknown[:6]:
            print(f"  - {retcon_id} -> {entry}")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    EVENTS.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"\nzapisane: {EVENTS.relative_to(ROOT).as_posix()}, {len(events)} wpisow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
