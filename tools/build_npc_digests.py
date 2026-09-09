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

GLOS OSOBNO OD DANYCH (2026-09-09). Zmierzone na karcie Kesza: `knowledge` w skrocie wazylo
8 343 B, `speech_traits` 400 B - dwadziescia razy wiecej tekstu w rejestrze protokolu
audytowego niz tekstu o tym, jak ta osoba brzmi. Model imituje rejestr dominujacy
w kontekscie, wiec skrot UCZYL mowic protokolem; to retcon_000040 i retcon_000136 wchodzace
przez skrot karty, a nie przez `summary`. Dwie rzeczy sie wiec zmienily:
  - `voice` (karta glosu z entities/npcs/voices/) jest WKLEJANY NA GORE skrotu, przed
    czymkolwiek innym, i jest jedynym zrodlem glosu,
  - wersaliki emfatyczne w `claim` sa GASZONE do zwyklego zapisu. Tresc zostaje bez zmiany
    ani jednego slowa; ginie tylko krzyk, ktory byl najglosniejszym sygnalem stylu
    w calym aktywnym kontekscie. Pelna karta zachowuje oryginalna pisownie.

FAKTY BEZ ARCHIWUM PROTOKOLU (2026-09-09, iteracja 2). Wygaszenie wersalikow zdjelo krzyk,
ale nie zdjelo WAGI: `recent_confirmed` Kesza to nadal 4 482 B na 2 323 B kontraktu glosu,
czyli archiwum wazylo dwa razy tyle, ile instrukcja stylu, i to archiwum jest pisane jako
protokol tury, nie jako fakt. Dlatego skrot teraz:
  - SCINA kazdy `claim` do CLAIM_CAP znakow na granicy zdania i oznacza to
    `claim_truncated: true` plus `claim_full` ze wskazaniem na pelna karte. Fakt siedzi
    w pierwszych zdaniach; ogon jest ksiegowoscia tury ("Nieustalone:", "converging_target#...",
    "zaden zegar z tego nie powstal") i nalezy do `outcome.audit`, nie do glosu postaci,
  - podaje indeks starszych faktow w formie `fact_id@<numer tury>` zamiast pelnego
    `fact_id <- event_turn_interlude_NNN`. Indeks Seraphiny (91 wpisow) spadl z 8,5 KB
    do ~4 KB bez utraty ani jednego adresu.
Stosunek `recent_confirmed` do kontraktu glosu jest BRAMKA w tools/voice_check.py.

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
VOICES = CARDS / "voices"

# SCIECIE `claim` W SKROCIE. Pelna karta zostaje nietknieta i jest jedynym zrodlem prawdy;
# skrot ma podac FAKT, nie protokol tury. 420 znakow to okolo trzech zdan - tyle, ile
# potrzeba na "co ta postac wie i skad".
CLAIM_CAP = 420
# STOSUNEK GWARANTOWANY KONSTRUKCJA, NIE DOBRA WOLA. tools/voice_check.py egzekwuje
# recent_confirmed <= 1,5 x kontrakt glosu, ale bramka, ktora zapala sie od dopisania
# jednego faktu w turze, jest zla ergonomia: narrator nie ma jej czym naprawic poza edycja
# stalej w narzedziu. Generator schodzi wiec capem tak dlugo, az niezmiennik jest spelniony
# z zapasem, a kontrola tylko go potwierdza.
CEL_STOSUNKU = 1.2
CAP_SCHODKI = (420, 340, 280, 220, 170, 130)

# KONTRAKT GLOSU JEDZIE RAZEM Z GLOSEM. Pelna regula (system/npc-voice.md) jest osiagalna
# przez load_when_npc_speaks, ale nie siedzi w always_load - sufit always_load to 12 KB,
# a narrator.md z player-agency.md go prawie wypelniaja. Te szesc linii kosztuje ~0,5 KB
# na uczestnika i stoi dokladnie tam, gdzie narrator czyta, jak ta postac mowi.
REGULY_GLOSU = [
    "Glos bierz z voice_contract powyzej - nie z knowledge, nie z audytu, nie z retconow.",
    "Kiedy ta postac mowi, gracz widzi CO NAJMNIEJ JEDNA jej kwestie wprost.",
    "Odpowiada na JEDNA rzecz, zwykle ostatnia albo najbardziej dla siebie niewygodna.",
    "PELNY RUCH SWIATA, nie ustepstwo: gest, milczenie, zwykla odpowiedz, czesciowe "
    "niezrozumienie, zmiana tematu, czynnosc fizyczna, bledny odczyt intencji, emocja "
    "bez analizy. Diagnoza gracza NIE jest wymagana ani domyslna.",
    "Bez wyliczania ukrytych skutkow - najwyzej jeden, widziany z jej miejsca, i moze byc bledny.",
    "Wycen decyzji: zero. Literalna cena tylko wtedy, gdy scena jest o pieniadzach.",
    "'nie X, tylko Y' najwyzej raz i nie u dwoch postaci w tej samej scenie.",
    "Pelna regula, menu ruchow i test na slepo: system/npc-voice.md",
]
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


WERSALIKI = re.compile(r"(?<!\w)([A-ZĄĆĘŁŃÓŚŹŻ]{3,}(?:[ -][A-ZĄĆĘŁŃÓŚŹŻ]{1,})*)(?!\w)")
POCZATEK_ZDANIA = re.compile(r"(?:^|[.!?:;]\s+|-\s+)$")


def wygas_wersaliki(text: str) -> str:
    """Gasi emfatyczne wersaliki, nie ruszajac tresci ani identyfikatorow.

    W `claim` narrator krzyczy: "NAJZIMNIEJSZY WNIOSEK TEJ SCENY", "ZAPLATA ODDANA
    W CALOSCI", "NIEUSTALONE". To jest sygnal stylu, a nie informacja - i w skrocie karty
    stoi tuz obok kontraktu glosu, ktory jest dwadziescia razy krotszy. Identyfikatory
    (npc_..., fact_..., retcon_000162) sa pisane malymi literami, wiec ich to nie dotyczy.

    Wielka litera wraca tylko na POCZATKU ZDANIA. Bez tego warunku srodek zdania dostawal
    wielkie litery przy kazdym urwanym ciagu wersalikow ("wiedza, Nie madrosc Z Urzedu").
    """
    def zamien(match: re.Match) -> str:
        run = match.group(1)
        przed = text[:match.start()]
        return run.capitalize() if POCZATEK_ZDANIA.search(przed) or not przed else run.lower()

    return WERSALIKI.sub(zamien, text)


def wygas_w_strukturze(node: object) -> object:
    if isinstance(node, str):
        return wygas_wersaliki(node)
    if isinstance(node, list):
        return [wygas_w_strukturze(item) for item in node]
    if isinstance(node, dict):
        return {key: wygas_w_strukturze(value) for key, value in node.items()}
    return node


def utnij_claim(claim: str, cap: int = CLAIM_CAP) -> tuple[str, bool]:
    """Scina claim na granicy zdania pod CLAIM_CAP. Zwraca (tekst, czy_ucieto).

    Granica zdania, nie znakow: urwane w polowie zdanie czyta sie jako uszkodzony fakt,
    a nie jako skrot. Jesli pierwsze zdanie samo przekracza cap, zostaje cale - lepiej
    przekroczyc limit niz zgubic tresc faktu.
    """
    claim = claim.strip()
    if len(claim) <= cap:
        return claim, False
    zdania = re.split(r"(?<=[.!?])\s+", claim)
    out = ""
    for zdanie in zdania:
        if out and len(out) + 1 + len(zdanie) > cap:
            break
        out = f"{out} {zdanie}".strip()
    return (out or zdania[0]), True


# DWA SCHEMATY WPISU WIEDZY I OBA SA W UZYCIU: 18 kart pisze {fact_id, claim}, a 6 kart
# (Neris, ojciec, portier, matka, promotor, garbarz) pisze {fact} bez fact_id. Generator
# widzial tylko `claim`, wiec dla tych szesciu kart indeks starszych faktow skladal sie
# z samych znakow zapytania: 67 wpisow Neris jako "? <- event_turn_interlude_171".
# Skrot twierdzil, ze pokazuje, CO ona wie, i nie pokazywal niczego.
KLUCZE_TEKSTU = ("claim", "fact")


def tekst_wpisu(wpis: dict) -> tuple[str | None, str]:
    for klucz in KLUCZE_TEKSTU:
        if wpis.get(klucz):
            return klucz, str(wpis[klucz])
    return None, ""


def etykieta_wpisu(wpis: dict) -> str:
    """Adres wpisu w indeksie: fact_id, a gdy go nie ma - slug z pierwszych slow tekstu."""
    if wpis.get("fact_id"):
        return str(wpis["fact_id"])
    _, tekst = tekst_wpisu(wpis)
    slowa = re.findall(r"\w+", tekst.lower())[:6]
    return ("~" + "_".join(slowa)) if slowa else "?"


def scisnij_wpisy(wpisy: list, full_card: str, cap: int = CLAIM_CAP) -> list:
    """recent_confirmed ze scietym tekstem i wskazaniem, gdzie lezy calosc."""
    out = []
    for wpis in wpisy:
        if not isinstance(wpis, dict):
            out.append(wpis)
            continue
        nowy = dict(wpis)
        klucz, tresc = tekst_wpisu(nowy)
        if klucz:
            tekst, ucieto = utnij_claim(tresc, cap)
            nowy[klucz] = tekst
            if ucieto:
                nowy["claim_truncated"] = True
                nowy["claim_full"] = f"{full_card}#{etykieta_wpisu(nowy)}"
        out.append(nowy)
    return out


def bajty(obiekt: object) -> int:
    if not obiekt:
        return 0
    return len(yaml.safe_dump(obiekt, allow_unicode=True, sort_keys=False).encode("utf-8"))


def dopasuj_do_stylu(najnowsze: list, full_card: str, styl_bajtow: int) -> tuple[list, int]:
    """Scisnij recent_confirmed do CEL_STOSUNKU x kontrakt glosu. Zwraca (wpisy, uzyty_cap).

    Fakt zostaje - ginie ogon protokolu tury. Pelna karta jest nietknieta i kazdy sciety
    wpis nosi `claim_full` z adresem calosci, wiec zaden szczegol nie znika z widoku.
    """
    limit = int(CEL_STOSUNKU * styl_bajtow) if styl_bajtow else 0
    ostatnie = scisnij_wpisy(najnowsze, full_card, CAP_SCHODKI[0])
    if not limit:
        return ostatnie, CAP_SCHODKI[0]
    for cap in CAP_SCHODKI:
        ostatnie = scisnij_wpisy(najnowsze, full_card, cap)
        if bajty(ostatnie) <= limit:
            return ostatnie, cap
    return ostatnie, CAP_SCHODKI[-1]


def voice_for(stem: str) -> dict | None:
    """Karta glosu dla tej postaci albo None. Kontrola pokrycia: tools/voice_check.py."""
    path = VOICES / f"{stem}.yaml"
    if not path.exists():
        return None
    try:
        voice = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError:
        return None
    return voice if isinstance(voice, dict) else None


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


def digest_for(card: dict, recent: int, now: int, stem: str = "", voice: dict | None = None,
               full_card: str = "") -> dict:
    # GLOS PIERWSZY, PRZED DANYMI. O kolejnosci w aktywnym kontekscie decyduje ten plik,
    # a nie dobra wola czytajacego - a rejestr dominujacy w kontekscie jest tym, ktory
    # model imituje.
    out: dict = {}
    if voice is not None:
        out["voice_ref"] = f"{VOICES.relative_to(ROOT).as_posix()}/{stem}.yaml"
        osie = voice.get("voice_contract") if isinstance(voice.get("voice_contract"), dict) else None
        out["voice_contract"] = osie if osie is not None else {
            key: value for key, value in voice.items()
            if key not in ("schema_version", "object_type", "id", "npc_id", "npc_ref", "samples")}
        if voice.get("samples"):
            out["voice_samples"] = list(voice["samples"])
        out["voice_rules"] = list(REGULY_GLOSU)
    else:
        out["voice_missing"] = (
            "BRAK KARTY GLOSU - nie ukladaj kwestii z knowledge ani z audytu. "
            "Zaloz plik w entities/npcs/voices/ (system/npc-voice.md)."
        )
        out["voice_rules"] = list(REGULY_GLOSU)
    # JEDNO ZRODLO GLOSU. Karta glosu zastepuje `speech_traits`, a nie stoi obok nich -
    # dwie listy o tym samym roznia sie zawsze i wygrywa dluzsza. `speech_traits` zostaja
    # w skrocie wylacznie dla postaci, ktore karty glosu jeszcze nie maja.
    pola = tuple(f for f in PLAY_FIELDS if f != "speech_traits" or voice is None)
    out.update({key: card[key] for key in pola if key in card})
    out["object_type"] = "npc_digest"
    out["full_card"] = full_card or None
    knowledge = card.get("knowledge") or {}
    confirmed = [entry for entry in (knowledge.get("confirmed") or []) if isinstance(entry, dict)]
    confirmed.sort(key=lambda entry: turn_number(entry.get("source_event_id")), reverse=True)

    najnowsze = confirmed[:recent]
    reszta = confirmed[recent:]
    ostatnia = turn_number(najnowsze[0].get("source_event_id")) if najnowsze else -1

    # WAGA STYLU LICZONA PRZED WIEDZA. Kontrakt glosu jest juz w `out`, wiec jego rozmiar
    # jest znany i wiedza moze sie do niego dopasowac - a nie odwrotnie.
    styl_bajtow = (bajty(out.get("voice_contract")) + bajty(out.get("voice_rules"))
                   + bajty(out.get("voice_samples")))
    dopasowane, uzyty_cap = dopasuj_do_stylu(
        wygas_w_strukturze(najnowsze), full_card, styl_bajtow)

    out["knowledge"] = {
        "register_note": (
            "TO SA DANE, NIE PROBKA MOWY. Ponizsze `claim` sa zapisem protokolu tury: "
            "mowia, CO postac wie, nigdy JAK mowi. Glos bierz wylacznie z `voice` na gorze "
            "tego skrotu (system/npc-voice.md). Wersaliki emfatyczne sa tu wygaszone "
            "celowo - pelna karta zachowuje oryginalna pisownie."
        ),
        "claim_cap_chars": uzyty_cap,
        "recent_confirmed": dopasowane,
        # INDEKS ADRESOWY, NIE OPIS. `fact_id@numer_tury` zamiast pelnego event_id:
        # ten sam adres, o trzydziesci procent mniej bajtow, a bajty w tym pliku odpychaja
        # kontrakt glosu od miejsca, w ktorym narrator sklada kwestie.
        "older_confirmed_index": [
            f"{etykieta_wpisu(entry)}@{turn_number(entry.get('source_event_id'))}"
            for entry in reszta
        ],
        "suspicions": wygas_w_strukturze(knowledge.get("suspicions") or []),
        "false_beliefs": wygas_w_strukturze(knowledge.get("false_beliefs") or []),
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
        full_card = path.relative_to(ROOT).as_posix()
        digest = digest_for(card, recent, now, path.stem, voice_for(path.stem), full_card)
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
