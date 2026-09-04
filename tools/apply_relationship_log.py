"""Wpisuje odtworzone ruchy osi do kart relacji. Jednorazowa migracja.

Ruchy zebrano z dziennika (piecioro czytelnikow po wycinku tur) i przepuszczono przez
adwersarialna weryfikacje: z 50 propozycji 6 obalono, w 7 skorygowano sile. Kazdy przyjety
ruch cytuje konkretne zdarzenie i przytacza z niego dowod.

CZEGO TEN SKRYPT NIE ROBI. Nie nadpisuje pola `axes`. Suma znalezionych ruchow SATURUJE osie
(cooperation 62 -> 100, judgment_confidence 88 -> 98), a to jest artefakt zrodla, nie stan
relacji: dziennik zapisuje, co postac dla Lucana ZROBILA, i prawie nie zapisuje odmow -
a te istnieja w kanonie (odmowa przyjecia nazwiska urzednika t_122, odmowa kustodii glejtu
t_036) i przecza wartosci skrajnej, tak samo jak portrayal.priorities_in_order Seraphiny,
gdzie Lucan jest czwarty. Wyliczone wartosci laduja WIEC OBOK, w polu
`axes_reconstructed_2026_09_04`, ze statusem needs_player_review.
Log jest kanonem, bo jest udowodniony. Liczby nie sa, bo wymagaja decyzji.

Uruchomienie:  python tools/apply_relationship_log.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "campaigns" / "lucan" / "relationships"
WYNIK = Path(
    "C:/Users/janr/.claude/projects/C--Projects-QwenGameMaster"
    "/4fd42bf8-fc9f-482e-b974-04df9cb5be5e/workflows/karty-wynik.json"
)

PLIKI = {"seraphine": "seraphine--lucan.yaml", "varkhen": "varkhen--lucan.yaml"}
STAN_NA = {"seraphine": 38, "varkhen": 54}

NOTA = (
    "ODTWORZONE 2026-09-04 z dziennika, kazdy ruch z cytowaniem zdarzenia. Karta stala {stara} "
    "tur w tyle, bo nikt jej nie prowadzil. Ruchy zebralo piecioro czytelnikow dziennika, po "
    "wycinku tur, i przeszly adwersarialna weryfikacje: z 50 propozycji 6 obalono (wnioski "
    "z ogolnego przebiegu zamiast z czynu, ruchy WIEDZY zamiast relacji, odwrotny kierunek), "
    "a w 7 skorygowano sile. "
    "UWAGA O STRONNICZOSCI, WAZNA PRZY KALIBRACJI: suma znalezionych ruchow SATURUJE osie, "
    "a to jest artefakt zrodla, nie stan relacji. Dziennik zapisuje, CO ta postac dla Lucana "
    "ZROBILA, i prawie nie zapisuje odmow - a te istnieja w kanonie (odmowa przyjecia nazwiska "
    "urzednika w t_122, odmowa kustodii glejtu w t_036) i przecza wartosci skrajnej, tak samo "
    "jak portrayal.priorities_in_order Seraphiny, gdzie Lucan jest czwarty, a nie pierwszy. "
    "DLATEGO POLE axes ZOSTAJE NIETKNIETE do kalibracji przez gracza, a wyliczone wartosci "
    "leza obok. Log jest kanonem, bo jest udowodniony; liczby nie sa, bo wymagaja decyzji."
)


def entry_yaml(entry: dict) -> str:
    body = yaml.safe_dump(entry, allow_unicode=True, sort_keys=False,
                          default_flow_style=False, width=4096)
    # Istniejace wpisy w kartach sa WCIETE DWIEMA SPACJAMI - wpis od zera lamie liste.
    lines = body.rstrip().split(chr(10))
    return "  - " + (chr(10) + "    ").join(lines)


def insert_after_block(text: str, key: str, addition: str) -> str:
    """Wstawia addition na koncu bloku `key:`, przed nastepnym kluczem najwyzszego poziomu."""
    start = text.index(key)
    match = re.search(r"(?m)^[A-Za-z_][\w]*:", text[start + len(key):])
    end = start + len(key) + (match.start() if match else len(text) - start - len(key))
    return text[:end] + addition + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wynik = json.loads(WYNIK.read_text(encoding="utf-8"))
    for karta, nazwa in PLIKI.items():
        path = CARDS / nazwa
        text = path.read_text(encoding="utf-8-sig")
        dane = wynik[karta]
        stara = 235 - STAN_NA[karta]

        wpisy = "\n".join(entry_yaml(e) for e in dane["log"]) + "\n"
        if "axis_change_log:" in text:
            text = insert_after_block(text, "axis_change_log:", wpisy)
        else:
            text = text.replace("history:", "axis_change_log:\n" + wpisy + "history:", 1)

        nota = NOTA.format(stara=stara)
        blok = (
            "axes_reconstructed_2026_09_04: "
            + yaml.safe_dump(dane["axes"], allow_unicode=True, sort_keys=False,
                             default_flow_style=True, width=4096).strip()
            + "\naxes_calibration_status: needs_player_review\n"
            + "axes_reconstruction_note: >-\n"
            + textwrap.indent(textwrap.fill(nota, width=94), "  ")
            + "\n"
        )
        anchor = re.search(r"(?m)^axes: \{[^\n]*\}\n", text)
        if not anchor:
            print(f"[BLAD] {nazwa}: nie znalazlem pola axes")
            return 1
        text = text[: anchor.end()] + blok + text[anchor.end():]
        text = re.sub(r"(?m)^last_event_id: .*$",
                      "last_event_id: event_turn_interlude_235", text)

        document = yaml.safe_load(text)
        assert document["axes"] == {"cooperation": 62, "judgment_confidence": 88,
                                    "discretion_trust": 38, "personal_regard": 42} \
            or karta == "varkhen", "pole axes nie moze byc ruszone"
        print(f"{nazwa}: log {len(document.get('axis_change_log') or [])} wpisow "
              f"| axes {document['axes']} (NIETKNIETE) "
              f"| wyliczone {document['axes_reconstructed_2026_09_04']}")
        if not args.dry_run:
            path.write_text(text, encoding="utf-8", newline="\n")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
    return 0


if __name__ == "__main__":
    sys.exit(main())
