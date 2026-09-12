"""Liczby, ktore zyja WYLACZNIE w prozie tury - i nigdzie poza nia.

POWOD ISTNIENIA. Trzy retcony z jednego miesiaca naprawialy to samo: stawke podana
w narracji, ktorej nie bylo w zadnej operacji ani w zadnym pliku stanu.
  - retcon_000165 - wyliczenie ogloszone i niezastosowane,
  - retcon_000167 - doplyw 1,8 na dobe nazwany w prozie przed wpisaniem do rejestru,
  - retcon_000172B - deficyt 1,0 na dobe policzony przy stole i podany graczowi jako fakt.
Liczba w prozie wyglada na pomiar. Jesli nie ma jej w operacjach ani w plikach, jest
najwyzej intencja - a gracz czyta ja jak stan.

CO TO ROBI. Przechodzi zacommitowane transakcje, wyciaga z `outcome.summary` i `prose`
liczby niosace JEDNOSTKE MECHANICZNA (na dobe, jednostek, sekund) i sprawdza, czy ta sama
liczba wystepuje gdziekolwiek w `operations` tej tury. Brak = zgloszenie do przeczytania.

CZYM TO NIE JEST. Nie jest bramka i nie bedzie: liczba moze legalnie zyc w prozie, bo
opisuje cudza wypowiedz, cene na targu albo stan sprzed tury. To jest lista do PRZEJRZENIA,
nie werdykt - dlatego wyjscie zawsze konczy sie kodem 0.

Uruchomienie:
    python tools/orphan_numbers.py --limit 30
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TRANSACTIONS = ROOT / "campaigns" / "lucan" / "journal" / "transactions"

# Liczba + jednostka mechaniczna. Tylko te trzy, bo tylko one opisuja STAN, a nie swiat.
JEDNOSTKI = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:jednostk\w*|na\s+dob\w+|sekund\w*|punkt\w*\s+integralno\w+)",
    re.IGNORECASE,
)


def numer(nazwa: str) -> int:
    m = re.search(r"(\d+)", nazwa)
    return int(m.group(1)) if m else -1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30, help="ile ostatnich tur przejrzec")
    args = parser.parse_args()

    pliki = sorted(TRANSACTIONS.glob("*.yaml"), key=lambda p: numer(p.name))[-args.limit:]
    znaleziska = 0

    for path in pliki:
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        outcome = doc.get("outcome") or {}
        tekst = " ".join(
            str(outcome.get(klucz) or "") for klucz in ("summary", "prose"))
        if not tekst.strip():
            continue

        operacje = yaml.safe_dump(outcome.get("operations") or [], allow_unicode=True)
        osierocone = []
        for surowa in {m.group(1) for m in JEDNOSTKI.finditer(tekst)}:
            znormalizowana = surowa.replace(",", ".")
            warianty = {surowa, znormalizowana, znormalizowana.rstrip("0").rstrip(".")}
            if not any(w and w in operacje for w in warianty):
                osierocone.append(surowa)

        if osierocone:
            znaleziska += 1
            print(f"{path.stem}: {sorted(osierocone)}")

    print()
    print(f"przejrzano {len(pliki)} tur, {znaleziska} z liczbami nieobecnymi w operacjach")
    print("To jest lista DO PRZECZYTANIA, nie werdykt: liczba moze legalnie zyc w prozie,")
    print("gdy opisuje cudza wypowiedz, cene albo stan sprzed tury. Sprawdzane jest jedno -")
    print("czy stawka ogloszona graczowi ma pokrycie w tym, co tura faktycznie zapisala.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
