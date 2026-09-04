"""Generuje indeks regul narratora z korpusu retconow. Etap 9.

PROBLEM. 107 z 142 retconow zawiera klauzule normatywna - zdanie mowiace narratorowi, jak
prowadzic - a 51 z nich nie ma odpowiednika NIGDZIE w system/*.md, AGENTS.md ani
SKILL-gramy.md. Zyja wylacznie w dzienniku, ktorego procedura wznowienia sesji NIE kaze
wczytywac ("nie wczytuj calego dziennika"). Regula, ktorej nikt nie czyta, nie dziala.

DLACZEGO INDEKS, A NIE PRZEPISANIE DO REGUL. Przepisanie tworzy DRUGA KOPIE kazdej reguly,
a duplikacja regul jest glowna zdiagnozowana choroba tego repo: ~20 klastrow duplikacji,
z ktorych 4 realnie sie rozjechaly (m.in. twarda sprzecznosc o katedre Lucana miedzy
SKILL-gramy.md i system/narrator.md). Indeks GENEROWANY nie moze sie rozjechac ze zrodlem,
bo jest z niego wyliczany. Decyzja gracza, 2026-09-04.

METODA JEST JAWNA I PROSTA, zeby wynik byl odtwarzalny bez modelu:
  - klauzula normatywna = tresc korekty zawiera marker imperatywu (lista MARKERY nizej),
  - skrot = ZDANIE, W KTORYM STOI IMPERATYW (nie pierwsze zdanie tresci),
  - temat = pierwszy pasujacy kubelek slow kluczowych (TEMATY nizej).
Skrot jest wiec dosc surowy. Nie jest streszczeniem - jest ADRESEM: mowi, ktory retcon
otworzyc. Pelna tresc zostaje w journal/retcons.jsonl, a `gm recall` od 2026-09-04 stawia
retcony na pierwszym miejscu wynikow.

Uruchomienie:  python tools/build_rules_index.py [--check]
    --check  nie zapisuje, tylko sprawdza, czy plik na dysku jest aktualny (tryb bramki)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RETCONS = ROOT / "campaigns/lucan/journal/retcons.jsonl"
OUTPUT = ROOT / "system" / "retcon-rules-index.md"

BODY_FIELDS = ("replacement", "correction")

# MARKERY MOCNE: samo ich wystapienie czyni tresc normatywna. Slowa "regula", "zasada"
# swiadomie WYPADLY - wystepuja w korpusie tez opisowo ("regula z t_227 zostala cofnieta")
# i wciagaly do indeksu czyste korekty faktu, np. retcon_000096 o wieku brata Klary.
MARKERY = (
    "nie wolno", "zakaz", "narrator nie", "narratorowi", "nie dopisuj", "nie produkuj",
    "nie twórz", "nie tworz", "nie licz", "nie podawaj", "nie grac", "nie grać",
    "nie wymyslaj", "nie wymyślaj", "nie rozstrzygaj", "nie przedstawiaj",
    "musi ", "musza ", "nigdy ", "zawsze ", "obowiaz", "obowiąz",
    "przed pierwsz", "wymaga ", "od teraz", "od tej pory",
)

TEMATY = [
    ("opor i stawki", ("opor", "opór", "stawk", "komplikacj", "utrudni", "przeciwfakt")),
    ("ekspozycja i wiedza NPC", ("ekspozycj", "knowledge", "wiedz", "swiadek", "świadek", "lista", "npc")),
    ("czas i tempo", ("czas", "advance_time", "minut", "godzin", "tempo", "zegar")),
    ("energia i ekonomia slug", ("energi", "rezerw", "nadwyzk", "nadwyżk", "growth", "sluga", "sługa", "sieciarz", "zbiornik")),
    ("nawias i sprawczosc gracza", ("nawias", "poza nawiasem", "deklaracj", "sprawczo")),
    ("mowa i prowadzenie postaci", ("speech", "mowy", "kwesti", "portrayal", "glos", "głos", "brzmi")),
    ("prawo i instytucje", ("praw", "legal", "gildia", "inkwizycj", "kosciol", "kościoł", "instytucj")),
    ("stan i pliki", ("plik", "state/", "karta", "pole", "schemat", "dziennik")),
]


def load() -> list[dict]:
    out = []
    for line in RETCONS.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def body(retcon: dict) -> str:
    for field in BODY_FIELDS:
        value = retcon.get(field)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return ""


def is_normative(text: str) -> bool:
    low = text.casefold()
    return any(marker in low for marker in MARKERY)


def gist(text: str) -> str:
    """Zdanie, w ktorym STOI imperatyw - nie pierwsze zdanie tresci.

    Pierwsze zdanie bylo bledem: dla retcon_000033 dawalo zrzut stanu ("czas 2026-08-18,
    elapsed_seconds_total 292500..."), a wlasciwa regula stala trzy zdania dalej.
    """
    low = text.casefold()
    pozycja = min((low.find(m) for m in MARKERY if low.find(m) >= 0), default=-1)
    if pozycja < 0:
        fragment = text[:170]
    else:
        start = text.rfind(". ", 0, pozycja)
        start = 0 if start < 0 else start + 2
        koniec = text.find(". ", pozycja)
        koniec = len(text) if koniec < 0 else koniec + 1
        fragment = text[start:koniec]
    fragment = " ".join(fragment.split()).strip()
    if len(fragment) > 190:
        fragment = fragment[:187].rsplit(" ", 1)[0] + "..."
    return fragment


def temat(text: str) -> str:
    low = text.casefold()
    for name, words in TEMATY:
        if any(word in low for word in words):
            return name
    return "pozostale"


def build() -> str:
    retcons = load()
    rules: dict[str, list[tuple[str, str]]] = {}
    total = 0
    for retcon in retcons:
        text = body(retcon)
        if not text or not is_normative(text):
            continue
        total += 1
        rules.setdefault(temat(text), []).append((retcon.get("id", "?"), gist(text)))

    lines = [
        "# Indeks regul narratora z korpusu retconow",
        "",
        "**PLIK GENEROWANY - NIE EDYTUJ.** Zrodlem prawdy jest",
        "`campaigns/lucan/journal/retcons.jsonl`. Przebuduj:",
        "",
        "```bash",
        "python tools/build_rules_index.py",
        "```",
        "",
        f"Regul z klauzula normatywna: **{total}** z {len(retcons)} retconow.",
        "",
        "Ten plik jest ADRESEM, nie streszczeniem: mowi, ktory retcon otworzyc. Skroty sa",
        "surowe, bo wycinane deterministycznie ze zdania z imperatywem - nie ufaj im",
        "jako pelnej tresci reguly. Pelny tekst: `gm recall <fraza>` (od 2026-09-04 stawia",
        "retcony na pierwszym miejscu) albo wprost linia w `retcons.jsonl`.",
        "",
        "Powstal dlatego, ze 51 klauzul normatywnych nie mialo odpowiednika w zadnym pliku",
        "regul - a procedura wznowienia sesji nie kaze wczytywac dziennika. Regula, ktorej",
        "nikt nie czyta, nie dziala. Indeks jest generowany, zeby nie mogl sie rozjechac ze",
        "zrodlem: duplikacja regul jest w tym repo choroba, nie rozwiazaniem.",
        "",
    ]
    for name in [t[0] for t in TEMATY] + ["pozostale"]:
        entries = rules.get(name)
        if not entries:
            continue
        lines.append(f"## {name} ({len(entries)})")
        lines.append("")
        for rid, text in sorted(entries):
            lines.append(f"- `{rid}` — {text}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print("[BLAD] system/retcon-rules-index.md jest nieaktualny "
                  "- uruchom: python tools/build_rules_index.py")
            return 1
        print("[OK] indeks regul aktualny")
        return 0

    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"zapisane: {OUTPUT.relative_to(ROOT).as_posix()}, {len(content)} B, "
          f"{content.count(chr(10) + '- `')} regul")
    return 0


if __name__ == "__main__":
    sys.exit(main())
