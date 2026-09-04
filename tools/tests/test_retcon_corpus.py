"""Testy etapu 9: linter korpusu retconow i generowany indeks regul.

Dwie rzeczy sa tu warte pilnowania. Pierwsza: ZAPADKA - dlug historyczny nie moze blokowac
(bo walidator swiecacy na czerwono bez przerwy jest ignorowany), ale nowy wpis MUSI przejsc.
Druga: skrot w indeksie ma byc zdaniem z IMPERATYWEM, nie pierwszym zdaniem tresci - na
pierwszym zdaniu retcon_000033 dawal zrzut stanu, a regula stala trzy zdania dalej.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import build_rules_index as index
import retcon_lint as lint


class LintTest(unittest.TestCase):
    def sprawdz(self, retcons: list[dict], events: set[str] | None = None):
        return lint.check(retcons, events or set())

    def wpis(self, numer: int, **nadpisz) -> dict:
        base = {
            "id": f"retcon_{numer:06}",
            "timestamp": f"2026-09-04T{numer % 24:02}:00:00+02:00",
            "reason": "powod",
            "replacement": "tresc korekty",
            "approved_by": "player_declaration_2026_09_04",
            "supersedes": [],
        }
        base.update(nadpisz)
        return base

    def test_poprawny_wpis_bez_naruszen(self):
        self.assertEqual(self.sprawdz([self.wpis(200)]), {})

    def test_brak_pola_wymaganego(self):
        problems = self.sprawdz([self.wpis(200, approved_by=None)])
        self.assertIn("pola_wymagane", problems)

    def test_brak_tresci_korekty(self):
        problems = self.sprawdz([self.wpis(200, replacement=None)])
        self.assertIn("tresc_korekty", problems)

    def test_supersedes_musi_byc_lista(self):
        problems = self.sprawdz([self.wpis(200, supersedes="retcon_000001")])
        self.assertIn("supersedes_lista", problems)

    def test_supersedes_na_nieistniejacy_retcon(self):
        problems = self.sprawdz([self.wpis(200, supersedes=["retcon_999999"])])
        self.assertIn("supersedes_wskazuje_w_nicosc", problems)

    def test_supersedes_na_katalog_jest_naruszeniem(self):
        """Katalog przechodzil jako poprawny ref i przemknal tak moj wlasny retcon_000144."""
        problems = self.sprawdz([self.wpis(200, supersedes=["campaigns/lucan/#cos"])])
        self.assertIn("supersedes_wskazuje_w_nicosc", problems)
        self.assertIn("katalog", problems["supersedes_wskazuje_w_nicosc"][0][1])

    def test_kotwica_na_retconie_nie_rozwiazuje_sie_nigdy(self):
        problems = self.sprawdz([self.wpis(200), self.wpis(201, supersedes=["retcon_000200#klucz"])])
        self.assertIn("kotwica_na_retconie", problems)

    def test_timestamp_w_czasie_kampanii(self):
        problems = self.sprawdz([self.wpis(200, timestamp="2026-08-19T18:01:40+02:00")])
        self.assertIn("timestamp_w_czasie_kampanii", problems)

    def test_timestamp_powtorzony(self):
        stamp = "2026-09-04T12:00:00+02:00"
        problems = self.sprawdz([self.wpis(200, timestamp=stamp), self.wpis(201, timestamp=stamp)])
        self.assertIn("timestamp_powtorzony", problems)

    def test_zapadka_dlug_nie_blokuje_a_nowy_wpis_blokuje(self):
        self.assertLess(lint.number("retcon_000100"), lint.BASELINE)
        self.assertGreater(lint.number("retcon_000200"), lint.BASELINE)
        self.assertIn("timestamp_w_czasie_kampanii", lint.BLOCKING)

    def test_prawdziwy_korpus_ma_dlug_ale_nowe_wpisy_czyste(self):
        retcons = lint.load(lint.RETCONS)
        events = {e.get("id") for e in lint.load(lint.EVENTS) if e.get("id")}
        problems = lint.check(retcons, events)
        nowe = [(n, rid, d) for n, rows in problems.items() for rid, d in rows
                if n in lint.BLOCKING and lint.number(rid) > lint.BASELINE]
        self.assertEqual(nowe, [], f"nowe wpisy naruszaja kontrole blokujace: {nowe}")
        self.assertGreater(sum(len(r) for r in problems.values()), 0,
                           "linter nie widzi zadnego dlugu - podejrzane, korpus go ma")


class IndexTest(unittest.TestCase):
    def test_skrot_bierze_zdanie_z_imperatywem_nie_pierwsze(self):
        text = ("STAN COFNIETY DO WEJSCIA: czas 2026-08-18T14:15, elapsed 292500, energia 8.0. "
                "KALIBRACJA: narratorowi nie wolno produkowac oporu bez pokrycia w pliku. "
                "Trzecie zdanie bez znaczenia.")
        skrot = index.gist(text)
        self.assertIn("nie wolno", skrot)
        self.assertNotIn("elapsed", skrot)

    def test_korekta_faktu_bez_imperatywu_nie_wchodzi(self):
        self.assertFalse(index.is_normative(
            "Mlodszy brat Klary mial czternascie lat, obecnie ma szesnascie."))

    def test_klauzula_normatywna_wchodzi(self):
        self.assertTrue(index.is_normative("Narratorowi NIE WOLNO tego przedstawiac jako zdrady."))

    def test_slowo_regula_samo_nie_wystarcza(self):
        """"regula" wystepuje w korpusie tez opisowo i wciagalo czyste korekty faktu."""
        self.assertFalse(index.is_normative("Regula z t_227 zostala cofnieta w tej turze."))

    def test_indeks_na_dysku_jest_aktualny(self):
        self.assertTrue(index.OUTPUT.exists(), "brak system/retcon-rules-index.md")
        self.assertEqual(index.OUTPUT.read_text(encoding="utf-8"), index.build(),
                         "indeks nieaktualny - uruchom python tools/build_rules_index.py")

    def test_indeks_ma_naglowek_o_generowaniu(self):
        body = index.OUTPUT.read_text(encoding="utf-8")
        self.assertIn("PLIK GENEROWANY", body)
        self.assertIn("retcons.jsonl", body)


if __name__ == "__main__":
    unittest.main()
