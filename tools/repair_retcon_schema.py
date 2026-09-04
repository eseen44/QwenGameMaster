"""Naprawa SCHEMATU korpusu retconow. Zadne slowo tresci nie zmienia sie ani nie ginie.

Trzy klasy dlugu, ktore linter zglaszal jako blokujace, i ktore da sie naprawic bez
wymyslania czegokolwiek:

1. BRAK approved_by w retconach 133-140 (osiem wpisow). Proweniencja NIE BYLA zgubiona -
   byla zapisana w polu `reason`, tylko nie w tym polu, w ktorym jej szuka walidator.
   Kazdy z osmiu mowi to w pierwszych slowach: "DEKLARACJA GRACZA DO SYSTEMU W NAWIASIE",
   "KOREKTA KANONU GRACZA W NAWIASIE", "COFNIECIE NA ZADANIE GRACZA", "REKLAMACJA GRACZA",
   "DOPRECYZOWANIE GRACZA W NAWIASIE" - wszystkie osiem z 2026-09-03. Wartosc jest wiec
   WYPROWADZANA Z WLASNEJ TRESCI WPISU, nie zgadywana: obecnosc slowa "NAWIASIE" wybiera
   miedzy `player_declaration_2026_09_03_bracket` i `player_declaration_2026_09_03`,
   dokladnie jak w istniejacej konwencji (retcon_000132 ma _bracket, retcon_000141 nie).
   Skrypt ODMAWIA wypelnienia pola, jesli w reason nie ma jawnego sladu gracza - wtedy
   zostawia brak, bo wpisanie tam "user" bez podstawy byloby falszowaniem proweniencji.

2. supersedes JAKO NAPIS w retconach 15-18. Poprawka jest czysto strukturalna: napis
   wchodzi do jednoelementowej listy. Wartosc zostaje znak w znak.

3. state_refs wskazujace na KATALOG albo WZORZEC ("campaigns/lucan/state/*",
   ".../instances/") w retconach 33, 105 i 108. Tego skrypt NIE rusza - to nie defekt
   danych, a brak w moim linterze, ktory zna tylko pojedyncze pliki. Naprawiane w
   retcon_lint.py, nie tutaj.

Uruchomienie:  python tools/repair_retcon_schema.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RETCONS = ROOT / "campaigns" / "lucan" / "journal" / "retcons.jsonl"

# Slady gracza w polu reason. Kolejnosc bez znaczenia - liczy sie samo trafienie.
SLADY_GRACZA = (
    "DEKLARACJA GRACZA", "KOREKTA KANONU GRACZA", "NA ZADANIE GRACZA", "REKLAMACJA GRACZA",
    "DOPRECYZOWANIE GRACZA", "NA ZYCZENIE GRACZA", "KOREKTA GRACZA",
)
DATA = re.compile(r"(20\d\d)-(\d\d)-(\d\d)")


def provenance(reason: str) -> str | None:
    """Wyprowadza wartosc approved_by z tresci wpisu albo zwraca None."""
    head = reason[:200].upper()
    if not any(slad in head for slad in SLADY_GRACZA):
        return None
    data = DATA.search(reason[:200])
    if not data:
        return None
    stamp = "-".join(data.groups()).replace("-", "_")
    return f"player_declaration_{stamp}" + ("_bracket" if "NAWIASIE" in head else "")


def words(node: object) -> collections.Counter:
    if isinstance(node, str):
        return collections.Counter(re.findall(r"\w+", node))
    if isinstance(node, dict):
        total = collections.Counter()
        for key, value in node.items():
            total += words(key) + words(value)
        return total
    if isinstance(node, list):
        total = collections.Counter()
        for value in node:
            total += words(value)
        return total
    return collections.Counter()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lines = [line for line in RETCONS.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    rows = [json.loads(line) for line in lines]
    przed = words(rows)

    uzupelnione, opakowane, odmowy = [], [], []
    for row in rows:
        if not row.get("approved_by"):
            wartosc = provenance(row.get("reason") or "")
            if wartosc:
                row["approved_by"] = wartosc
                row["approved_by_source"] = (
                    "WYPROWADZONE 2026-09-04 z pola reason tego samego wpisu, ktore nazywa "
                    "zrodlo wprost; pole bylo puste, proweniencja nie byla zgubiona. "
                    "Patrz retcon_000149.")
                uzupelnione.append((row["id"], wartosc))
            else:
                odmowy.append(row["id"])

        supersedes = row.get("supersedes")
        if isinstance(supersedes, str):
            row["supersedes"] = [supersedes]
            opakowane.append(row["id"])

    po = words(rows)
    brak = przed - po
    if brak:
        print(f"[BLAD] naprawa gubi tresc: {dict(list(brak.items())[:6])}")
        return 1

    print(f"approved_by uzupelnione: {len(uzupelnione)}")
    for rid, wartosc in uzupelnione:
        print(f"   {rid} -> {wartosc}")
    print(f"supersedes opakowane w liste: {len(opakowane)} ({', '.join(opakowane)})")
    if odmowy:
        print(f"ODMOWA wypelnienia (brak sladu gracza w reason, zostaje puste): "
              f"{', '.join(odmowy)}")
    print("kontrola slow: zadne slowo nie ginie")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    RETCONS.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8", newline="\n")
    print(f"\nzapisane: {RETCONS.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
