"""Kontrakt prozy tury: wycena metaforyczna, mowa zalezna, dialog wprost, szablon "nie X, tylko Y".

DLACZEGO TO ISTNIEJE, ZMIERZONE 2026-09-09. `outcome.prose` nie mialo zadnego kontraktu:
nie ma go w templates/journal/turn-outcome.yaml, nie sprawdza go commit, a AGENTS.md poswieca
mu jedno zdanie. Wychodzilo z tego STRESZCZENIE PROTOKOLU zapisane zdaniami - i to samo
streszczenie `gm recent` podaje przy otwarciu nastepnej sesji jako JEDYNA probke prozy.
Petla domyka sie sama: tura 248 uczy tury 249, ze proza to relacja pośrednia w rejestrze
narratora. W turach 236-248 (13 wpisow `authored`) nie ma ani jednej kwestii wprost, a mowy
zaleznej ("powiedzial, ze...", "wycenil", "uzasadnil rachunkiem") jest kilkadziesiat.

CO ROZROZNIA. Naiwny zakaz slowa "cena" byl by bezuzyteczny, bo scena u wagi syndykatu MA
byc o kwotach. Kontrola patrzy wiec na SASIEDZTWO: trafienie ze slownika wyceny, przy ktorym
w promieniu OKNO znakow stoi realny znacznik pieniedzy (srebro, honorarium, zaplata, kwota,
czynsz, liczba z waluta), jest LITERALNE i nie jest zgloszone. Trafienie bez takiego
znacznika jest wycenianiem decyzji, czyli tym, co zabronil retcon_000162.

BRAMKA JEST JEDNA I POCHODZI Z KANONU. retcon_000162 mowi: "policz zdania o wartosci, cenie,
rachunku, oplacalnosci; wiecej niz jedno - przepisz". Dokladnie to jest warunkiem dla NOWEJ
prozy (numer tury > BASELINE). Reszta - gestosc mowy zaleznej, brak dialogu, szablon
"nie X, tylko Y" - jest RAPORTEM, bo wymaga decyzji redakcyjnej, a walidator swiecacy na
czerwono bez przerwy jest ignorowany (patrz AGENTS.md#Kontrole przed commitem).

Uruchomienie:
    python tools/prose_check.py                 # raport z ostatnich 20 tur
    python tools/prose_check.py --limit 40
    python tools/prose_check.py --new-only      # bramka: tylko tury powyzej baseline
    python tools/prose_check.py --text "..."    # ocena pojedynczego fragmentu
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "campaigns" / "lucan" / "journal" / "events.jsonl"

# BASELINE. Proza do tury 248 wlacznie jest dlugiem historycznym - raportowanym, nigdy
# blokujacym; tego tekstu nie wolno przepisywac (AGENTS.md#Aktualizacja pamieci). Podniesienie
# tej liczby jest cofnieciem zapadki i wolno je zrobic tylko po splaceniu dlugu.
BASELINE_TURN = 248

LIMIT_WYCEN = 1          # retcon_000162: wiecej niz jedno zdanie o cenie - przepisz
LIMIT_MOWY_ZALEZNEJ = 3  # tyle parafraz przy ZERO kwestiach wprost to juz nie skracanie
OKNO = 90                # promien w znakach, w ktorym szukamy znacznika pieniedzy

SLOWNIK_WYCENY = re.compile(
    r"(?iu)\b("
    r"cen[aeyoęą]\w*|wycen\w*|koszt\w*|wartoś\w*|wartos\w*|"
    r"rachun\w*|opłacal\w*|oplacal\w*|bilans\w*|przelicz\w*"
    r")\b"
)

# Realne pieniadze. Celowo WASKIE: "kupuje grunt pod przyszlosc" i "placi za to nastepny"
# to metafory, wiec ogolne kupic/placic tu nie wchodzi.
ZNACZNIK_PIENIEDZY = re.compile(
    r"(?iu)("
    r"srebr\w*|złot\w*|zlot\w*|miedziak\w*|"
    r"honorari\w*|zapłat\w*|zaplat\w*|wynagrodz\w*|prowizj\w*|zadatek\w*|zaliczk\w*|"
    r"kwot\w*|pieniądz\w*|pieniedz\w*|pieniądz\w*|sakiew\w*|utarg\w*|czynsz\w*|"
    r"stawk[aięęy]\w*|\d+\s*(?:sr|zl|zł)\b|za sztukę|za sztuke"
    r")"
)

MOWA_ZALEZNA = re.compile(
    r"(?iu)\b("
    r"powiedzia\w+|dodał\w*|dodal\w*|zapytał\w*|zapytal\w*|stwierdzi\w+|uznał\w*|uznal\w*|"
    r"odnotował\w*|odnotowal\w*|przyznał\w*|przyznal\w*|zauważył\w*|zauwazyl\w*|"
    r"wyjaśnił\w*|wyjasnil\w*|odpowiedział\w*|odpowiedzial\w*|oświadczy\w+|oswiadczy\w+|"
    r"zapowiedzia\w+|skwitował\w*|skwitowal\w*|nazwał\w*|nazwal\w*|"
    r"wycenił\w*|wycenil\w*|policzy\w+|uzasadni\w+"
    r")\s*,?\s+(że|ze|iż|iz|czy|co|ile|jak|dlaczego|kto|gdzie|kiedy|komu|czego)\b"
)

# Dialog wprost: myslnik dialogowy na poczatku linii albo cudzysłowy polskie/proste.
# CUDZYSLOW MUSI OBEJMOWAC ZDANIE, nie slowo. Bez tego pojedyncze "nie da sie" i
# "prostodusznego" - a wlasnie tak cudzyslow jest w tej prozie uzywany - liczyly sie jako
# kwestia i licznik dialogu pokazywal 3 tam, gdzie kwestii nie ma ani jednej.
DIALOG_MYSLNIK = re.compile(r"(?m)^\s*[—–-]\s*\w")
DIALOG_CYTAT = re.compile(r'(„[^”]{12,}”)|("[^"]{12,}")|(«[^»]{12,}»)')


def kwestie_wprost(text: str) -> int:
    ile = len(DIALOG_MYSLNIK.findall(text))
    for match in DIALOG_CYTAT.finditer(text):
        srodek = match.group(0)[1:-1]
        if " " in srodek.strip() and len(srodek.split()) >= 3:
            ile += 1
    return ile

SZABLON_NIE_TYLKO = re.compile(
    r"(?iu)(\bnie\b[^,.;!?]{1,70},\s*tylko\b)|(\bnie dlatego[^,.;!?]{0,40},\s*(tylko|ale)\b)"
)


def wyceny_metaforyczne(text: str) -> list[str]:
    """Trafienia ze slownika wyceny, przy ktorych NIE stoi znacznik realnych pieniedzy."""
    out = []
    for match in SLOWNIK_WYCENY.finditer(text):
        start = max(0, match.start() - OKNO)
        koniec = min(len(text), match.end() + OKNO)
        if ZNACZNIK_PIENIEDZY.search(text[start:koniec]):
            continue          # rozmowa o pieniadzach, nie wycenianie decyzji
        lewo = max(0, match.start() - 35)
        out.append(text[lewo:match.end() + 35].replace("\n", " ").strip())
    return out


def zmierz(text: str) -> dict:
    text = text or ""
    metafory = wyceny_metaforyczne(text)
    return {
        "znaki": len(text),
        "wyceny_metaforyczne": len(metafory),
        "wyceny_fragmenty": metafory,
        "mowa_zalezna": len(MOWA_ZALEZNA.findall(text)),
        "dialog_wprost": kwestie_wprost(text),
        "szablon_nie_tylko": len(SZABLON_NIE_TYLKO.findall(text)),
    }


def numer_tury(event_id: object) -> int:
    if not isinstance(event_id, str):
        return -1
    cyfry = [chunk for chunk in event_id.replace("-", "_").split("_") if chunk.isdigit()]
    return int(cyfry[-1]) if cyfry else -1


def wpisy() -> list[dict]:
    if not EVENTS.exists():
        return []
    out = []
    for line in EVENTS.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--new-only", action="store_true",
                        help="bramka: blokuje wylacznie tury powyzej baseline")
    parser.add_argument("--text", help="oceń podany fragment i wyjdz")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.text:
        pomiar = zmierz(args.text)
        print(json.dumps(pomiar, ensure_ascii=False, indent=2))
        return 1 if pomiar["wyceny_metaforyczne"] > LIMIT_WYCEN else 0

    wszystkie = wpisy()[-max(1, args.limit):]
    wybrane = [e for e in wszystkie if (e.get("prose") or "").strip()]
    if not wybrane:
        print("[OK] brak prozy autorskiej do sprawdzenia")
        return 0

    zle: list[str] = []
    raport: list[str] = []
    suma = {"wyceny_metaforyczne": 0, "mowa_zalezna": 0, "dialog_wprost": 0,
            "szablon_nie_tylko": 0, "znaki": 0}

    for event in wybrane:
        pomiar = zmierz(event.get("prose"))
        for key in suma:
            suma[key] += pomiar[key]
        tura = numer_tury(event.get("id"))
        flagi = []
        if pomiar["wyceny_metaforyczne"] > LIMIT_WYCEN:
            flagi.append(f"wycen metaforycznych: {pomiar['wyceny_metaforyczne']}")
            if tura > BASELINE_TURN:
                zle.append(f"{event.get('id')}: {pomiar['wyceny_metaforyczne']} wycen "
                           f"metaforycznych (limit {LIMIT_WYCEN}, retcon_000162); pierwsze: "
                           + " | ".join(pomiar["wyceny_fragmenty"][:3]))
        if pomiar["mowa_zalezna"] >= 2 and pomiar["dialog_wprost"] == 0:
            flagi.append(f"mowa zalezna {pomiar['mowa_zalezna']}x, dialogu wprost ZERO")
            # Ta sama bramka, ktora ma turn commit (gm_runtime.validate_prose_contract):
            # trzy albo wiecej parafraz przy zero kwestiach wprost to tura rozmowy, w ktorej
            # gracz nie uslyszal nikogo. Dwie parafrazy sa jeszcze skracaniem.
            if tura > BASELINE_TURN and pomiar["mowa_zalezna"] >= LIMIT_MOWY_ZALEZNEJ:
                zle.append(f"{event.get('id')}: {pomiar['mowa_zalezna']} konstrukcji mowy "
                           f"zaleznej i ZERO kwestii wprost - gdy postac mowi, gracz ma "
                           f"zobaczyc co najmniej jedna jej kwestie")
        if pomiar["szablon_nie_tylko"] > 1:
            flagi.append(f"szablon 'nie X, tylko Y': {pomiar['szablon_nie_tylko']}")
        if flagi:
            raport.append(f"  {event.get('id')} ({pomiar['znaki']} zn.): " + "; ".join(flagi))

    if not args.quiet:
        # PRZECHYL PROZA / PROTOKOL. Zmierzone 2026-09-09 na 20 turach: 15 972 znakow prozy
        # na 115 819 znakow audytu, czyli 7,3x. To nie jest bramka - audyt ma byc techniczny
        # (retcon_000162) - ale przechyl, ktorego nikt nie liczy, wraca.
        audyt = sum(len(e.get("audit") or e.get("summary") or "") for e in wszystkie)
        proza_all = sum(len(e.get("prose") or e.get("prose_auto") or "") for e in wszystkie)
        if proza_all:
            print(f"przechyl proza/protokol na {len(wszystkie)} turach: proza {proza_all} zn., "
                  f"audyt {audyt} zn. - protokol {audyt / proza_all:.1f}x wiekszy")
            print("  (audyt ma byc szczegolowy, ale NIE ma powtarzac tego, co sprawdza "
                  "checker - patrz AGENTS.md#audyt-nie-jest-samo-raportem)")
        print(f"proza autorska: {len(wybrane)} tur, {suma['znaki']} znakow")
        print(f"  wyceny metaforyczne: {suma['wyceny_metaforyczne']}")
        print(f"  mowa zalezna:        {suma['mowa_zalezna']}")
        print(f"  kwestie wprost:      {suma['dialog_wprost']}")
        print(f"  'nie X, tylko Y':    {suma['szablon_nie_tylko']}")
        if raport:
            print("\nUWAGA (raport, nie bramka - poza turami powyzej baseline):")
            print("\n".join(raport))

    if zle:
        print(f"\n[BLAD] {len(zle)} nowych tur lamie kontrakt prozy:")
        for wpis in zle:
            print(f"  - {wpis}")
        print("\nregula: system/npc-voice.md, retcon_000162")
        return 1

    if args.new_only:
        print(f"[OK] proza powyzej tury {BASELINE_TURN} spelnia kontrakt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
