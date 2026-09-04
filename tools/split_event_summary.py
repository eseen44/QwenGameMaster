"""Rozdzielenie pola `summary` na proze i slad audytowy. Etap 11.

PROBLEM, ZMIERZONY. `summary` w events.jsonl pelni dwie wykluczajace sie funkcje: jest
JEDYNYM zapisem narracji miedzy sesjami (tak stanowi SKILL-gramy.md) i jednoczesnie
protokolem audytowym tury. Protokol wygral: udzial tresci audytowej wzrosl z 0,6% (tury
50-74) do 51,3% (tury 225-235), a srednia dlugosc z 1 048 do 6 432 znakow. Skutki sa
udokumentowane przez samo repo dwa razy - retcon_000040 (wszystkie NPC brzmia jednakowo,
bo narrator odtwarza je z rejestru ksiegowego) i retcon_000136 (uzasadnienie narratora
recytowane jako kwestia postaci) - i oba razy naprawione REGULA, nie zmiana schematu.

Otwarcie sesji to dzis 33 235 znakow z czterech ostatnich wpisow.

CO ROBI TA MIGRACJA - I CZEGO NIE ROBI.
Robi: do kazdego wpisu dopisuje `audit` (dokladna kopia dotychczasowego `summary`) oraz
`prose_auto` - deterministyczny wyciag: GLOWA wpisu (akapit przed pierwsza numerowana
sekcja, czyli teza tury) plus sekcja STAN z konca, przyciete. Wyciag jest oznaczony
`prose_source: auto_extracted`, bo nie jest autorska proza - jest ADRESEM i orientacja.
NIE robi: nie przepisuje 235 pol summary na nowo. To jedyny zapis prozy calej kampanii
(788 344 znakow) i zadna maszyna nie napisze jej za nikogo; probowac znaczyloby zgubic
zdanie. `summary` zostaje NIETKNIETE.

Od tej migracji `commit` przyjmuje `outcome.prose` i wtedy wpis dostaje `prose` z
`prose_source: authored` - czyli nowe tury maja proze pisana, a nie wyciagana.

Uruchomienie:  python tools/split_event_summary.py [--dry-run] [--cap 1100]
Podglad taniego otwarcia sesji: python tools/gm.py recent --limit 4
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "campaigns" / "lucan" / "journal" / "events.jsonl"

CAP_DEFAULT = 1100


def extract(summary: str, cap: int) -> str:
    """GLOWA + STAN, przyciete. Deterministycznie, bez modelu."""
    text = summary or ""
    numbered = re.search(r"(?m)^\s*\d+\.\s", text)
    head = (text[: numbered.start()] if numbered else text).strip()
    state = ""
    match = re.search(r"(?ms)^\s*\d+\.\s*STAN[.:]?\s*(.+)$", text)
    if match:
        state = match.group(1).strip()
    head = " ".join(head.split())
    state = " ".join(state.split())

    if state:
        budget_head = max(cap // 2, cap - len(state) - 12)
        if len(head) > budget_head:
            head = head[: budget_head - 3].rsplit(" ", 1)[0] + "..."
        remaining = cap - len(head) - 12
        if len(state) > remaining:
            state = state[: max(0, remaining - 3)].rsplit(" ", 1)[0] + "..."
        return f"{head}  STAN: {state}"
    if len(head) > cap:
        head = head[: cap - 3].rsplit(" ", 1)[0] + "..."
    return head


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cap", type=int, default=CAP_DEFAULT)
    args = parser.parse_args()

    lines = [line for line in EVENTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]

    touched = 0
    for event in events:
        summary = event.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            continue
        if event.get("audit") == summary and event.get("prose_auto"):
            continue
        event["audit"] = summary
        event["prose_auto"] = extract(summary, args.cap)
        event.setdefault("prose_source", "auto_extracted")
        touched += 1

    # GWARANCJA: `audit` trzyma DOKLADNIE dotychczasowy summary, wiec nic nie ginie.
    for event, raw in zip(events, lines):
        original = json.loads(raw).get("summary")
        if isinstance(original, str) and original.strip():
            if event["audit"] != original:
                print(f"[BLAD] {event['id']}: audit nie jest kopia summary")
                return 1

    prose_total = sum(len(e.get("prose_auto") or "") for e in events)
    summary_total = sum(len(e.get("summary") or "") for e in events)
    ostatnie4_summary = sum(len(e.get("summary") or "") for e in events[-4:])
    ostatnie4_prose = sum(len(e.get("prose_auto") or "") for e in events[-4:])
    print(f"wpisow: {len(events)}, uzupelnionych: {touched}")
    print(f"summary razem: {summary_total} znakow -> prose_auto razem: {prose_total}")
    print(f"OTWARCIE SESJI (4 ostatnie): {ostatnie4_summary} -> {ostatnie4_prose} znakow "
          f"({100 - 100 * ostatnie4_prose // max(1, ostatnie4_summary)}% mniej)")
    puste = [e["id"] for e in events if not (e.get("prose_auto") or "").strip()]
    if puste:
        print(f"UWAGA: {len(puste)} wpisow bez wyciagu prozy: {puste[:5]}")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    EVENTS.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"\nzapisane: {EVENTS.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
