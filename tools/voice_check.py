"""Kontrola kart glosu NPC: pokrycie, kompletnosc osi, dlugosc, rejestr i rozroznialnosc.

DLACZEGO TO ISTNIEJE, ZMIERZONE 2026-09-09. Glos NPC nie mial wlasnego zrodla. Karta miala
`speech_traits` - trzy wypunktowania, ~0,4 KB - obok `knowledge`, ktore w skrocie karty
Kesza wazy 8,3 KB i jest napisane rejestrem protokolu audytowego (wersaliki, "WNIOSKU NIE
WYCIAGNAL NA GLOS", "NIEUSTALONE:", odwolania do plikow). Stosunek 20:1 na rzecz protokolu
w tym samym aktywnym kontekscie znaczy, ze model imituje protokol, bo protokol jest tam
dominujacym rejestrem. To jest retcon_000040 i retcon_000136 wchodzace przez skrot karty.

Dwie z trzech linii `speech_traits` Kesza kazaly mu wprost wyceniac ("Wycenia, nie bramkuje:
mowi to kosztuje tyle"), a pierwsza linia Seraphiny kazala nazywac CENE kazdej rzeczy przed
zgoda - czyli zrodlo wejsciowe uczylo dokladnie tego, czego retcon_000162 zabronil w prozie.

CO SPRAWDZA (wszystko BLOKUJACE - kazde twierdzenie jest maszynowo sprawdzalne):
  1. brak_karty_glosu   - wymagany NPC nie ma pliku w entities/npcs/voices/
  2. brak_osi           - karta glosu nie ma wszystkich osmiu osi (albo os jest pusta)
  3. karta_za_dluga     - powyzej LIMIT_BAJTOW; kontrakt przestaje byc kontraktem
  4. rejestr_wyceny     - karta glosu uzywa slownika wyceny/audytu, czyli uczy tego,
                          czego ma nie uczyc (retcon_000162)
  5. glos_nierozroznialny - dwie karty maja te sama os slowo w slowo
  6. karta_bez_npc      - plik glosu wskazuje na npc_id, ktorego nie ma
  7. szablon_w_probce   - `samples` uzywaja konstrukcji "nie X, tylko Y" u wiecej niz
                          jednej postaci; to ma byc wyjatek, nie wspolny glos

KOGO WYMAGAMY. Zbior wymaganych kart jest WYLICZANY z kart NPC (status active oraz
importance full_agent albo istniejacy skrot karty), a nie trzymany recznie - rejestr,
ktory klamie, jest gorszy niz jego brak (patrz tools/registry_check.py).

Uruchomienie:  python tools/voice_check.py [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "campaigns" / "lucan" / "entities" / "npcs"
VOICES = CARDS / "voices"
DIGESTS = CARDS / "digests"

OSIE = ("rhythm", "diction", "evasion", "mistakes", "body", "length", "emotion", "blind_spot")
LIMIT_BAJTOW = 2500

# SLOWNIK, KTORY MA NIE WCHODZIC DO KARTY GLOSU. Nie jest to zakaz slow w prozie - to zakaz
# UCZENIA rejestru z pliku, ktory jest jedynym zrodlem glosu. Kart glosu jest kilka i sa
# krotkie, wiec falszywy alarm poprawia sie w jednym zdaniu; w prozie ten sam zakaz byl by
# kruchy i dlatego proza ma osobna kontrole (tools/prose_check.py), ktora odroznia rozmowe
# o pieniadzach od wyceniania kazdej decyzji.
REJESTR_WYCENY = re.compile(
    r"(?iu)\b("
    r"cen[aeyoęą]\w*|wycen\w*|koszt\w*|wartoś\w*|wartos\w*|"
    r"rachun\w*|opłacal\w*|oplacal\w*|bilans\w*|"
    r"ekspozycj\w*|aktyw\w*|przelicz\w*|kalkul\w*|audyt\w*|"
    r"zmierzon\w*|nierozstrzygni\w*"
    r")\b"
)
# Pole `money` opisuje, jak postac rozmawia o pieniadzach - tam slowo "kwota"/"liczba" jest
# na miejscu, ale slownik wyceny nadal nie. Zadnego wyjatku nie ma; sprawdzamy caly plik.

SZABLON_NIE_TYLKO = re.compile(r"(?iu)\bnie\b[^,.;!?]{1,70},\s*tylko\b")


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def wymagane() -> dict[str, Path]:
    """{stem karty NPC: sciezka karty} dla postaci, ktore MUSZA miec karte glosu."""
    out: dict[str, Path] = {}
    for path in sorted(CARDS.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        try:
            card = load(path)
        except yaml.YAMLError:
            continue
        if not isinstance(card, dict) or card.get("status") != "active":
            continue
        ma_skrot = (DIGESTS / path.name).exists()
        if card.get("importance") == "full_agent" or ma_skrot:
            out[path.stem] = path
    return out


def normalizuj(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def check() -> tuple[dict[str, list[str]], dict[str, int]]:
    problemy: dict[str, list[str]] = {}
    liczby = {"wymaganych": 0, "kart_glosu": 0, "bajtow": 0}

    def zglos(nazwa: str, opis: str) -> None:
        problemy.setdefault(nazwa, []).append(opis)

    npc_ids = {}
    for path in sorted(CARDS.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        try:
            card = load(path)
        except yaml.YAMLError:
            continue
        if isinstance(card, dict) and card.get("id"):
            npc_ids[card["id"]] = path.stem

    potrzebne = wymagane()
    liczby["wymaganych"] = len(potrzebne)
    for stem, card_path in sorted(potrzebne.items()):
        if not (VOICES / f"{stem}.yaml").exists():
            zglos("brak_karty_glosu",
                  f"{card_path.relative_to(ROOT).as_posix()} -> brakuje "
                  f"entities/npcs/voices/{stem}.yaml")

    osie_widziane: dict[tuple[str, str], str] = {}
    szablon_u: list[str] = []

    for path in sorted(VOICES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        liczby["kart_glosu"] += 1
        rozmiar = path.stat().st_size
        liczby["bajtow"] += rozmiar
        krotko = path.relative_to(ROOT).as_posix()
        try:
            voice = load(path)
        except yaml.YAMLError as blad:
            zglos("brak_osi", f"{krotko}: nieczytelny YAML ({blad})")
            continue

        if rozmiar > LIMIT_BAJTOW:
            zglos("karta_za_dluga",
                  f"{krotko}: {rozmiar} B > {LIMIT_BAJTOW} B - kontrakt glosu ma byc krotki")

        npc_id = voice.get("npc_id")
        if npc_id not in npc_ids:
            zglos("karta_bez_npc", f"{krotko}: npc_id {npc_id!r} nie ma karty NPC")

        for os in OSIE:
            if not normalizuj(voice.get(os)):
                zglos("brak_osi", f"{krotko}: brak albo pusta os '{os}'")
                continue
            klucz = (os, normalizuj(voice[os]))
            if klucz in osie_widziane:
                zglos("glos_nierozroznialny",
                      f"{krotko} ma os '{os}' identyczna jak {osie_widziane[klucz]}")
            else:
                osie_widziane[klucz] = krotko

        if not isinstance(voice.get("samples"), list) or len(voice["samples"]) < 2:
            zglos("brak_osi", f"{krotko}: potrzebne co najmniej dwie 'samples' - kwestie wprost")

        tresc = path.read_text(encoding="utf-8-sig")
        trafienia = sorted({m.group(0).lower() for m in REJESTR_WYCENY.finditer(tresc)})
        if trafienia:
            zglos("rejestr_wyceny",
                  f"{krotko}: slownik wyceny/audytu w karcie glosu: {', '.join(trafienia)}")

        probki = " ".join(str(s) for s in (voice.get("samples") or []))
        if SZABLON_NIE_TYLKO.search(probki):
            szablon_u.append(krotko)

    if len(szablon_u) > 1:
        zglos("szablon_w_probce",
              "konstrukcja 'nie X, tylko Y' w probkach wiecej niz jednej postaci: "
              + ", ".join(szablon_u))

    return problemy, liczby


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="tylko wynik, kod 1 przy bledzie")
    args = parser.parse_args()

    problemy, liczby = check()
    if not problemy:
        print(f"[OK] karty glosu: {liczby['kart_glosu']} plikow, {liczby['bajtow']} B, "
              f"pokrycie {liczby['wymaganych']}/{liczby['wymaganych']} wymaganych NPC")
        return 0

    print(f"[BLAD] karty glosu: {sum(len(v) for v in problemy.values())} problemow "
          f"w {len(problemy)} kategoriach")
    for nazwa, wpisy in sorted(problemy.items()):
        print(f"\n{nazwa} ({len(wpisy)}):")
        for wpis in wpisy if args.check else wpisy[:12]:
            print(f"  - {wpis}")
    print("\nregula: system/npc-voice.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
