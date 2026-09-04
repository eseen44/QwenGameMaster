"""Generuje skroty kart NPC. Etap 8.

POWOD, ZMIERZONY. Karty NPC stojacych w scenie to 68 465 B, czyli 167% calego budzetu
kontekstu - i licznik ich nie widzial do etapu 6. Sama karta Seraphiny wazy 60 680 B,
z czego `knowledge.confirmed` (91 wpisow) to 54 219 B. Wszystko, co mowi JAK JA GRAC -
portrayal, speech_traits, agenda, do_not_play, forbidden_without_source - wazy 5,9 KB.

Skrot zawiera wiec:
  - cala czesc "jak grac" 1:1 (portrayal, speech_traits, agenda, appearance, lifecycle...),
  - N NAJNOWSZYCH wpisow knowledge.confirmed w calosci (bo to one sa stanem biezacym),
  - INDEKS pozostalych: fact_id + source_event_id, po jednej linii, zeby bylo widac,
    CO postac wie, nawet gdy szczegol trzeba dociagnac z pelnej karty,
  - suspicions i false_beliefs w calosci (krotkie, a zmieniaja prowadzenie),
  - swiezosc: numer ostatniej tury na karcie wobec biezacej.

NIC NIE GINIE PRZEZ KONSTRUKCJE: skrot jest WYLICZANY, pelna karta zostaje na miejscu
i jest jedynym zrodlem prawdy. Skrot bez pelnej karty nie jest kanonem.

Uruchomienie:  python tools/build_npc_digests.py [--check] [--recent N]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "campaigns" / "lucan" / "entities" / "npcs"
DIGESTS = CARDS / "digests"
SCENE = ROOT / "campaigns" / "lucan" / "context" / "scene.yaml"

RECENT_DEFAULT = 4

# Pola "jak grac" - przenoszone do skrotu w calosci.
PLAY_FIELDS = (
    "schema_version", "id", "name", "status", "review_status", "importance", "role",
    "guild_rank", "lifecycle", "current_location_id", "current_zone_id", "location_note",
    "appearance", "relationship_ref", "portrayal", "speech_traits", "agenda",
    "open_question_she_asked", "open_question_asked", "introduced_by", "relevance_to_lucan",
    "mechanics_ref", "faction_ref",
)


def turn_number(event_id: object) -> int:
    if not isinstance(event_id, str):
        return -1
    digits = [chunk for chunk in event_id.replace("-", "_").split("_") if chunk.isdigit()]
    return int(digits[-1]) if digits else -1


def current_turn() -> int:
    try:
        scene = yaml.safe_load(SCENE.read_text(encoding="utf-8-sig")) or {}
    except (OSError, yaml.YAMLError):
        return -1
    return turn_number(scene.get("last_event_id"))


def digest_for(card: dict, recent: int, now: int) -> dict:
    out = {key: card[key] for key in PLAY_FIELDS if key in card}
    out["object_type"] = "npc_digest"
    out["full_card"] = None          # wypelniane przez wolajacego
    knowledge = card.get("knowledge") or {}
    confirmed = [entry for entry in (knowledge.get("confirmed") or []) if isinstance(entry, dict)]
    confirmed.sort(key=lambda entry: turn_number(entry.get("source_event_id")), reverse=True)

    najnowsze = confirmed[:recent]
    reszta = confirmed[recent:]
    ostatnia = turn_number(najnowsze[0].get("source_event_id")) if najnowsze else -1

    out["knowledge"] = {
        "recent_confirmed": najnowsze,
        "older_confirmed_index": [
            f"{entry.get('fact_id', '?')} <- {entry.get('source_event_id', '?')}"
            for entry in reszta
        ],
        "suspicions": knowledge.get("suspicions") or [],
        "false_beliefs": knowledge.get("false_beliefs") or [],
        "forbidden_without_source": knowledge.get("forbidden_without_source") or [],
    }
    out["freshness"] = {
        "confirmed_entries_total": len(confirmed),
        "in_digest": len(najnowsze),
        "last_fact_from_turn": ostatnia,
        "current_turn": now,
        "turns_behind": (now - ostatnia) if (now >= 0 and ostatnia >= 0) else None,
        "warning": (
            "KARTA JEST TAK SWIEZA, JAK OSTATNI DOPISEK, NIE JAK OSTATNIA TURA "
            "(retcon_000121). Wpis w knowledge.confirmed to ZDARZENIE, nie stan biezacy. "
            "Jesli turns_behind jest duze, traktuj karte jako NIEKOMPLETNA i sprawdz "
            "recall/dziennik przed pierwsza kwestia tej postaci."
        ),
    }
    out["digest_note"] = (
        "SKROT GENEROWANY - NIE EDYTUJ i NIE TRAKTUJ JAKO KANONU. Zrodlem prawdy jest pelna "
        "karta wskazana w full_card; tu leza czesc 'jak grac' 1:1, najnowsze fakty w calosci "
        "oraz INDEKS starszych (fact_id <- zdarzenie). Szczegol starszego faktu dociagnij "
        "z pelnej karty. Przebuduj: python tools/build_npc_digests.py"
    )
    return out


def build(recent: int) -> dict[Path, str]:
    now = current_turn()
    out: dict[Path, str] = {}
    for path in sorted(CARDS.glob("*.yaml")) + sorted((CARDS / "fixtures").glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        try:
            card = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        except yaml.YAMLError:
            continue
        if not isinstance(card, dict) or not card.get("id"):
            continue
        confirmed = ((card.get("knowledge") or {}).get("confirmed") or [])
        if len(confirmed) <= recent:
            continue          # karta i tak jest mala - skrot nic nie da
        digest = digest_for(card, recent, now)
        digest["full_card"] = path.relative_to(ROOT).as_posix()
        body = yaml.safe_dump(digest, allow_unicode=True, sort_keys=False, width=100)
        # SKROT, KTORY NIE ZMNIEJSZA, JEST SZUMEM. Naglowki, ostrzezenie o swiezosci
        # i nota o niekanonicznosci wazą ~1,5 KB, wiec przy malej karcie skrot potrafi byc
        # WIEKSZY od oryginalu (zmierzone na boros-keld.yaml: 3 747 B skrotu na 3 471 B
        # karty). Emitujemy tylko wtedy, gdy oszczednosc jest realna.
        PROG_OSZCZEDNOSCI = 0.75
        if len(body.encode("utf-8")) > PROG_OSZCZEDNOSCI * path.stat().st_size:
            stary = DIGESTS / f"{path.stem}.yaml"
            if stary.exists():
                stary.unlink()     # skrot przestal sie oplacac - usun, zeby nie klamal
            continue
        out[DIGESTS / f"{path.stem}.yaml"] = body
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--recent", type=int, default=RECENT_DEFAULT)
    args = parser.parse_args()

    files = build(args.recent)
    if args.check:
        stale = [path for path, body in files.items()
                 if not path.exists() or path.read_text(encoding="utf-8") != body]
        if stale:
            print(f"[BLAD] {len(stale)} skrotow kart nieaktualnych "
                  f"- uruchom: python tools/build_npc_digests.py")
            for path in stale[:8]:
                print(f"  - {path.relative_to(ROOT).as_posix()}")
            return 1
        print(f"[OK] skroty kart aktualne ({len(files)})")
        return 0

    DIGESTS.mkdir(parents=True, exist_ok=True)
    for path, body in files.items():
        path.write_text(body, encoding="utf-8", newline="\n")
    total_full = sum((ROOT / yaml.safe_load(body)["full_card"]).stat().st_size
                     for body in files.values())
    total_digest = sum(len(body.encode("utf-8")) for body in files.values())
    print(f"zapisane: {len(files)} skrotow w {DIGESTS.relative_to(ROOT).as_posix()}/")
    print(f"pelne karty: {total_full} B -> skroty: {total_digest} B "
          f"({100 - 100 * total_digest // max(1, total_full)}% mniej)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
