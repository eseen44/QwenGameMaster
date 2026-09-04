"""Kontrola korpusu retconow. Etap 9.

142 retcony sa formalnie kanonem NR 1 (system/canon-policy.md) i do 2026-09-04 nie mialy ani
jednej kontroli zawartosci - validate_project.py wymienial retcons.jsonl tylko w
REQUIRED_PATHS, a validate_jsonl sprawdzal wylacznie "czy linia jest JSON-em i ma id".
Odczyt korpusu (2026-09-04) pokazal: 107 wpisow z klauzula normatywna, 51 klauzul zyjacych
WYLACZNIE w dzienniku, 43 sprzecznosci miedzy retconami, z czego 25 bez zadeklarowanego
uchylenia - czyli lancuch "co dzis obowiazuje" jest maszynowo niewidoczny.

ZAPADKA. Naruszen historycznych jest za duzo, zeby blokowac (od 4 do 90 na kontrole), a
walidator swiecacy na czerwono bez przerwy jest ignorowany. Dlatego:
  - wpisy o numerze <= BASELINE sa DLUGIEM: raportowane, nigdy blokujace,
  - wpisy NOWSZE musza przejsc kontrole blokujace.
Dlug maleje tylko wtedy, gdy ktos go swiadomie splaci; nowy dlug nie powstanie.

Uruchomienie:
    python tools/retcon_lint.py            # dlug + stan nowych wpisow
    python tools/retcon_lint.py --new-only  # tylko wpisy powyzej baseline (tryb bramki)
    python tools/retcon_lint.py --debt       # pelna lista dlugu, per kontrola
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RETCONS = ROOT / "campaigns/lucan/journal/retcons.jsonl"
EVENTS = ROOT / "campaigns/lucan/journal/events.jsonl"

# Ostatni wpis istniejacy PRZED wprowadzeniem kontroli (korpus mial 142 wpisy). Wpisy do tego numeru wlacznie sa
# dlugiem historycznym. PODNOSZENIE TEJ LICZBY jest cofaniem zapadki - rob to wylacznie po
# splaceniu dlugu, nigdy zeby uciszyc alarm.
BASELINE = 142

# Pole z trescia korekty. Korpus uzywa dwoch nazw; "replacement" jest wersja przewazajaca.
BODY_FIELDS = ("replacement", "correction", "state_correction")

REQUIRED = ("id", "timestamp", "reason", "approved_by")


def number(retcon_id: str) -> int:
    match = re.search(r"(\d+)", retcon_id or "")
    return int(match.group(1)) if match else -1


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def check(retcons: list[dict], events: set[str]) -> dict[str, list[tuple[str, str]]]:
    """Zwraca {nazwa_kontroli: [(id_wpisu, opis_naruszenia)]}."""
    problems: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    ids = {r.get("id") for r in retcons}
    seen_timestamps: dict[str, str] = {}
    previous_stamp: dt.datetime | None = None

    for retcon in retcons:
        rid = retcon.get("id") or "(bez id)"

        for field in REQUIRED:
            if not retcon.get(field):
                problems["pola_wymagane"].append((rid, f"brak pola {field}"))

        if not any(retcon.get(field) for field in BODY_FIELDS):
            problems["tresc_korekty"].append(
                (rid, f"brak tresci korekty - zadne z pol {', '.join(BODY_FIELDS)}"))

        supersedes = retcon.get("supersedes")
        if supersedes is not None and not isinstance(supersedes, list):
            problems["supersedes_lista"].append((rid, f"supersedes jest {type(supersedes).__name__}, nie lista"))
        for entry in supersedes if isinstance(supersedes, list) else []:
            if not isinstance(entry, str):
                problems["supersedes_lista"].append((rid, "element supersedes nie jest napisem"))
                continue
            base = entry.split("#")[0].strip()
            if base.startswith("retcon_") and base not in ids:
                problems["supersedes_wskazuje_w_nicosc"].append((rid, f"{base} nie istnieje w korpusie"))
            elif base.startswith("event_") and base not in events:
                if not any(e.startswith(base) for e in events):
                    problems["supersedes_wskazuje_w_nicosc"].append((rid, f"{base} nie istnieje w dzienniku"))
            elif "/" in base and not (ROOT / base).is_file():
                # is_file(), nie exists(): katalog przechodzil jako poprawny ref i moj
                # wlasny retcon_000144 przemknal przez te bramke z pseudo-sciezka
                # "campaigns/lucan/#provenance:..." - bo katalog campaigns/lucan istnieje.
                powod = "to katalog, nie plik" if (ROOT / base).is_dir() else "nie istnieje"
                problems["supersedes_wskazuje_w_nicosc"].append((rid, f"{base} - {powod}"))
            if base.startswith("retcon_") and "#" in entry:
                problems["kotwica_na_retconie"].append(
                    (rid, f"{entry} - retcony nie maja podkluczy, wiec ta kotwica nie rozwiazuje sie nigdy"))

        for ref in retcon.get("state_refs_updated") or []:
            if isinstance(ref, str) and "/" in ref.split("#")[0] and not (ROOT / ref.split("#")[0]).is_file():
                problems["state_refs_wskazuje_w_nicosc"].append((rid, f"{ref} nie istnieje"))

        stamp = retcon.get("timestamp")
        if isinstance(stamp, str):
            if stamp in seen_timestamps:
                problems["timestamp_powtorzony"].append((rid, f"ten sam czas co {seen_timestamps[stamp]}"))
            seen_timestamps[stamp] = rid
            try:
                parsed = dt.datetime.fromisoformat(stamp)
            except ValueError:
                problems["timestamp_nieparsowalny"].append((rid, stamp))
            else:
                # Czas KAMPANII to sierpien 2026; wpisy powstaja realnie wrzesien 2026+.
                # Timestamp w czasie kampanii uniewaznia regule "wygrywa pozniejszy",
                # uzyta wprost w retcon_000106.
                if parsed.year == 2026 and parsed.month < 9:
                    problems["timestamp_w_czasie_kampanii"].append((rid, stamp))
                elif previous_stamp and parsed < previous_stamp:
                    problems["timestamp_nierosnacy"].append((rid, f"{stamp} < poprzedni"))
                if parsed.tzinfo:
                    previous_stamp = parsed if not previous_stamp or parsed > previous_stamp else previous_stamp

    return problems


BLOCKING = {
    "pola_wymagane", "tresc_korekty", "supersedes_lista",
    "supersedes_wskazuje_w_nicosc", "state_refs_wskazuje_w_nicosc",
    "timestamp_nieparsowalny", "timestamp_powtorzony", "timestamp_w_czasie_kampanii",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-only", action="store_true", help="tryb bramki: tylko wpisy powyzej baseline")
    parser.add_argument("--debt", action="store_true", help="pelna lista dlugu historycznego")
    args = parser.parse_args()

    retcons = load(RETCONS)
    events = {e.get("id") for e in load(EVENTS) if e.get("id")}
    problems = check(retcons, events)

    debt: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    fresh: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for name, rows in problems.items():
        for rid, detail in rows:
            (fresh if number(rid) > BASELINE else debt)[name].append((rid, detail))

    print(f"korpus: {len(retcons)} retconow, baseline = retcon_{BASELINE:06} "
          f"(wpisy do tego numeru sa dlugiem historycznym)")
    print()

    if not args.new_only:
        print("DLUG HISTORYCZNY (raportowany, nigdy blokujacy):")
        if not debt:
            print("  brak")
        for name in sorted(debt, key=lambda n: -len(debt[n])):
            rows = debt[name]
            flag = "BLOK" if name in BLOCKING else "uwaga"
            print(f"  [{flag:5}] {name:<34} {len(rows)}")
            if args.debt:
                for rid, detail in rows:
                    print(f"           {rid}: {detail}")
        print()

    blocking_fresh = {n: r for n, r in fresh.items() if n in BLOCKING}
    print(f"WPISY NOWE (powyzej baseline): {sum(1 for r in retcons if number(r.get('id', '')) > BASELINE)}")
    if blocking_fresh:
        print()
        print(f"[BLAD] {sum(len(r) for r in blocking_fresh.values())} naruszen w nowych wpisach:")
        for name, rows in sorted(blocking_fresh.items()):
            for rid, detail in rows:
                print(f"  - {name}: {rid}: {detail}")
        return 1
    for name, rows in sorted(fresh.items()):
        for rid, detail in rows:
            print(f"  [uwaga] {name}: {rid}: {detail}")
    print()
    print("[OK] retcon_lint: nowe wpisy bez naruszen blokujacych")
    return 0


if __name__ == "__main__":
    sys.exit(main())
