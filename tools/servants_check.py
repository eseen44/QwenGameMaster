"""Przeglad WSZYSTKICH slug, nie trzech uczestnikow biezacej sceny.

POWOD ISTNIENIA. retcon_000171: narrator wyprowadzil trzy szczury "do kratki, przy ktorej
od tygodni siedza wije" - do miejsca, w ktorym nie ma kogo spotkac. Zrodlem byla nie pomylka
pamieci, tylko trzy sprzeczne zdania w trzech plikach: instancja niosla w polu pozycji ROZKAZ
z t_186 ("mapuj teren pod gildia"), obok stala flaga "brak stalego rozkazu", a pomiar z t_091
w karcie grupowej stawial wija pod dzielnica gildii BEZ WSPOLRZEDNYCH.

Zadna kontrola tego nie widziala, bo wszystkie patrza na UCZESTNIKOW SCENY. Siec ma 36 bytow,
a scena zwykle trzech - czyli 8 procent. Reszta jest niesprawdzana od chwili wypuszczenia.

CO TA KONTROLA SPRAWDZA - wylacznie rzeczy STRUKTURALNE, po identyfikatorach i polach.
Zadnego grepowania prozy: konstrukcja odrzucona w tym repo wczesniej (DECISIONS.md) i slusznie,
bo bramka szukajaca fraz w zdaniach zglasza szum i zostaje wylaczona po tygodniu.

Uruchomienie:
    python tools/servants_check.py            # raport
    python tools/servants_check.py --check    # kod 1 przy naruszeniu (tryb bramki)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
INSTANCES = CAMPAIGN / "state" / "instances"
COMPANIONS = CAMPAIGN / "companions"

# Flagi twierdzace, ze okaz NIE MA stalego rozkazu. Dopasowanie po prefiksie, nie po frazie.
NO_ORDER_FLAG = re.compile(r"^no_standing_order")


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def instances() -> list[tuple[str, dict]]:
    index = load(INSTANCES / "index.yaml")
    out: list[tuple[str, dict]] = []
    for entry in index.get("instances") or []:
        if not isinstance(entry, dict) or entry.get("state") == "dead":
            continue
        ref = entry.get("ref")
        if not isinstance(ref, str):
            continue
        path = CAMPAIGN / ref
        if path.is_file():
            out.append((entry.get("id", path.stem), load(path)))
    return out


def active_orders(instance: dict) -> list[str]:
    return [
        str(order.get("id"))
        for order in instance.get("orders") or []
        if isinstance(order, dict) and order.get("status") == "active"
    ]


def check(wszystkie: list[tuple[str, dict]] | None = None,
          karty: dict[str, dict] | None = None) -> dict[str, list[str]]:
    """Dane sa wstrzykiwalne, zeby test nie zalezal od tego, gdzie akurat stoi siec."""
    problems: dict[str, list[str]] = {}

    def zglos(nazwa: str, opis: str) -> None:
        problems.setdefault(nazwa, []).append(opis)

    wszystkie = instances() if wszystkie is None else wszystkie

    # 1. ROZKAZ KONTRA FLAGA "BRAK ROZKAZU" - dokladnie para, ktora dala retcon_000171.
    for node_id, instance in wszystkie:
        flagi = [f for f in instance.get("status_flags") or []
                 if isinstance(f, str) and NO_ORDER_FLAG.match(f)]
        rozkazy = active_orders(instance)
        if flagi and rozkazy:
            zglos("rozkaz_kontra_flaga",
                  f"{node_id}: ma aktywny rozkaz {rozkazy} ORAZ flage {flagi} - "
                  "jedno z dwoch jest nieaktualne i nie wiadomo ktore")

    # 2. ROZKAZ UDAJACY OBSERWACJE. Silnik blokuje to przy zapisie od tury 275;
    #    ta kontrola lapie pliki, ktore juz takie sa.
    for node_id, instance in wszystkie:
        fix = (instance.get("position") or {}).get("fix")
        if isinstance(fix, dict) and fix.get("source") == "order_assumption" \
                and fix.get("status") == "confirmed":
            zglos("rozkaz_jako_obserwacja",
                  f"{node_id}: position.fix mowi confirmed przy source order_assumption - "
                  "wiadomo DOKAD okaz mial isc, nie gdzie jest")

    # 3. KARTA GRUPOWA KONTRA INSTANCJA. Karty w companions/ powtarzaja polozenie, ktore
    #    zyje w instancji. Porownanie po IDENTYFIKATORACH loc_*, nie po tresci zdania.
    pozycje = {node_id: (instance.get("position") or {}).get("location_id")
               for node_id, instance in wszystkie}
    zrodla = ({p.name: load(p) for p in sorted(COMPANIONS.glob("*.yaml"))}
              if karty is None else karty)
    for nazwa_karty, karta in sorted(zrodla.items()):
        deployment = (karta.get("deployment") or {})
        if not isinstance(deployment, dict):
            continue
        for node_id, opis in deployment.items():
            if node_id not in pozycje or not isinstance(opis, str):
                continue
            wymienione = set(re.findall(r"\bloc_[a-z0-9_]+", opis))
            biezaca = pozycje[node_id]
            if wymienione and biezaca and biezaca not in wymienione:
                zglos("karta_kontra_instancja",
                      f"{node_id}: {nazwa_karty}#deployment wymienia {sorted(wymienione)}, "
                      f"a instancja stoi w {biezaca}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="kod 1 przy naruszeniu")
    args = parser.parse_args()

    wszystkie = instances()
    problems = check()
    print(f"{'bytow w przegladzie':<28} {len(wszystkie)}")
    print(f"{'z aktywnym rozkazem':<28} "
          f"{sum(1 for _, i in wszystkie if active_orders(i))}")
    print(f"{'z okreslonym fix pozycji':<28} "
          f"{sum(1 for _, i in wszystkie if (i.get('position') or {}).get('fix'))}")
    print()

    if not problems:
        print("[OK] slugi: rozkaz, flaga i pozycja nie przecza sobie nawzajem")
        return 0

    print(f"[BLAD] {sum(len(v) for v in problems.values())} naruszen "
          f"w {len(problems)} kontrolach:")
    for nazwa, opisy in sorted(problems.items()):
        for opis in opisy:
            print(f"  - {nazwa}: {opis}")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
