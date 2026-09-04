"""Wynosi uzasadnienia zobowiazan z pliku wczytywanego co ture. Domkniecie etapu 8.

SKILL-gramy.md i sam audyt mowia to samo: `state/obligations.yaml` i `state/objectives.yaml`
sa w active_refs, czyli wchodza do KAZDEJ tury, i maja trzymac STRUKTURE - id, status,
zobowiazanie, jednolinijkowy warunek - a uzasadnienia maja lezec w magazynie. Zmierzone:
57% objetosci obligations.yaml to napisy dluzsze niz 200 znakow.

Osiem pol jest uzasadnieniem albo szczegolem sekwencji, nie stanem potrzebnym co ture:
player_position, order_status, sequence, declared_plan, disclosed_to_neris,
what_the_risk_actually_is, not_triggered_by, note_open_but_no_deadline.

PRZENIESIENIE JEST DOSLOWNE. Zadne zdanie nie jest skracane ani streszczane - to jest ta sama
zasada co przy rozbiciu magazynu uzasadnien i przy rozdzieleniu summary: maszyna przenosi,
nie przepisuje. W zobowiazaniu zostaje `rationale_ref` wskazujacy plik i klucz.

Gwarancja: po migracji wielozbior slow (plik zobowiazan + plik uzasadnien) zawiera kazde
slowo oryginalu, liczone na SPARSOWANEJ tresci.

Uruchomienie:  python tools/split_obligations_rationale.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "campaigns" / "lucan" / "state" / "obligations.yaml"
TARGET = ROOT / "campaigns" / "lucan" / "planning" / "obligations-rationale.yaml"

# Pola uzasadnienia. `commitment`, `status`, `key_constraint` i identyfikatory ZOSTAJA -
# tura ich potrzebuje.
RATIONALE_FIELDS = (
    "player_position", "order_status", "sequence", "declared_plan", "disclosed_to_neris",
    "what_the_risk_actually_is", "not_triggered_by", "note_open_but_no_deadline",
)


def parsed_words(node: object) -> collections.Counter:
    if isinstance(node, str):
        return collections.Counter(re.findall(r"\w+", node))
    if isinstance(node, dict):
        total = collections.Counter()
        for key, value in node.items():
            total += parsed_words(key) + parsed_words(value)
        return total
    if isinstance(node, list):
        total = collections.Counter()
        for value in node:
            total += parsed_words(value)
        return total
    return collections.Counter() if node is None else collections.Counter(re.findall(r"\w+", str(node)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    original = yaml.safe_load(SOURCE.read_text(encoding="utf-8-sig"))
    przed = SOURCE.stat().st_size

    wyniesione: dict[str, dict] = {}
    for obligation in original.get("obligations") or []:
        if not isinstance(obligation, dict):
            continue
        oid = obligation.get("id")
        moved = {field: obligation.pop(field) for field in RATIONALE_FIELDS if field in obligation}
        if not moved:
            continue
        wyniesione[oid] = moved
        existing = obligation.get("rationale_ref")
        pointer = f"campaigns/lucan/planning/obligations-rationale.yaml#{oid}"
        obligation["rationale_ref"] = (
            [existing, pointer] if isinstance(existing, str) else
            ((existing or []) + [pointer]) if isinstance(existing, list) else pointer
        )

    if not wyniesione:
        print("nic do wyniesienia - plik jest juz odchudzony")
        return 0

    rationale_doc = {
        "schema_version": 1,
        "id": "obligations_rationale",
        "object_type": "rationale_store",
        "part_of": "campaigns/lucan/state/obligations.yaml",
        "split_note": (
            "Wyniesione 2026-09-04 z state/obligations.yaml, ktory jest w active_refs i wchodzi "
            "do KAZDEJ tury. Tresc przeniesiona 1:1, bez skracania. W zobowiazaniu zostaly "
            "id, status, commitment, key_constraint i source_event_id - to, czego tura "
            "potrzebuje; tu leza uzasadnienia, sekwencje i zastrzezenia. Wczytuj przy "
            "planowaniu albo gdy rozmowa dotyka konkretnego zobowiazania."
        ),
        "obligations": wyniesione,
    }

    nowy_source = yaml.safe_dump(original, allow_unicode=True, sort_keys=False, width=100)
    nowy_target = yaml.safe_dump(rationale_doc, allow_unicode=True, sort_keys=False, width=100)

    brak = parsed_words(yaml.safe_load(SOURCE.read_text(encoding="utf-8-sig"))) - (
        parsed_words(yaml.safe_load(nowy_source)) + parsed_words(yaml.safe_load(nowy_target)))
    if brak:
        print(f"[BLAD] migracja zgubilaby {sum(brak.values())} slow: {dict(list(brak.items())[:8])}")
        return 1
    print("kontrola slow: zadne slowo nie ginie")
    print(f"obligations.yaml: {przed} B -> {len(nowy_source.encode('utf-8'))} B")
    print(f"nowy plik uzasadnien: {len(nowy_target.encode('utf-8'))} B, "
          f"{len(wyniesione)} zobowiazan, pol: {sum(len(v) for v in wyniesione.values())}")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    TARGET.write_text(nowy_target, encoding="utf-8", newline="\n")
    SOURCE.write_text(nowy_source, encoding="utf-8", newline="\n")
    print(f"\nzapisane: {TARGET.relative_to(ROOT).as_posix()} oraz {SOURCE.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
