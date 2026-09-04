"""Rozbicie magazynu uzasadnien act-03-defence na pliki per sekcja. Etap 8.

POWOD. SKILL-gramy.md deklaruje `planning/act-03-defence.yaml` jako OBOWIAZKOWY w kazdej
turze, w ktorej gracz planuje - a plik wazy 78 517 B, czyli 1,92 calego budzetu kontekstu.
Zmierzone `context plan --tag choosing_a_plan`: tura planowania to 211 587 B = 516% budzetu.
Jednoczesnie tura planowania potrzebuje zwykle JEDNEJ albo DWOCH sekcji z dwudziestu
czterech - reszta to uzasadnienia watkow, ktorych ta tura nie dotyczy.

CO ROBI SKRYPT. Kazda sekcje merytoryczna zapisuje jako osobny plik w
`planning/act-03-defence/<klucz>.yaml`, a `act-03-defence.yaml` zamienia w INDEKS
z metadanymi i lista sekcji (klucz, sciezka, rozmiar). Przepisuje TEZ wszystkie odwolania
w repo z `planning/act-03-defence.yaml#<sekcja>` na nowa sciezke - takze te siedzace
w prozie kart NPC, bo to wskazniki, ktore ktos bedzie chcial otworzyc.

GWARANCJA. Po migracji sprawdzane jest, ze wielozbior slow wszystkich nowych plikow razem
z indeksem zawiera KAZDE slowo oryginalu. Skrypt odmawia zapisu, gdy cokolwiek by zniknelo.

Uruchomienie:  python tools/split_defence_store.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
SOURCE = CAMPAIGN / "planning" / "act-03-defence.yaml"
TARGET_DIR = CAMPAIGN / "planning" / "act-03-defence"
REF_OLD = "planning/act-03-defence.yaml#"

# Klucze, ktore zostaja w indeksie - metadane, nie uzasadnienia.
META_KEYS = ("schema_version", "id", "name", "status", "purpose", "source_refs")


def words(text: str) -> collections.Counter:
    return collections.Counter(re.findall(r"\w+", text))


def dump(document: object) -> str:
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=100)


def parsed_words(node: object) -> collections.Counter:
    """Slowa z SPARSOWANEJ struktury, nie z tekstu.

    Liczenie na tekscie bylo bledem: yaml.safe_dump koduje czesc napisow jako skalary
    cudzyslowowe z sekwencjami \n, wiec token "PIATA" zamienial sie w "nPIATA" i miara
    zglaszala utrate slowa, ktore nie zginelo. Ten sam blad co w etapie 3, gdzie podzial
    po spacjach gubil slowo z doklejonym przecinkiem. Miara musi patrzec na TRESC.
    """
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
    if node is None:
        return collections.Counter()
    return collections.Counter(re.findall(r"\w+", str(node)))


def section_slices(text: str, keys: list[str]) -> dict[str, str]:
    """Surowe linie kazdej sekcji najwyzszego poziomu, BEZ ponownej serializacji.

    Kopiowanie tekstu zamiast przepisywania przez biblioteke YAML zachowuje formatowanie,
    blokowe skalary i lamanie linii - a magazyn uzasadnien jest czytany przez ludzi.
    Przy okazji gwarancja "nic nie ginie" staje sie dokladna, nie przyblizona.
    """
    lines = text.split(chr(10))
    starts: dict[str, int] = {}
    for index, line in enumerate(lines):
        match = re.match(r"^([a-z0-9_]+):", line)
        if match and match.group(1) in keys:
            starts[match.group(1)] = index
    order = sorted(starts.items(), key=lambda item: item[1])
    out: dict[str, str] = {}
    for position, (key, begin) in enumerate(order):
        end = order[position + 1][1] if position + 1 < len(order) else len(lines)
        # obetnij puste linie na koncu bloku
        block = lines[begin:end]
        while block and not block[-1].strip():
            block.pop()
        out[key] = chr(10).join(block) + chr(10)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    original_text = SOURCE.read_text(encoding="utf-8-sig")
    document = yaml.safe_load(original_text)
    sections = {k: v for k, v in document.items() if k not in META_KEYS}
    print(f"sekcji merytorycznych: {len(sections)}, zrodlo: {len(original_text)} znakow")

    slices = section_slices(original_text, list(sections))
    missing_slices = [k for k in sections if k not in slices]
    if missing_slices:
        print(f"[BLAD] nie znalazlem surowych linii sekcji: {missing_slices}")
        return 1

    files: dict[str, str] = {}
    index_sections = []
    for key in sections:
        naglowek = chr(10).join([
            f"schema_version: {document.get('schema_version', 1)}",
            f"id: {document.get('id', 'act_03_defence')}__{key}",
            f"section: {key}",
            'part_of: campaigns/lucan/planning/act-03-defence.yaml',
            'split_note: >-',
            '  Wyodrebnione 2026-09-04 z planning/act-03-defence.yaml (etap 8). Tresc',
            '  przeniesiona 1:1, surowymi liniami, bez ponownej serializacji - formatowanie',
            '  i lamanie linii oryginalu zachowane.',
            '',
        ])
        body = naglowek + slices[key]
        files[key] = body
        index_sections.append({
            "key": key,
            "ref": f"campaigns/lucan/planning/act-03-defence/{key}.yaml",
            "bytes": len(body.encode("utf-8")),
        })

    index = {key: document[key] for key in META_KEYS if key in document}
    index["object_type"] = "rationale_store_index"
    index["split_note"] = (
        "ROZBITY 2026-09-04 (etap 8). Ten plik jest INDEKSEM - uzasadnienia leza w "
        "planning/act-03-defence/<klucz>.yaml, po jednym pliku na sekcje. Powod: plik byl "
        "deklarowany jako obowiazkowy w kazdej turze planowania i wazyl 78 517 B, czyli "
        "1,92 budzetu kontekstu, a tura potrzebuje zwykle jednej-dwoch sekcji z dwudziestu "
        "czterech. Tresc nie zostala zmieniona ani skrocona; przeniesiona 1:1. "
        "Wczytuj sekcje, ktorej dotyczy tura, nie caly magazyn."
    )
    index["sections"] = sorted(index_sections, key=lambda item: -item["bytes"])
    index_text = dump(index)

    # GWARANCJA: zadne slowo nie ginie - liczone na SPARSOWANEJ tresci.
    razem = parsed_words(yaml.safe_load(index_text))
    for key, body in files.items():
        razem += parsed_words(yaml.safe_load(body))
    brak = parsed_words(document) - razem
    if brak:
        print(f"[BLAD] migracja zgubilaby {sum(brak.values())} slow: {dict(list(brak.items())[:10])}")
        print("nic nie zapisano")
        return 1
    print("kontrola slow: zadne slowo nie ginie")

    total_new = len(index_text.encode("utf-8")) + sum(len(b.encode("utf-8")) for b in files.values())
    print(f"indeks: {len(index_text.encode('utf-8'))} B | sekcje razem: {total_new} B")

    # Przepisanie odwolan w calym repo.
    rewrites: list[tuple[str, int]] = []
    pattern = re.compile(r"(campaigns/lucan/)?planning/act-03-defence\.yaml#([a-z0-9_]+)")

    def replace(match: re.Match) -> str:
        section = match.group(2)
        if section not in sections:
            return match.group(0)
        return f"campaigns/lucan/planning/act-03-defence/{section}.yaml"

    targets = [p for p in list(CAMPAIGN.rglob("*.yaml")) + list(CAMPAIGN.rglob("*.md"))
               + list((ROOT / "worlds").rglob("*.yaml")) + [ROOT / "SKILL-gramy.md", ROOT / "AGENTS.md"]
               if p.exists() and not any(x in p.as_posix() for x in
                                         ("/transactions/", "/snapshots/", "/migration/sources/",
                                          "/superseded/", "/act-03-defence/"))]
    for path in targets:
        text = path.read_text(encoding="utf-8-sig")
        new = pattern.sub(replace, text)
        # Anchor zagniezdzony: <sekcja>.<podklucz> -> plik#podklucz
        new = re.sub(r"campaigns/lucan/planning/act-03-defence/([a-z0-9_]+)\.yaml\.([a-z0-9_]+)",
                     r"campaigns/lucan/planning/act-03-defence/\1.yaml#\2", new)
        if new != text:
            rewrites.append((path.relative_to(ROOT).as_posix(), len(pattern.findall(text))))
            if not args.dry_run:
                path.write_text(new, encoding="utf-8", newline="\n")
    print(f"plikow z przepisanymi odwolaniami: {len(rewrites)}")
    for name, count in rewrites:
        print(f"  {name} ({count})")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for key, body in files.items():
        (TARGET_DIR / f"{key}.yaml").write_text(body, encoding="utf-8", newline="\n")
    SOURCE.write_text(index_text, encoding="utf-8", newline="\n")
    print(f"\nzapisane: {len(files)} sekcji w {TARGET_DIR.relative_to(ROOT).as_posix()}/ "
          f"oraz indeks {SOURCE.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
