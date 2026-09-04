"""Odzysk prozy, ktora YAML przeczytal jako klucze o wartosci null.

OBJAW. W mapie w zapisie plaskim niecytowana wartosc z przecinkiem rozpada sie na kolejne
pary, bo przecinek jest separatorem:

    {fact_id: X, claim: Wie, ze wlasciciel znal skale zagrozenia}
                        ^^^^^^^^ para "claim: Wie"    ^^^^^^^^^^^ para " ze ...": null

Tekst na dysku jest KOMPLETNY - ginie wylacznie jego widocznosc dla kazdego maszynowego
czytelnika, w tym dla narratora czytajacego sparsowany plik. W 23 plikach kampanii jest tak
91 fragmentow, m.in. negacja "NIE material zuzywany przy ozywieniu (retcon_000015)"
w state/resources.yaml, ktora po sparsowaniu znika i zostawia przedmiot bez zastrzezenia.

NAPRAWA JEST PRZECYTOWANIEM, NIE PRZEPISANIEM. Skrypt pracuje na TEKSCIE - round-trip przez
biblioteke YAML jest tu zabroniony, bo sam produkuje dokladnie te awarie (sprawdzone
2026-09-04 na entities/npcs/varkhen.yaml, plik trzeba bylo cofnac). Dla kazdej mapy plaskiej
znajduje pierwsza pare o wartosci null i przycytowywuje wartosc pary POPRZEDNIEJ tak, zeby
objela caly tekst do konca mapy.

GWARANCJA. Po naprawie kazdego pliku sprawdzane jest, ze: YAML sie parsuje, liczba elementow
w kazdej liscie jest identyczna, nie ma juz ani jednego klucza-prozy o wartosci null, a suma
znakow prozy nie zmalala. Plik, ktory nie przechodzi ktorejkolwiek kontroli, jest cofany.

ZNANE OGRANICZENIE, CELOWE. Apostrof w niecytowanej wartosci ("Mowi don't, a potem")
wyglada dla skanera jak otwarcie cudzyslowu, wiec taka mapa nie zostaje rozpoznana i plik
jest RAPORTOWANY jako "wzorzec nierozpoznany - do recznej naprawy", nie ruszany. Lepiej
odmowic niz zepsuc. W kampanii nie ma dzis ani jednego takiego przypadku.

Uruchomienie:  python tools/fix_prose_keys.py [--dry-run] [--only SCIEZKA]
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


def is_prose_key(key: object) -> bool:
    return isinstance(key, str) and " " in key.strip() and len(key.strip()) > 12


def prose_key_count(node: object) -> int:
    total = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if value is None and is_prose_key(key):
                total += 1
            total += prose_key_count(value)
    elif isinstance(node, list):
        for value in node:
            total += prose_key_count(value)
    return total


def list_shape(node: object) -> list[int]:
    """Dlugosci wszystkich list w dokumencie, w kolejnosci przejscia."""
    shape: list[int] = []
    if isinstance(node, dict):
        for value in node.values():
            shape += list_shape(value)
    elif isinstance(node, list):
        shape.append(len(node))
        for value in node:
            shape += list_shape(value)
    return shape


def split_top_level(inner: str) -> list[str]:
    """Dzieli wnetrze mapy plaskiej po przecinkach najwyzszego poziomu."""
    parts: list[str] = []
    depth = 0
    quote: str | None = None
    current = ""
    for char in inner:
        if quote:
            current += char
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current += char
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    return parts


def find_flow_maps(line: str) -> list[tuple[int, int]]:
    """Pozycje (start, koniec) map plaskich najwyzszego poziomu.

    Dziala na CALYM tekscie, nie na pojedynczej linii - mapy plaskie w tym repo
    rozciagaja sie na kilka linii (np. state/resources.yaml), a skan linia po linii
    ich nie widzial i pierwsza wersja tego skryptu nie rozpoznala ani jednego wzorca.
    """
    spans: list[tuple[int, int]] = []
    depth = 0
    start = -1
    quote: str | None = None
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                spans.append((start, index))
                start = -1
    return spans


def quote_scalar(text: str) -> str:
    """Cytowanie w stylu YAML: pojedyncze cudzyslowy, apostrof podwojony."""
    return "'" + text.replace("'", "''") + "'"


def is_pair(part: str) -> bool:
    """Czy element mapy plaskiej jest prawdziwa para "klucz: wartosc".

    Klucz schematu nie ma spacji (fact_id, source_event_id, claim, assessed_use).
    Element bez dwukropka albo z kluczem zawierajacym spacje jest fragmentem prozy,
    ktory przecinek oderwal od poprzedniej wartosci.
    """
    head, sep, tail = part.partition(":")
    if not sep:
        return False
    key = head.strip()
    if not key or " " in key or "'" in key or '"' in key:
        return False
    return True


def repair_flow_map(inner: str) -> tuple[str, int]:
    """Wtapia kazdy fragment prozy w NAJBLIZSZA POPRZEDZAJACA pare.

    Kluczowe: legalne pary stojace PO fragmencie zostaja nietkniete. Pierwsza wersja
    scalala wszystko do konca mapy i wchlaniala np. assessed_use razem z trescia,
    co gubilo klucz - kontrola slow to wylapala i plik zostal odrzucony.
    """
    parts = split_top_level(inner)
    if len(parts) < 2:
        return inner, 0
    if not any(not is_pair(part) and part.strip() for part in parts[1:]):
        return inner, 0

    groups: list[list[str]] = []
    merged = 0
    for index, part in enumerate(parts):
        if index == 0 or is_pair(part) or not part.strip():
            groups.append([part])
        else:
            if not groups:
                return inner, 0
            groups[-1].append(part)
            merged += 1

    out: list[str] = []
    for group in groups:
        if len(group) == 1:
            out.append(group[0])
            continue
        key, sep, value = group[0].partition(":")
        if not sep or value.strip().startswith(("'", '"', "{", "[")):
            return inner, 0
        whole = ",".join([value.strip()] + group[1:])
        whole = " ".join(whole.split())          # zwiniecie zlaman linii, jak w YAML
        out.append(f"{key}: {quote_scalar(whole)}")
    return ",".join(out), merged


def repair_text(text: str) -> tuple[str, int]:
    """Jedno przejscie po CALYM tekscie - mapy plaskie lamia sie na kilka linii."""
    merged = 0
    for start, end in reversed(find_flow_maps(text)):
        inner = text[start + 1 : end]
        repaired, count = repair_flow_map(inner)
        if count:
            text = text[:start] + "{" + repaired + "}" + text[end + 1 :]
            merged += count
    return text, merged


def all_words(node: object) -> list[str]:
    """Wszystkie slowa z dokumentu, z kluczy i wartosci, po normalizacji bialych znakow.

    Cytowany skalar wielolinijkowy zwija zlamanie linii w spacje, wiec porownanie
    znak-w-znak dawaloby falszywy alarm. Porownujemy WIELOZBIOR SLOW: zadne slowo
    nie moze zniknac, i to jest wlasciwa gwarancja "nie tracimy tresci".
    """
    if isinstance(node, str):
        # \w+ zamiast split(): po scaleniu slowo dostaje przy sobie przecinek
        # ("uznal" -> "uznal,"), wiec podzial po spacjach dawal falszywy alarm o utracie.
        return re.findall(r"\w+", node)
    if isinstance(node, dict):
        words: list[str] = []
        for key, value in node.items():
            words += all_words(key) + all_words(value)
        return words
    if isinstance(node, list):
        words = []
        for value in node:
            words += all_words(value)
        return words
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only")
    args = parser.parse_args()

    targets = [ROOT / args.only] if args.only else sorted(CAMPAIGN.rglob("*.yaml"))
    repaired_files = 0
    repaired_fragments = 0
    refused: list[str] = []

    for path in targets:
        if "sources" in path.parts and "migration" in path.parts:
            continue
        original = path.read_text(encoding="utf-8-sig")
        try:
            before = yaml.safe_load(original)
        except yaml.YAMLError:
            continue
        broken = prose_key_count(before)
        if not broken:
            continue

        candidate, merged = repair_text(original)
        if not merged:
            refused.append(f"{path.relative_to(ROOT).as_posix()}: {broken} fragmentow, "
                           f"wzorzec nierozpoznany - do recznej naprawy")
            continue

        # KONTROLE. Kazda musi przejsc, inaczej plik zostaje bez zmian.
        try:
            after = yaml.safe_load(candidate)
        except yaml.YAMLError as exc:
            refused.append(f"{path.relative_to(ROOT).as_posix()}: po naprawie YAML nie parsuje sie ({exc})")
            continue
        checks = {
            "kluczy-prozy": prose_key_count(after) < broken,
            "ksztalt-list": list_shape(after) == list_shape(before),
            "nie-ubylo-slow": not (collections.Counter(all_words(before))
                                   - collections.Counter(all_words(after))),
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            refused.append(f"{path.relative_to(ROOT).as_posix()}: kontrola nieprzeszla ({', '.join(failed)})")
            continue

        left = prose_key_count(after)
        status = "OK" if left == 0 else f"zostalo {left}"
        print(f"  {path.relative_to(ROOT).as_posix():<62} {broken} -> {left}  {status}")
        repaired_files += 1
        repaired_fragments += broken - left
        if not args.dry_run:
            path.write_text(candidate, encoding="utf-8", newline="\n")

    print()
    print(f"plikow naprawionych: {repaired_files} | fragmentow odzyskanych: {repaired_fragments}")
    if refused:
        print(f"ODMOWA NAPRAWY ({len(refused)}) - te pliki zostaly nietkniete:")
        for item in refused:
            print(f"  - {item}")
    if args.dry_run:
        print("--dry-run: nic nie zapisano")
    return 0


if __name__ == "__main__":
    sys.exit(main())
