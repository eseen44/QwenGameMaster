"""Testy odzysku prozy czytanej jako klucze o wartosci null.

Awaria: w mapie plaskiej niecytowana wartosc z przecinkiem rozpada sie na kolejne pary,
wiec tekst jest na dysku, ale nie widzi go zaden maszynowy czytelnik. Naprawa musi byc
PRZECYTOWANIEM - nie wolno jej zgubic ani slowa, ani legalnego klucza stojacego PO prozie.
Pierwsza wersja skryptu scalala wszystko do konca mapy i wchlaniala assessed_use razem
z trescia; te testy pilnuja, zeby to nie wrocilo.
"""

from __future__ import annotations

import collections
import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import fix_prose_keys as F


class FixProseKeysTest(unittest.TestCase):
    def naprawa(self, text: str):
        fixed, merged = F.repair_text(text)
        before, after = yaml.safe_load(text), yaml.safe_load(fixed)
        return fixed, merged, before, after

    def test_proza_bez_dwukropka_wraca_do_wartosci(self):
        text = "a:\n  - {id: x, claim: Wie, ze wlasciciel znal skale zagrozenia}\n"
        fixed, merged, before, after = self.naprawa(text)
        self.assertEqual(merged, 1)
        self.assertEqual(after["a"][0]["claim"], "Wie, ze wlasciciel znal skale zagrozenia")
        self.assertEqual(F.prose_key_count(after), 0)
        self.assertGreater(F.prose_key_count(before), 0)

    def test_legalny_klucz_po_prozie_zostaje_kluczem(self):
        text = ("a:\n  - {id: x, role: trwale ulepszenie, NIE material zuzywany (retcon_000015),\n"
                "     assessed_use: 'event_087 - jedyna pozycja'}\n")
        fixed, merged, before, after = self.naprawa(text)
        entry = after["a"][0]
        self.assertEqual(entry["role"], "trwale ulepszenie, NIE material zuzywany (retcon_000015)")
        self.assertEqual(entry["assessed_use"], "event_087 - jedyna pozycja")
        self.assertEqual(F.prose_key_count(after), 0)

    def test_mapa_plaska_lamana_na_kilka_linii(self):
        text = ("a:\n  - {id: x, quantity: 1,\n"
                "     basis: kanaly, zer obfity, bez rozkazu,\n"
                "     bank: 2.5}\n")
        fixed, merged, before, after = self.naprawa(text)
        self.assertEqual(after["a"][0]["basis"], "kanaly, zer obfity, bez rozkazu")
        self.assertEqual(after["a"][0]["bank"], 2.5)

    def test_zadne_slowo_nie_ginie(self):
        text = ("a:\n  - {id: x, claim: Pod wplywem Confusion chwilowo uznal, ze zaloga jest Orenem., "
                "disclosure: NIEZNANE gildii - patrz retcon_000009}\n")
        fixed, merged, before, after = self.naprawa(text)
        lost = collections.Counter(F.all_words(before)) - collections.Counter(F.all_words(after))
        self.assertFalse(lost, f"zgubione slowa: {dict(lost)}")

    def test_wartosc_juz_cytowana_nie_jest_ruszana(self):
        text = "a:\n  - {id: x, claim: 'Wie, ze wszystko jest w cudzyslowie'}\n"
        fixed, merged, _, after = self.naprawa(text)
        self.assertEqual(merged, 0)
        self.assertEqual(fixed, text)

    def test_apostrof_w_niecytowanej_prozie_powoduje_odmowe_nie_zepsucie(self):
        """Znane ograniczenie, celowe: skaner nie odgadnie, gdzie konczy sie skalar.

        Apostrof w niecytowanej wartosci ("Mowi don't, a potem") wyglada dla skanera jak
        otwarcie cudzyslowu, wiec mapa nie zostaje rozpoznana. Skrypt wtedy NIE RUSZA
        pliku i raportuje go jako "wzorzec nierozpoznany - do recznej naprawy".
        Lepiej odmowic niz zepsuc - dokladnie ten blad popelnil round-trip YAML
        2026-09-04 na karcie Varkhena. W kampanii nie ma dzis takiego przypadku (91 -> 0).
        """
        text = "a:\n  - {id: x, note: Mowi don't, a potem, milczy}\n"
        fixed, merged, _, _ = self.naprawa(text)
        self.assertEqual(merged, 0, "skrypt probowal naprawiac przypadek, ktorego nie umie")
        self.assertEqual(fixed, text, "plik zostal zmieniony mimo odmowy naprawy")

    def test_zdrowy_plik_nie_jest_zmieniany(self):
        text = "a:\n  - {id: x, claim: bez przecinka}\n  - {id: y, claim: tez bez}\n"
        fixed, merged, _, _ = self.naprawa(text)
        self.assertEqual(merged, 0)
        self.assertEqual(fixed, text)

    def test_kampania_nie_ma_ani_jednego_klucza_prozy(self):
        """Zapadka: gdy ktos wpisze niecytowana proze z przecinkiem, ten test padnie."""
        campaign = TOOLS.parent / "campaigns" / "lucan"
        winne: list[str] = []
        for path in sorted(campaign.rglob("*.yaml")):
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
            except yaml.YAMLError:
                continue
            count = F.prose_key_count(document)
            if count:
                winne.append(f"{path.relative_to(TOOLS.parent).as_posix()}: {count}")
        self.assertEqual(winne, [], "proza czytana jako klucze null wrocila: " + "; ".join(winne))


if __name__ == "__main__":
    unittest.main()
