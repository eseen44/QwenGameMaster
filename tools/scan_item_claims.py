"""Gdzie w plikach AKTYWNYCH mowi sie o przedmiotach z rejestru zapasu.

POWOD ISTNIENIA. Przy retcon_000170 zabraklo dokladnie tej listy. Poprawiono rejestr,
a cztery inne pliki dalej twierdzily, ze porcje tlumiace rozklad czekaja na stole:
ocena gatunkowa w companions/spy-series.yaml, kolejka i nota w companions/webber-network.yaml
oraz OTWARTY lead w planning/lucan-leads.yaml. Jeden z tych zapisow stal kilkanascie linii
pod wlasnym blokiem `done`. Trzy tury pozniej narrator polozyl graczowi na stole srodek,
ktorego nie ma - nie z pamieci, tylko z pliku.

CZEGO TO NARZEDZIE NIE ROBI. Nie interpretuje, nie uogolnia i nie proponuje poprawek.
Nie zna sie na tym, czy zdanie mowi o stanie dzisiejszym, czy o ocenie sprzed stu tur -
to rozstrzyga czlowiek. Wypisuje miejsca do przeczytania, i to jest cala jego rola.
Kazde uogolnienie ("ten przedmiot zawsze daje ten skutek") byloby ustanawianiem mechaniki,
ktorej nikt nie zatwierdzil.

Uruchomienie:
    python tools/scan_item_claims.py                      # wszystkie przedmioty
    python tools/scan_item_claims.py --consumed-only      # tylko zuzyte (najgrozniejsze)
    python tools/scan_item_claims.py decay_suppressing_vial
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
RESOURCES = CAMPAIGN / "state" / "resources.yaml"

# Drzewa czytane przy stole. Dziennik i transakcje sa slad audytowym - zapis sprzed stu tur
# JEST tam poprawny i nie ma go po co zglaszac.
ACTIVE_DIRS = ("player", "companions", "planning", "state", "context", "entities", "locations")
SKIP_PARTS = ("journal", "migration", "snapshots", "__pycache__")


def load_items() -> dict[str, dict]:
    document = yaml.safe_load(RESOURCES.read_text(encoding="utf-8")) or {}
    items: dict[str, dict] = {}
    for cache in document.get("caches") or []:
        for entry in cache.get("contents") or []:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                items[entry["id"]] = entry
    return items


def active_files() -> list[Path]:
    files: list[Path] = []
    for name in ACTIVE_DIRS:
        base = CAMPAIGN / name
        if not base.is_dir():
            continue
        for path in base.rglob("*.yaml"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def scan(items: dict[str, dict], wanted: list[str], consumed_only: bool) -> int:
    targets = {
        item_id: entry for item_id, entry in items.items()
        if (not wanted or item_id in wanted)
        and (not consumed_only or entry.get("status") == "consumed")
    }
    if not targets:
        print("brak przedmiotow pasujacych do zapytania")
        return 0

    files = active_files()
    print(f"rejestr: {len(items)} przedmiotow | szukane: {len(targets)} | plikow aktywnych: {len(files)}")
    print()

    total = 0
    for item_id, entry in sorted(targets.items()):
        quantity = entry.get("quantity")
        status = entry.get("status", "available")
        consumed = entry.get("consumed_event_id")
        head = f"{item_id}  [quantity: {quantity}, status: {status}"
        head += f", zuzyty w {consumed}]" if consumed else "]"
        print(head)

        hits = 0
        for path in files:
            if path == RESOURCES:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(lines, 1):
                if item_id in line:
                    rel = path.relative_to(ROOT).as_posix()
                    print(f"    {rel}:{number}  {line.strip()[:120]}")
                    hits += 1
        if not hits:
            print("    (poza rejestrem nikt o nim nie mowi)")
        total += hits
        print()

    print(f"razem {total} wystapien poza rejestrem")
    if consumed_only and total:
        print("UWAGA: to sa przedmioty ZUZYTE. Kazde z tych zdan trzeba przeczytac i ustalic,")
        print("czy opisuje stan dzisiejszy, czy ocene historyczna - ta druga potrzebuje daty.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("items", nargs="*", help="identyfikatory przedmiotow; puste = wszystkie")
    parser.add_argument("--consumed-only", action="store_true",
                        help="tylko przedmioty oznaczone jako zuzyte")
    args = parser.parse_args()
    return scan(load_items(), args.items, args.consumed_only)


if __name__ == "__main__":
    sys.exit(main())
