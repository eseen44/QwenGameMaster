"""Kontrola kontraktow glosu NPC: pokrycie, osie, dlugosc, rejestr, rozroznialnosc i WAGA STYLU.

DLACZEGO TO ISTNIEJE, ZMIERZONE. Glos NPC nie mial wlasnego zrodla. Karta miala
`speech_traits` - trzy wypunktowania, ~0,4 KB - obok `knowledge`, ktore w skrocie karty
Kesza wazylo 8,3 KB i bylo napisane rejestrem protokolu audytowego (wersaliki, "WNIOSKU NIE
WYCIAGNAL NA GLOS", "NIEUSTALONE:", odwolania do plikow). Stosunek 20:1 na rzecz protokolu
w tym samym aktywnym kontekscie znaczy, ze model imituje protokol, bo protokol jest tam
rejestrem dominujacym. To jest retcon_000040 i retcon_000136 wchodzace przez skrot karty.

Dwie z trzech linii `speech_traits` Kesza kazaly mu wprost wyceniac ("Wycenia, nie bramkuje:
mowi to kosztuje tyle"), a pierwsza linia Seraphiny kazala nazywac CENE kazdej rzeczy przed
zgoda - czyli zrodlo wejsciowe uczylo dokladnie tego, czego retcon_000162 zabronil w prozie.

CO SPRAWDZA (wszystko BLOKUJACE - kazde twierdzenie jest maszynowo sprawdzalne):
  1. brak_kontraktu     - wazny NPC nie ma pliku w entities/npcs/voices/
  2. brak_osi           - kontrakt nie ma wszystkich osi (albo os jest pusta)
  3. kontrakt_za_dlugi  - powyzej LIMIT_BAJTOW; kontrakt przestaje byc kontraktem
  4. rejestr_wyceny     - kontrakt uzywa slownika wyceny/audytu poza polem `avoid`,
                          czyli uczy tego, czego ma nie uczyc (retcon_000162)
  5. glos_nierozroznialny - dwie karty maja te sama os slowo w slowo
  6. kontrakt_bez_npc   - plik glosu wskazuje na npc_id, ktorego nie ma
  7. probka_nie_jest_kwestia - `samples` musza byc wypowiedziami, nie opisami
  8. szablon_w_probce   - "nie X, tylko Y" u wiecej niz jednej postaci
  9. wiedza_zalewa_styl - w skrocie karty `knowledge.recent_confirmed` wazy wiecej niz
                          MAX_STOSUNEK x kontrakt glosu. To jest cala diagnoza w jednej
                          liczbie: przy 20:1 model imituje archiwum, nie kontrakt.
 10. dwa_zrodla_glosu  - karta NPC z kontraktem glosu nadal ma `speech_traits`. Dwie listy
                          o tym samym rozjezdzaja sie i wygrywa dluzsza; ta konkretna
                          uczyla wyceniania i narrator powolywal sie na nia w audytach
                          tur 240, 242, 244 i 245.

POLE `avoid` JEST JEDYNYM WYJATKIEM od zakazu slownika wyceny. Kontrakt ma byc POZYTYWNY -
mowic, jak ta osoba mowi - a jedno pole na "czego u niej nie nadużywać" jest potrzebne,
zeby dalo sie nazwac konstrukcje, ktora wlasnie sie zdegenerowala. Jedno pole, nie caly plik.

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

# OSIE KONTRAKTU. Kolejnosc jest kolejnoscia czytania: najpierw jak brzmi zdanie, potem ile
# go jest, potem czym mowi, a dopiero na koncu czego nie widzi i czego nie nadużywac.
OSIE = (
    "sentences",        # dlugosc i budowa zdan
    "answer_length",    # domyslna dlugosc odpowiedzi
    "register",         # slownictwo i rejestr
    "evasion",          # sposob unikania odpowiedzi
    "body",             # fizyczne odruchy
    "mistakes",         # typowe bledy i ograniczenia
    "unnoticed",        # czego zwykle nie zauwaza
    "emotion",          # jak okazuje emocje
    "blind_spot",       # czego sam nie potrafi nazwac
    "money",            # kiedy w ogole mowi o pieniadzach
    "avoid",            # konstrukcje, ktorych u niej nie nadużywac
)
OS_NEGATYWNA = "avoid"
LIMIT_BAJTOW = 2800
PROBKI_MIN, PROBKI_MAX = 2, 4

# Kontrakt glosu ma miec realna wage stylistyczna wobec archiwum wiedzy w tym samym pliku.
# 1,5 nie jest liczba z powietrza: przed ta naprawa stosunek wynosil 20, po wprowadzeniu
# kontraktu 1,1-2,5, a po scisnieciu `claim` w skrocie schodzi pod 1.
MAX_STOSUNEK = 1.5

REJESTR_WYCENY = re.compile(
    r"(?iu)\b("
    r"cen[aeyoęą]\w*|wycen\w*|koszt\w*|wartoś\w*|wartos\w*|"
    r"rachun\w*|opłacal\w*|oplacal\w*|bilans\w*|"
    r"ekspozycj\w*|aktyw\w*|przelicz\w*|kalkul\w*|audyt\w*|"
    r"zmierzon\w*|nierozstrzygni\w*"
    r")\b"
)
SZABLON_NIE_TYLKO = re.compile(r"(?iu)\bnie\b[^,.;!?]{1,70},\s*tylko\b")
# PROBKA MA BYC KWESTIA, NIE RELACJA O KWESTII - i to sie rozpoznaje dwiema scislymi
# rzeczami, nie morfologia czasownika. Wzorzec po morfologii zglaszal "Powiedziales kilka.
# Ile to jest kilka." (dobra kwestia w drugiej osobie) i przepuszczal "Bede stal obok".
#   1. MOWA ZALEZNA: czasownik mowienia + spojnik podrzedny. To jest wada z reklamacji.
#   2. WLASNE IMIE: postac nie opowiada o sobie w trzeciej osobie, wiec obecnosc jej
#      wlasnego imienia w "kwestii" znaczy, ze to opis ("Kesz ocenil ryzyko").
OPIS_NIE_KWESTIA = re.compile(
    r"(?iu)\b("
    r"powiedzia[lł]a?|zapyta[lł]a?|doda[lł]a?|stwierdzi[lł]a?|odnotowa[lł]a?|"
    r"oceni[lł]a?|wyceni[lł]a?|uzasadni[lł]a?|skwitowa[lł]a?|nazwa[lł]a?"
    r")\s*,?\s+(że|ze|iż|iz|czy|co|ile|jak|dlaczego|kto|gdzie|kiedy|czego)\b"
)


def probka_jest_opisem(probka: str, imie: str | None) -> str | None:
    """Zwraca powod, dla ktorego to nie jest kwestia, albo None."""
    if OPIS_NIE_KWESTIA.search(probka):
        return "mowa zalezna zamiast kwestii"
    for czlon in (imie or "").split():
        if len(czlon) > 2 and re.search(rf"\b{re.escape(czlon)}\b", probka):
            return f"postac mowi o sobie w trzeciej osobie ({czlon})"
    return None


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def bajty(obiekt: object) -> int:
    if not obiekt:
        return 0
    return len(yaml.safe_dump(obiekt, allow_unicode=True, sort_keys=False).encode("utf-8"))


def wymagane() -> dict[str, Path]:
    """{stem karty NPC: sciezka karty} dla postaci, ktore MUSZA miec kontrakt glosu."""
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
        if card.get("importance") == "full_agent" or (DIGESTS / path.name).exists():
            out[path.stem] = path
    return out


def normalizuj(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def kontrakt(voice: dict) -> dict:
    """Osie kontraktu. Znosi tez stary, plaski uklad z pierwszej iteracji."""
    blok = voice.get("voice_contract")
    return blok if isinstance(blok, dict) else voice


def check() -> tuple[dict[str, list[str]], dict[str, object]]:
    problemy: dict[str, list[str]] = {}
    liczby: dict[str, object] = {"wymaganych": 0, "kontraktow": 0, "bajtow": 0,
                                 "najgorszy_stosunek": 0.0}

    def zglos(nazwa: str, opis: str) -> None:
        problemy.setdefault(nazwa, []).append(opis)

    npc_ids: dict[str, str] = {}
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
            zglos("brak_kontraktu",
                  f"{card_path.relative_to(ROOT).as_posix()} -> brakuje "
                  f"entities/npcs/voices/{stem}.yaml")

    osie_widziane: dict[tuple[str, str], str] = {}
    szablon_u: list[str] = []

    for path in sorted(VOICES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        liczby["kontraktow"] = int(liczby["kontraktow"]) + 1
        rozmiar = path.stat().st_size
        liczby["bajtow"] = int(liczby["bajtow"]) + rozmiar
        krotko = path.relative_to(ROOT).as_posix()
        try:
            voice = load(path)
        except yaml.YAMLError as blad:
            zglos("brak_osi", f"{krotko}: nieczytelny YAML ({blad})")
            continue
        osie = kontrakt(voice)

        if rozmiar > LIMIT_BAJTOW:
            zglos("kontrakt_za_dlugi",
                  f"{krotko}: {rozmiar} B > {LIMIT_BAJTOW} B - kontrakt glosu ma byc krotki")

        if voice.get("npc_id") not in npc_ids:
            zglos("kontrakt_bez_npc", f"{krotko}: npc_id {voice.get('npc_id')!r} bez karty NPC")
        else:
            karta = CARDS / f"{npc_ids[voice['npc_id']]}.yaml"
            if "speech_traits" in load(karta):
                zglos("dwa_zrodla_glosu",
                      f"{karta.relative_to(ROOT).as_posix()}: ma kontrakt glosu I "
                      f"`speech_traits` - zostaw jedno zrodlo (system/npc-voice.md)")

        for os_ in OSIE:
            if not normalizuj(osie.get(os_)):
                zglos("brak_osi", f"{krotko}: brak albo pusta os '{os_}'")
                continue
            klucz = (os_, normalizuj(osie[os_]))
            if klucz in osie_widziane:
                zglos("glos_nierozroznialny",
                      f"{krotko} ma os '{os_}' identyczna jak {osie_widziane[klucz]}")
            else:
                osie_widziane[klucz] = krotko

        probki = voice.get("samples")
        if not isinstance(probki, list) or not PROBKI_MIN <= len(probki) <= PROBKI_MAX:
            zglos("brak_osi",
                  f"{krotko}: potrzebne od {PROBKI_MIN} do {PROBKI_MAX} 'samples' - kwestie wprost")
            probki = probki if isinstance(probki, list) else []
        imie = None
        if voice.get("npc_id") in npc_ids:
            imie = load(CARDS / f"{npc_ids[voice['npc_id']]}.yaml").get("name")
        for probka in probki:
            powod = probka_jest_opisem(str(probka), imie)
            if powod:
                zglos("probka_nie_jest_kwestia",
                      f"{krotko}: {powod}: {str(probka)[:60]}")

        # Zakaz slownika wyceny NIE dotyczy pola `avoid` - to jedyne miejsce, w ktorym
        # wolno nazwac konstrukcje do unikania.
        pozytywne = {k: v for k, v in osie.items() if k != OS_NEGATYWNA}
        tresc = yaml.safe_dump(pozytywne, allow_unicode=True) + yaml.safe_dump(probki, allow_unicode=True)
        trafienia = sorted({m.group(0).lower() for m in REJESTR_WYCENY.finditer(tresc)})
        if trafienia:
            zglos("rejestr_wyceny",
                  f"{krotko}: slownik wyceny/audytu poza polem '{OS_NEGATYWNA}': "
                  + ", ".join(trafienia))

        if SZABLON_NIE_TYLKO.search(" ".join(str(s) for s in probki)):
            szablon_u.append(krotko)

    if len(szablon_u) > 1:
        zglos("szablon_w_probce",
              "konstrukcja 'nie X, tylko Y' w probkach wiecej niz jednej postaci: "
              + ", ".join(szablon_u))

    # WAGA STYLU. Ta jedna liczba jest cala diagnoza: jesli archiwum wiedzy w skrocie karty
    # wazy wielokrotnie wiecej niz kontrakt glosu, model imituje archiwum.
    for path in sorted(DIGESTS.glob("*.yaml")):
        digest = load(path)
        # Styl liczony DOKLADNIE tak samo jak w generatorze (build_npc_digests.digest_for),
        # inaczej bramka i konstrukcja mierza dwie rozne rzeczy i jedna z nich klamie.
        styl = (bajty(digest.get("voice_contract")) + bajty(digest.get("voice_rules"))
                + bajty(digest.get("voice_samples")))
        wiedza = bajty((digest.get("knowledge") or {}).get("recent_confirmed"))
        if not styl:
            continue
        stosunek = wiedza / styl
        liczby["najgorszy_stosunek"] = max(float(liczby["najgorszy_stosunek"]), stosunek)
        if stosunek > MAX_STOSUNEK:
            zglos("wiedza_zalewa_styl",
                  f"{path.relative_to(ROOT).as_posix()}: recent_confirmed {wiedza} B na "
                  f"{styl} B kontraktu glosu = {stosunek:.1f}x (max {MAX_STOSUNEK}); "
                  f"zmniejsz CLAIM_CAP w tools/build_npc_digests.py")

    return problemy, liczby


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="tylko wynik, kod 1 przy bledzie")
    args = parser.parse_args()

    problemy, liczby = check()
    if not problemy:
        print(f"[OK] kontrakty glosu: {liczby['kontraktow']} plikow, {liczby['bajtow']} B, "
              f"pokrycie {liczby['wymaganych']}/{liczby['wymaganych']} waznych NPC, "
              f"wiedza/styl najgorzej {float(liczby['najgorszy_stosunek']):.2f}x "
              f"(max {MAX_STOSUNEK})")
        return 0

    print(f"[BLAD] kontrakty glosu: {sum(len(v) for v in problemy.values())} problemow "
          f"w {len(problemy)} kategoriach")
    for nazwa, wpisy in sorted(problemy.items()):
        print(f"\n{nazwa} ({len(wpisy)}):")
        for wpis in wpisy if args.check else wpisy[:12]:
            print(f"  - {wpis}")
    print("\nregula: system/npc-voice.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
