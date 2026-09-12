"""Kontrola rejestru zapasu: czy liczby domykaja sie same ze soba.

POWOD ISTNIENIA. retcon_000170 i 000173. Narrator polozyl graczowi na stole porcje
tlumiaca rozklad, ktora zostala zuzyta 97 tur wczesniej - bo `contents_summary` w ekwipunku
opisywal stan sprzed zuzycia, a rejestr w resources.yaml nikt nie domknal. Zadna bramka
tego nie widziala: audit_refs sprawdzal, czy SCIEZKI istnieja, a nie czy LICZBY sie zgadzaja.

CZEGO TA KONTROLA NIE ROBI. Nie czyta prozy i nie ocenia, czy zdanie w karcie towarzysza
opisuje stan dzisiejszy, czy ocene sprzed stu tur - do tego sluzy `scan_item_claims.py`,
uruchamiany przez czlowieka. Bramka szukajaca fraz w zdaniach zglasza szum i zostaje
wylaczona po tygodniu; ta sprawdza wylacznie rzeczy, ktore albo sie zgadzaja, albo nie.

Uruchomienie:
    python tools/audit_stock.py            # raport
    python tools/audit_stock.py --check    # kod 1 przy naruszeniu (tryb bramki)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
RESOURCES = CAMPAIGN / "state" / "resources.yaml"
INVENTORY = CAMPAIGN / "player" / "inventory.yaml"
INSTANCES = CAMPAIGN / "state" / "instances" / "index.yaml"

STATUSES = {"available", "consumed", "disputed"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {} if path.is_file() else {}


def records() -> list[tuple[str, dict]]:
    out = []
    for cache in load(RESOURCES).get("caches") or []:
        for entry in cache.get("contents") or []:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                out.append((cache.get("id", "?"), entry))
    return out


def known_instances() -> set[str]:
    return {
        entry["id"] for entry in load(INSTANCES).get("instances") or []
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }


def check() -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}

    def zglos(nazwa: str, opis: str) -> None:
        problems.setdefault(nazwa, []).append(opis)

    instancje = known_instances()

    for cache_id, entry in records():
        item_id = entry["id"]
        quantity = entry.get("quantity")
        status = entry.get("status")

        # K2. Kazdy rekord ma ILOSC jako liczbe i STATUS ze slownika.
        if not isinstance(quantity, (int, float)):
            zglos("rekord_niepelny",
                  f"{item_id}: quantity to {quantity!r}, nie liczba - z wartosci prozatorskiej "
                  "nie da sie nic odjac, a narrator bedzie zgadywal")
        if status is None:
            zglos("rekord_niepelny", f"{item_id}: brak pola status")
        elif status not in STATUSES:
            zglos("rekord_niepelny",
                  f"{item_id}: status '{status}' - dozwolone {sorted(STATUSES)}")

        # K3. Zero i "zuzyte" to ta sama rzecz powiedziana dwa razy; maja sie zgadzac.
        if isinstance(quantity, (int, float)) and status in {"available", "consumed"}:
            if quantity == 0 and status != "consumed":
                zglos("zero_kontra_status",
                      f"{item_id}: quantity 0, a status '{status}' - czego nie ma, tego nie ma")
            if quantity > 0 and status == "consumed":
                zglos("zero_kontra_status",
                      f"{item_id}: status consumed przy quantity {quantity}")

        # K1. Zuzycie musi miec DATE i istniejacego odbiorce - inaczej nie da sie
        #     odtworzyc, kiedy i na co poszlo, a wlasnie tego zabraklo przy t_177.
        if status == "consumed":
            if not entry.get("consumed_event_id"):
                zglos("zuzycie_bez_sladu", f"{item_id}: status consumed bez consumed_event_id")
            odbiorcy = entry.get("consumed_on")
            odbiorcy = odbiorcy if isinstance(odbiorcy, list) else [odbiorcy] if odbiorcy else []
            for odbiorca in odbiorcy:
                if isinstance(odbiorca, str) and odbiorca not in instancje:
                    zglos("zuzycie_bez_sladu",
                          f"{item_id}: consumed_on wskazuje '{odbiorca}', "
                          "ktorego nie ma w indeksie instancji")

    # K4. Sumy waluty. Przy rozjezdzie ODMOWA i raport, nigdy ciche przeliczenie -
    #     przeliczenie rozstrzygaloby, ktora strona jest bledna, a tego nikt nie wie.
    currency = load(INVENTORY).get("currency") or {}
    skladniki = [
        wartosc for klucz, wartosc in currency.items()
        if klucz.endswith("_silver") and isinstance(wartosc, (int, float))
        and klucz not in {"liquid_silver_available_now", "total_known_net_silver",
                          "syndicate_payout_outstanding_silver", "refundable_deposits_silver"}
    ]
    liquid = currency.get("liquid_silver_available_now")
    depozyty = currency.get("refundable_deposits_silver", 0)
    total = currency.get("total_known_net_silver")
    if isinstance(liquid, (int, float)) and skladniki and sum(skladniki) != liquid:
        zglos("sumy_waluty",
              f"skladniki daja {sum(skladniki)}, a liquid_silver_available_now to {liquid} - "
              "NIE przeliczam po cichu, bo to rozstrzygaloby, ktora strona jest bledna")
    if isinstance(total, (int, float)) and isinstance(liquid, (int, float)):
        if liquid + depozyty != total:
            zglos("sumy_waluty",
                  f"liquid {liquid} + depozyty {depozyty} != total_known_net_silver {total}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="kod 1 przy naruszeniu")
    args = parser.parse_args()

    wszystkie = records()
    zuzyte = [e for _, e in wszystkie if e.get("status") == "consumed"]
    problems = check()

    print(f"{'pozycji w rejestrze':<28} {len(wszystkie)}")
    print(f"{'zuzytych':<28} {len(zuzyte)}")
    print()
    if not problems:
        print("[OK] zapas: ilosci, statusy, slady zuzycia i sumy waluty sie zgadzaja")
        print("     UWAGA: to NIE sprawdza, czy karty i leady nie twierdza czegos innego -")
        print("     do tego jest tools/scan_item_claims.py --consumed-only.")
        return 0

    print(f"[BLAD] {sum(len(v) for v in problems.values())} naruszen "
          f"w {len(problems)} kontrolach:")
    for nazwa, opisy in sorted(problems.items()):
        for opis in opisy:
            print(f"  - {nazwa}: {opis}")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
