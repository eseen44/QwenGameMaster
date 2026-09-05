"""Kontrola rejestrow: czy index.yaml mowi prawde o plikach, na ktore wskazuje.

DLACZEGO TO ISTNIEJE. Przeglad 2026-09-05 pokazal, ze rejestry klamaly o statusie 23 z 34 wpisow:
entities/npcs/index.yaml twierdzil "needs_review" o npc_seraphine_vale, ktorej karta od dawna mowi
"active", i to samo o Marze, Borosie, Rusku i Orenie. Jeden wpis (rel_neris_to_lucan) deklarowal
status "active" dla pliku, ktory pola status nie ma w ogole. Rejestr, ktory klamie, jest gorszy niz
jego brak: ktos go czyta zamiast otwierac karte, i podejmuje decyzje na nieaktualnym stanie.

ZRODLEM PRAWDY JEST PLIK, NIE REJESTR. Karta jest miejscem, gdzie odbywa sie praca; rejestr jest
spisem. Dlatego --fix przepisuje status Z PLIKU DO REJESTRU, nigdy odwrotnie.

CO SPRAWDZA, dla kazdego index.yaml poza migration/:
  1. ref_nie_istnieje    - wpis wskazuje na plik, ktorego nie ma
  2. id_sie_nie_zgadza   - plik pod tym ref ma inne id niz wpis
  3. status_sie_rozjechal- wpis deklaruje inny status niz plik
  4. plik_bez_wpisu      - w katalogu rejestru lezy karta, ktorej rejestr nie zna
Kontrola 4 dziala tylko dla rejestrow, ktorych wpisy wskazuja do WLASNEGO katalogu - inaczej
zglaszalaby lokacje (katalogi, nie pliki) i instancje.

Uruchomienie:  python tools/registry_check.py [--check] [--fix]
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


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def resolve(ref: str) -> Path | None:
    """DWIE KONWENCJE SCIEZEK W TYM REPO i obie sa legalne: wiekszosc rejestrow pisze pelna
    sciezke od korzenia repo ('campaigns/lucan/...'), a state/instances/index.yaml pisze
    wzgledem korzenia KAMPANII ('state/instances/...'). To samo rozroznienie obsluguje juz
    gm_runtime.ref_path. Sprawdzanie tylko jednej konwencji dawalo 30 falszywych 'martwych
    wskazan' i 30 falszywych 'plikow bez wpisu' na tym jednym rejestrze."""
    for kandydat in (ROOT / ref, CAMPAIGN / ref):
        if kandydat.is_file():
            return kandydat
    return None


def linie_pliku(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").split("\n")


def bloki(reg: Path) -> list[tuple[int, int, str]]:
    """(start, koniec, id) dla wpisow zapisanych STYLEM BLOKOWYM ('  - id: X' i wciecia nizej)."""
    linie = linie_pliku(reg)
    poczatki = [(i, line.strip()[len("- id: "):]) for i, line in enumerate(linie)
                if re.match(r"^  - id: [\w-]+$", line)]
    out = []
    for nr, (i, wid) in enumerate(poczatki):
        koniec = poczatki[nr + 1][0] if nr + 1 < len(poczatki) else len(linie)
        out.append((i, koniec, wid))
    return out


def registries() -> list[Path]:
    return [p for p in sorted(CAMPAIGN.rglob("index.yaml")) if "/migration/" not in p.as_posix()]


def entries(document: dict) -> list[tuple[str, dict]]:
    """(nazwa_listy, wpis) dla kazdej listy wpisow z polem ref."""
    out = []
    for key, value in document.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and item.get("ref"):
                out.append((key, item))
    return out


def check(fix: bool = False) -> tuple[dict[str, list[str]], dict[str, int]]:
    problems: dict[str, list[str]] = {}
    liczby = {"rejestrow": 0, "wpisow": 0, "naprawionych": 0}

    def zglos(nazwa: str, opis: str) -> None:
        problems.setdefault(nazwa, []).append(opis)

    for reg in registries():
        liczby["rejestrow"] += 1
        document = load(reg)
        do_naprawy: list[tuple[str, str, str]] = []
        wskazane: set[Path] = set()

        for lista, wpis in entries(document):
            liczby["wpisow"] += 1
            cel = resolve(wpis["ref"])
            krotko = f"{reg.relative_to(ROOT).as_posix()}#{lista}/{wpis.get('id')}"
            if cel is None:
                zglos("ref_nie_istnieje", f"{krotko} -> {wpis['ref']}")
                continue
            wskazane.add(cel.resolve())
            plik = load(cel)
            # Id wpisu moze nazywac INSTANCJE, ktorej definicja lezy we WSPOLNYM pliku - tak
            # jest z webber_anchored, ktorego ref wskazuje na companions/webber-network.yaml
            # (id companion_webber_network), a state_ref na instancje o wlasnie tym id.
            # Dlatego dopuszczamy zgodnosc z ref ALBO ze state_ref.
            dozwolone = {plik.get("id")}
            if wpis.get("state_ref"):
                stan = resolve(wpis["state_ref"])
                if stan is not None:
                    dozwolone.add(load(stan).get("id"))
            if wpis.get("id") and plik.get("id") and wpis["id"] not in dozwolone:
                zglos("id_sie_nie_zgadza",
                      f"{krotko}: plik ma id {plik['id']}"
                      + (f", instancja {sorted(dozwolone - {plik.get('id')})}" if len(dozwolone) > 1 else ""))
            if "status" in wpis:
                if plik.get("status") is None:
                    zglos("status_sie_rozjechal",
                          f"{krotko}: rejestr mowi {wpis['status']}, a plik NIE MA pola status")
                elif plik["status"] != wpis["status"]:
                    if fix:
                        do_naprawy.append((wpis["id"], wpis["status"], plik["status"]))
                    else:
                        zglos("status_sie_rozjechal",
                              f"{krotko}: rejestr {wpis['status']} != plik {plik['status']}")

        # Pokrycie katalogu - tylko gdy rejestr wskazuje do siebie.
        wlasne = [p for p in wskazane if p.parent == reg.parent]
        if wlasne or not wskazane:
            for kandydat in sorted(reg.parent.glob("*.yaml")):
                if kandydat.name == "index.yaml" or kandydat.resolve() in wskazane:
                    continue
                zglos("plik_bez_wpisu",
                      f"{reg.relative_to(ROOT).as_posix()} nie zna {kandydat.name}")

        # DUPLIKAT KLUCZA W WPISIE. YAML polyka go bez slowa i bierze OSTATNI, wiec pierwsza
        # wartosc jest niewidzialna dla wszystkiego oprocz czytajacego czlowieka. Tak bylo
        # z loc_city_sewer, ktory mial naraz 'known_by_proxy_unmapped' i 'needs_review'.
        for start, koniec, wid in bloki(reg):
            klucze = [line.split(":")[0].strip() for line in linie_pliku(reg)[start + 1:koniec]
                      if re.match(r"^    \w+:", line)]
            for klucz, ile in collections.Counter(klucze).items():
                if ile > 1:
                    zglos("duplikat_klucza_w_wpisie",
                          f"{reg.relative_to(ROOT).as_posix()}#{wid}: klucz '{klucz}' wystepuje "
                          f"{ile} razy; YAML bierze ostatni, reszta jest niewidzialna")

        if fix and do_naprawy:
            # EDYCJA TEKSTOWA, nie round-trip: czesc rejestrow pisze wpisy jednolinijkowym stylem
            # zwartym ({id: ..., ref: ..., status: ...}), a yaml.safe_dump rozbilby kazdy wpis
            # na blok i zamienil prosta poprawke statusu w przepisanie calego pliku.
            linie = reg.read_text(encoding="utf-8-sig").split("\n")
            for wid, stary, nowy in do_naprawy:
                # (a) wpis w jednej linii
                trafione = [i for i, line in enumerate(linie)
                            if line and f"id: {wid}," in line and f"status: {stary}" in line]
                if len(trafione) == 1:
                    linie[trafione[0]] = linie[trafione[0]].replace(
                        f"status: {stary}", f"status: {nowy}", 1)
                    liczby["naprawionych"] += 1
                    continue
                # (b) wpis blokowy: szukamy linii status W OBREBIE tego wpisu
                poczatki = [i for i, line in enumerate(linie) if line and line.strip() == f"- id: {wid}"]
                if len(poczatki) != 1:
                    zglos("status_nie_do_naprawy_automatem",
                          f"{reg.relative_to(ROOT).as_posix()}#{wid}: nie umiem znalezc wpisu")
                    continue
                i = poczatki[0] + 1
                zrobione = False
                while (i < len(linie) and linie[i] is not None
                       and not re.match(r"^  - ", linie[i]) and linie[i].startswith("    ")):
                    if re.match(r"^    status: ", linie[i]):
                        if zrobione:
                            linie[i] = None  # duplikat - usuwamy w calosci
                        else:
                            linie[i] = f"    status: {nowy}"
                            zrobione = True
                            liczby["naprawionych"] += 1
                    i += 1
                if not zrobione:
                    zglos("status_nie_do_naprawy_automatem",
                          f"{reg.relative_to(ROOT).as_posix()}#{wid}: brak linii status w bloku")
            reg.write_text("\n".join(l for l in linie if l is not None),
                           encoding="utf-8", newline="\n")

    return problems, liczby


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="kod 1 przy naruszeniu (tryb bramki)")
    parser.add_argument("--fix", action="store_true", help="przepisz status Z PLIKU do rejestru")
    args = parser.parse_args()

    problems, liczby = check(fix=args.fix)
    print(f"rejestrow: {liczby['rejestrow']} | wpisow: {liczby['wpisow']}"
          + (f" | zsynchronizowanych statusow: {liczby['naprawionych']}" if args.fix else ""))
    if not problems:
        print("[OK] rejestry: kazdy wpis wskazuje na istniejacy plik o zgodnym id i statusie")
        return 0
    print(f"[BLAD] {sum(len(v) for v in problems.values())} naruszen w {len(problems)} kontrolach:")
    for nazwa, opisy in sorted(problems.items()):
        print(f"  {nazwa} ({len(opisy)}):")
        for opis in opisy[:12]:
            print(f"    - {opis}")
        if len(opisy) > 12:
            print(f"    ... i {len(opisy) - 12} wiecej")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
