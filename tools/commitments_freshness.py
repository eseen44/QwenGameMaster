"""Od kiedy nikt nie ruszyl zobowiazania, celu ani tajemnicy.

POWOD ISTNIENIA. W state/obligations.yaml, objectives.yaml i secrets.yaml mieszkaja TERMINY
I OBIETNICE - rzeczy, ktorych narratorowi nie wolno wymyslac (CLAUDE.md pkt 5). Kazdy wpis
ma `source_event_id`, czyli KIEDY POWSTAL, i zaden nie ma informacji, kiedy ostatnio
cokolwiek sie z nim dzialo. Po 276 turach roznica miedzy jednym a drugim jest cala tresc:
zobowiazanie sprzed dwustu tur i zobowiazanie sprzed piatej wygladaja w pliku identycznie.

DLACZEGO NIE ZAPISUJEMY TEGO W PLIKU. Bo to jest liczba WYPROWADZALNA z dziennika, a kazda
wyprowadzalna liczba przepisana do stanu to kolejna kopia do rozjechania - dokladnie ta
awaria, ktora dala retcon_000170 przy zapasie i ktora zdjelo `upkeep_ref` przy zawisaku.
Swiezosc liczy sie NA ZADANIE, ze zrodla, ktore i tak jest prawda: z transakcji.

CO TO ZNACZY "RUSZONE". Ze identyfikator wpisu wystapil w zacommitowanej transakcji tury.
To jest proxy, nie pomiar uwagi gracza - i tak jest nazwane w wyjsciu.

Uruchomienie:
    python tools/commitments_freshness.py
    python tools/commitments_freshness.py --older-than 50
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
STATE = CAMPAIGN / "state"
TRANSACTIONS = CAMPAIGN / "journal" / "transactions"

ZRODLA = {
    "obligations.yaml": ("obligations",),
    "objectives.yaml": ("player_declared", "long_term_context", "external_pressures"),
    "secrets.yaml": None,  # struktura nieregularna - zbieramy kazde pole 'id'
}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {} if path.is_file() else {}


def zbierz_id(node: object, out: set[str]) -> None:
    if isinstance(node, dict):
        wartosc = node.get("id")
        if isinstance(wartosc, str) and wartosc.startswith(("obligation_", "objective_", "secret_",
                                                            "cover_", "fact_")):
            out.add(wartosc)
        for value in node.values():
            zbierz_id(value, out)
    elif isinstance(node, list):
        for value in node:
            zbierz_id(value, out)


def identyfikatory() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for nazwa in ZRODLA:
        ids: set[str] = set()
        zbierz_id(load(STATE / nazwa), ids)
        if ids:
            out[nazwa] = ids
    return out


def numer(nazwa: str) -> int:
    m = re.search(r"(\d+)", nazwa)
    return int(m.group(1)) if m else -1


def ostatnie_wystapienia(ids: set[str]) -> dict[str, int]:
    """{id: numer najwyzszej tury, w ktorej sie pojawil}. Jeden przebieg po transakcjach."""
    wynik: dict[str, int] = {}
    for path in sorted(TRANSACTIONS.glob("*.yaml"), key=lambda p: numer(p.name)):
        tura = numer(path.name)
        if tura < 0:
            continue
        tekst = path.read_text(encoding="utf-8", errors="replace")
        for item_id in ids:
            if item_id in tekst:
                wynik[item_id] = tura
    return wynik


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--older-than", type=int, default=None,
                        help="pokaz tylko wpisy nieruszone od tylu tur")
    args = parser.parse_args()

    zrodla = identyfikatory()
    wszystkie = set().union(*zrodla.values()) if zrodla else set()
    if not wszystkie:
        print("brak wpisow do sprawdzenia")
        return 0

    biezaca = numer(str(load(STATE / "time.yaml").get("last_event_id") or ""))
    ostatnie = ostatnie_wystapienia(wszystkie)

    print(f"biezaca tura: {biezaca} | wpisow: {len(wszystkie)}")
    print('"ruszone" = identyfikator wystapil w zacommitowanej transakcji tury (proxy)')
    print()
    for nazwa, ids in sorted(zrodla.items()):
        print(f"--- {nazwa} ---")
        wiersze = []
        for item_id in sorted(ids):
            tura = ostatnie.get(item_id)
            wiek = (biezaca - tura) if (tura is not None and biezaca >= 0) else None
            wiersze.append((wiek if wiek is not None else 10**9, item_id, tura, wiek))
        for _, item_id, tura, wiek in sorted(wiersze, reverse=True):
            if args.older_than is not None and (wiek is None or wiek < args.older_than):
                continue
            if tura is None:
                print(f"  {item_id:<62} NIGDY nie wystapil w transakcji")
            else:
                print(f"  {item_id:<62} ostatnio t_{tura} ({wiek} tur temu)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
