"""Testy kontroli rejestrow. Kazda z pieciu kontrol musi dac sie ZOBACZYC, jak odrzuca.

Kontrola powstala po przegladzie 2026-09-05, ktory pokazal, ze rejestry klamaly o statusie
23 z 34 wpisow - entities/npcs/index.yaml twierdzil "needs_review" o npc_seraphine_vale,
ktorej karta od dawna mowila "active". Rejestr, ktory klamie, jest gorszy niz jego brak.
"""

from __future__ import annotations

import sys
import textwrap
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import registry_check as rc


class KontroleTest(unittest.TestCase):
    """Kontrole odpalane na SZTUCZNYM drzewie plikow w tmp, zeby test nie zalezal od kampanii."""

    def zbuduj(self, tmp: Path, rejestr: str, karty: dict[str, str]) -> None:
        (tmp / "rzeczy").mkdir(parents=True, exist_ok=True)
        (tmp / "rzeczy" / "index.yaml").write_text(textwrap.dedent(rejestr).lstrip(),
                                                   encoding="utf-8")
        for nazwa, tresc in karty.items():
            (tmp / "rzeczy" / nazwa).write_text(textwrap.dedent(tresc).lstrip(), encoding="utf-8")

    def sprawdz(self, tmp: Path):
        stare_root, stare_camp = rc.ROOT, rc.CAMPAIGN
        rc.ROOT = rc.CAMPAIGN = tmp
        try:
            return rc.check()[0]
        finally:
            rc.ROOT, rc.CAMPAIGN = stare_root, stare_camp

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_poprawny_rejestr_przechodzi(self):
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/a.yaml, status: active}
                    """,
                    {"a.yaml": "id: rzecz_a\nstatus: active\n"})
        self.assertEqual(self.sprawdz(self.tmp), {})

    def test_ref_wskazuje_w_nicosc(self):
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/nie-ma-mnie.yaml, status: active}
                    """, {})
        self.assertIn("ref_nie_istnieje", self.sprawdz(self.tmp))

    def test_id_sie_nie_zgadza(self):
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/a.yaml, status: active}
                    """,
                    {"a.yaml": "id: zupelnie_co_innego\nstatus: active\n"})
        self.assertIn("id_sie_nie_zgadza", self.sprawdz(self.tmp))

    def test_status_sie_rozjechal(self):
        """Ta wlasnie kontrola wylapala 36 rozjazdow w prawdziwej kampanii."""
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/a.yaml, status: needs_review}
                    """,
                    {"a.yaml": "id: rzecz_a\nstatus: active\n"})
        problemy = self.sprawdz(self.tmp)
        self.assertIn("status_sie_rozjechal", problemy)
        self.assertIn("needs_review", problemy["status_sie_rozjechal"][0])

    def test_rejestr_deklaruje_status_pliku_ktory_go_nie_ma(self):
        """Tak bylo z rel_neris_to_lucan: rejestr mowil 'active', a plik nie mial pola status."""
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/a.yaml, status: active}
                    """,
                    {"a.yaml": "id: rzecz_a\n"})
        problemy = self.sprawdz(self.tmp)
        self.assertIn("status_sie_rozjechal", problemy)
        self.assertIn("NIE MA pola status", problemy["status_sie_rozjechal"][0])

    def test_plik_bez_wpisu_w_rejestrze(self):
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - {id: rzecz_a, ref: rzeczy/a.yaml, status: active}
                    """,
                    {"a.yaml": "id: rzecz_a\nstatus: active\n",
                     "sierota.yaml": "id: rzecz_b\nstatus: active\n"})
        problemy = self.sprawdz(self.tmp)
        self.assertIn("plik_bez_wpisu", problemy)
        self.assertIn("sierota.yaml", problemy["plik_bez_wpisu"][0])

    def test_duplikat_klucza_w_wpisie(self):
        """YAML polyka duplikat i bierze OSTATNI - tak loc_city_sewer mial dwa statusy naraz."""
        self.zbuduj(self.tmp,
                    """
                    schema_version: 1
                    rzeczy:
                      - id: rzecz_a
                        ref: rzeczy/a.yaml
                        status: known_by_proxy
                        status: active
                    """,
                    {"a.yaml": "id: rzecz_a\nstatus: active\n"})
        problemy = self.sprawdz(self.tmp)
        self.assertIn("duplikat_klucza_w_wpisie", problemy)
        self.assertIn("YAML bierze ostatni", problemy["duplikat_klucza_w_wpisie"][0])


class KampaniaTest(unittest.TestCase):
    def test_prawdziwe_rejestry_sa_czyste(self):
        problemy, liczby = rc.check()
        self.assertEqual(problemy, {}, f"rejestry kampanii maja naruszenia: {problemy}")
        self.assertGreater(liczby["wpisow"], 90, "kontrola nagle widzi mniej wpisow - podejrzane")

    def test_obie_konwencje_sciezek_sie_rozwiazuja(self):
        """state/instances/index.yaml pisze wzgledem korzenia KAMPANII, reszta od korzenia repo.
        Sprawdzanie jednej konwencji dawalo 30 falszywych martwych wskazan."""
        self.assertIsNotNone(rc.resolve("campaigns/lucan/relationships/seraphine--lucan.yaml"))
        self.assertIsNotNone(rc.resolve("state/instances/pc-lucan.yaml"))
        self.assertIsNone(rc.resolve("state/instances/nie-ma-takiego.yaml"))


if __name__ == "__main__":
    unittest.main()
