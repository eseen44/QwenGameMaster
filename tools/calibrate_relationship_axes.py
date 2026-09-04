"""Kalibracja osi relacji po odtworzeniu logu z dziennika. Decyzja gracza 2026-09-04.

PROBLEM. tools/apply_relationship_log.py wpisal 54 udowodnione ruchy osi, ale NIE dotknal
pola `axes`, bo suma tych ruchow saturuje: cooperation Seraphiny wychodzila 100, czyli
"zrobi dla niego wszystko", co przeczy jej wlasnemu portrayal.priorities_in_order, gdzie
Lucan jest czwarty. Saturacja jest artefaktem zrodla: dziennik zapisuje, co postac dla
Lucana ZROBILA, i prawie nie zapisuje odmow, a te sa w kanonie (t_122, t_036).

DECYZJA GRACZA: sufit 85, przeliczyc proporcjonalnie. Realizacja to jedna regula:
KAZDY UDOWODNIONY RUCH DODATNI LICZY SIE W 60%, bo brakujace odmowy to pozostale 40%.
Wspolczynnik nie jest dobrany pod wynik - wynika z sufitu: cooperation 62 + 0,6*38 = 85.

DWA OGRANICZENIA, ktore czynia te regule wierna uzasadnieniu, a nie tylko rowna:

1. RUCHY UJEMNE ZOSTAJA W PELNEJ SILE. Tlumienie bierze sie z tego, ze dziennik
   nadreprezentuje przyslugi i GUBI odmowy. Ruch ujemny jest wlasnie ta rzadka zapisana
   odmowa - jest niedoreprezentowany, wiec skracanie go odwracaloby sens poprawki.

2. RUCHY PRZED PUNKTEM ZAMROZENIA KARTY ZOSTAJA NIETKNIETE. Sprawdzone: ich chain trafia
   w kanoniczne `axes` co do punktu na wszystkich czterech osiach (45+17=62, 70+18=88,
   15+23=38, 35+7=42). Te wpisy DOKUMENTUJA, jak powstala liczba, ktora ktos ustawil
   swiadomie; tlumienie ich podwazaloby kanon zamiast go uzupelniac.

Kazdy stlumiony wpis dostaje `raw_delta` z wartoscia sprzed tlumienia, zeby kalibracja byla
odwracalna bez siegania do gita. `axes_raw_reconstruction` trzyma wynik nietlumiony.

EDYCJA JEST TEKSTOWA. Round-trip YAML w tym repo zamienia nieocytowana proze z przecinkami
na zagniezdzone mapy z nullami - ten sam blad, ktory naprawialismy w 23 plikach. Skrypt
podmienia wylacznie linie `from:` / `to:` wewnatrz bloku logu i linie pola `axes`.

Uruchomienie:  python tools/calibrate_relationship_axes.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "campaigns" / "lucan" / "relationships"

WSPOLCZYNNIK = 0.6
SUFIT = 85
# Tura, na ktorej karta stala, gdy zaczelo sie odtwarzanie. Ruchy do tej tury wlacznie
# sa juz wycenione w kanonicznym `axes`.
STAN_NA = {"seraphine--lucan.yaml": 38, "varkhen--lucan.yaml": 54}

# Slowa, ktore ZNIKAJA legalnie: nazwy pol przemianowanych przez te kalibracje.
LEGALNIE_ZNIKAJA = (
    "axes_reconstructed_2026_09_04 needs_player_review axes_reconstruction_note "
    "reconstructed needs player review note reconstruction axes 2026 09 04"
).split()

WPIS = re.compile(r"^  - axis: ")

SPROSTOWANIE = (
    "SPROSTOWANIE 2026-09-04: zdanie powyzej o NIETKNIETYM polu axes bylo prawdziwe do "
    "chwili decyzji gracza i przestalo byc - gracz kalibracje rozstrzygnal, patrz "
    "axes_calibration_note. Reszta tej noty, w szczegolnosci ostrzezenie o stronniczosci "
    "zrodla, obowiazuje dalej i JEST PODSTAWA tej kalibracji."
)

NOTA = (
    "SKALIBROWANE 2026-09-04 decyzja gracza: sufit 85, przeliczyc proporcjonalnie. "
    "REGULA PIERWSZA: kazdy udowodniony ruch DODATNI po turze {stale} liczy sie w 60%, bo "
    "dziennik zapisuje, co ta postac dla Lucana ZROBILA, i gubi jej odmowy - a te sa w "
    "kanonie (odmowa przyjecia nazwiska urzednika t_122, odmowa kustodii glejtu t_036). "
    "Brakujace odmowy to pozostale 40%. Wspolczynnik nie jest dobrany pod wynik, wynika "
    "z sufitu: 62 + 0,6*38 = 85. "
    "REGULA DRUGA: ruchy UJEMNE zostaja w pelnej sile. Ruch ujemny to wlasnie ta rzadka "
    "zapisana odmowa - jest niedoreprezentowany, wiec skracanie go odwracaloby sens poprawki. "
    "REGULA TRZECIA: ruchy do tury {stale} wlacznie sa nietkniete, bo ich chain trafia "
    "w kanoniczne axes co do punktu na kazdej osi - dokumentuja, jak powstala liczba "
    "ustawiona swiadomie, a nie dokladaja do niej. "
    "REGULA CZWARTA: osi, ktora kanon postawil POWYZEJ sufitu (tu judgment_confidence na 88), "
    "sufit nie obniza - taka os moze domknac najwyzej polowe dystansu do 100. Sufit "
    "ogranicza wzrost, nie odbiera przeszlosci. "
    "ODWRACALNOSC: kazdy stlumiony wpis nosi raw_delta sprzed tlumienia, a "
    "axes_raw_reconstruction trzyma wynik nietlumiony. "
    "Log byl kanonem, bo jest udowodniony. Liczby sa kanonem teraz, bo gracz je rozstrzygnal."
)


def folded(key: str, tresc: str) -> str:
    return f"{key}: >-\n" + textwrap.indent(textwrap.fill(tresc, width=94), "  ") + "\n"


def tura(event_id: str) -> int:
    match = re.search(r"_(\d{3})_", event_id) or re.search(r"_(\d+)", event_id)
    return int(match.group(1)) if match else 0


def stlum(delta: int) -> int:
    """Dodatnie w 60% (nigdy do zera - dowod istnieje), ujemne bez zmian."""
    if delta <= 0:
        return delta
    return max(1, int(delta * WSPOLCZYNNIK + 0.5))


def sufit(start: int) -> int:
    """Sufit dla osi, ktora startuje z `start`.

    Osie ponizej sufitu konczy na 85. Osi, ktora kanon USTAWIL WYZEJ (judgment_confidence
    Seraphiny stoi na 88), sufit nie moze obnizyc - to byloby cofniecie liczby ustawionej
    swiadomie, czyli dokladnie to, czego ta migracja ma nie robic. Taka os moze domknac
    najwyzej POLOWE dystansu do 100: sufit ogranicza wzrost, nie odbiera przeszlosci.
    """
    return SUFIT if start <= SUFIT else start + (100 - start) // 2


def parsed_words(node: object) -> collections.Counter:
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
    return collections.Counter()


def blok_logu(lines: list[str]) -> tuple[int, int]:
    start = next(i for i, line in enumerate(lines) if line.startswith("axis_change_log:"))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"^[A-Za-z_]\w*:", lines[i])), len(lines))
    return start + 1, end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for nazwa, stale in STAN_NA.items():
        path = CARDS / nazwa
        text = path.read_text(encoding="utf-8-sig")
        before = yaml.safe_load(text)

        # MIGRACJA JEDNORAZOWA I NIE JEST IDEMPOTENTNA: drugie przejscie stlumiloby
        # ruchy juz stlumione. Wychodzimy z komunikatem, a nie z KeyError.
        if before.get("axes_calibration_status") == "player_calibrated_2026_09_04":
            print(f"{nazwa}: juz skalibrowane {before['axes']} - pomijam. "
                  f"Powrot do wartosci surowych: git checkout tego pliku albo "
                  f"axes_raw_reconstruction + raw_delta w logu.")
            continue
        lines = text.split("\n")
        start, end = blok_logu(lines)

        heads = [i for i in range(start, end) if WPIS.match(lines[i])]
        granice = list(zip(heads, heads[1:] + [end]))

        biezace = dict(before["axes"])
        sufity = {os_: sufit(wartosc) for os_, wartosc in before["axes"].items()}
        stlumione = 0
        for head, stop in granice:
            body = "\n".join(line[4:] for line in lines[head:stop])
            entry = yaml.safe_load(body.replace("- axis:", "axis:", 1))
            os_, delta = entry["axis"], entry["to"] - entry["from"]
            if tura(entry["event_id"]) <= stale:
                continue  # juz wyceniony w kanonicznym axes
            nowy = stlum(delta)
            od = biezace[os_]
            do = min(od + nowy, sufity[os_]) if nowy > 0 else od + nowy
            biezace[os_] = do
            for i in range(head, stop):
                if re.match(r"^    from: -?\d+$", lines[i]):
                    lines[i] = f"    from: {od}"
                elif re.match(r"^    to: -?\d+$", lines[i]):
                    lines[i] = f"    to: {do}"
                    if do - od != delta:
                        lines[i] += f"\n    raw_delta: {delta}"
                        stlumione += 1

        text = "\n".join(lines)
        surowe = before["axes_reconstructed_2026_09_04"]
        blok = (
            "axes: {" + ", ".join(f"{k}: {v}" for k, v in biezace.items()) + "}\n"
            + "axes_raw_reconstruction: {"
            + ", ".join(f"{k}: {v}" for k, v in surowe.items()) + "}\n"
            + "axes_calibration_status: player_calibrated_2026_09_04\n"
            + folded("axes_calibration_note", NOTA.format(stale=f"t_{stale:03d}"))
        )
        text = re.sub(r"(?m)^axes: \{[^\n]*\}\n", blok, text, count=1)
        text = re.sub(r"(?m)^axes_reconstructed_2026_09_04: \{[^\n]*\}\n", "", text, count=1)
        text = re.sub(r"(?m)^axes_calibration_status: needs_player_review\n", "", text, count=1)

        # Nota rekonstrukcji ZOSTAJE - opisuje stronniczosc zrodla i to jest dalej prawda.
        # Nieaktualne jest w niej jedno zdanie, o nietknietym polu axes, wiec dostaje
        # sprostowanie na koncu tego samego bloku. Zadne slowo nie jest usuwane.
        stary = re.search(r"(?m)^axes_reconstruction_note: >-\n((?:  .*\n)+)", text)
        if stary:
            text = (text[:stary.end()]
                    + textwrap.indent(textwrap.fill(SPROSTOWANIE, width=94), "  ") + "\n"
                    + text[stary.end():])

        after = yaml.safe_load(text)
        assert len(after["axis_change_log"]) == len(before["axis_change_log"]), "wpis logu zniknal"
        brak = parsed_words(before) - parsed_words(after)
        for slowo in LEGALNIE_ZNIKAJA:
            brak.pop(slowo, None)
        assert not brak, f"{nazwa}: migracja gubi tresc: {dict(list(brak.items())[:6])}"

        for os_ in after["axes"]:
            chain = [e for e in after["axis_change_log"] if e["axis"] == os_]
            for a, b in zip(chain, chain[1:]):
                assert a["to"] == b["from"], (
                    f"{nazwa}/{os_}: dziura w chainie {a['to']} != {b['from']}")
            if chain:
                assert chain[-1]["to"] == after["axes"][os_], (
                    f"{nazwa}/{os_}: chain konczy sie na {chain[-1]['to']}, "
                    f"a axes mowi {after['axes'][os_]}")

        for os_, wartosc in after["axes"].items():
            assert wartosc <= sufity[os_], (
                f"{nazwa}/{os_}: sufit przebity - {wartosc} > {sufity[os_]}")
            # Os moze spasc TYLKO wtedy, gdy log nosi na niej ruch ujemny z dowodem.
            if wartosc < before["axes"][os_]:
                assert any(e["axis"] == os_ and e["to"] < e["from"]
                           for e in after["axis_change_log"]), (
                    f"{nazwa}/{os_}: spadek {before['axes'][os_]} -> {wartosc} bez ruchu "
                    f"ujemnego w logu, czyli bez dowodu")

        print(f"{nazwa}: {stlumione} wpisow stlumionych z {len(granice)} w logu")
        print(f"   przed  {before['axes']}")
        print(f"   surowe {surowe}")
        print(f"   PO     {after['axes']}")
        if not args.dry_run:
            path.write_text(text, encoding="utf-8", newline="\n")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
    return 0


if __name__ == "__main__":
    sys.exit(main())
