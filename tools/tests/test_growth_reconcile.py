"""Testy uzgodnienia silnika z rejestrem wzrostu (etap 10, czesc druga).

Dwa realne bledy z tej rodziny zostaly naprawione osobno (retcon_000145 i 000146); tu
pilnujemy, zeby nie wrocily, i zeby raport nie zaczal klamac w druga strone.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import reconcile_growth as recon

INSTANCES = ROOT / "campaigns" / "lucan" / "state" / "instances"


class ReconcileTest(unittest.TestCase):
    def instancja(self, nazwa: str) -> dict:
        return yaml.safe_load((INSTANCES / nazwa).read_text(encoding="utf-8-sig"))

    def test_osa_nie_ubywa_juz_na_minus(self):
        """retcon_000146: bramka zeru stala na fladze, ktorej osa nie nosila - od t_177 do 0/3."""
        rate, notes = recon.engine_rate(self.instancja("spy-wasp-01.yaml"))
        self.assertGreaterEqual(rate, 0.0, f"osa nadal traci rezerwe: {rate}/dobe, uwagi: {notes}")

    def test_tlumienie_ubytku_jest_widziane_przez_raport(self):
        rate, notes = recon.engine_rate(self.instancja("webber-anchored.yaml"))
        self.assertTrue(any("stlumiony" in note for note in notes))
        self.assertGreater(rate, 0.0)

    def test_raport_liczy_lacza_a_nie_tylko_strumienie(self):
        """Bez laczy polowa 'rozjazdow' byla artefaktem miary, nie stanem repo."""
        flows = recon.link_flow()
        self.assertTrue(flows, "raport nie widzi zadnego lacza")
        self.assertIn("companion_varkhen", flows)
        self.assertGreater(flows["companion_varkhen"], 0.0)
        self.assertLess(flows["webber_home"], 0.0, "zrodlo lacza musi byc obciazone")

    def test_zablokowana_bramka_jest_nazwana_z_brakujaca_flaga(self):
        rate, notes = recon.engine_rate(self.instancja("spy-hawk-moth-01.yaml"))
        blokady = [note for note in notes if "zablokowany brakiem flag" in note]
        self.assertTrue(blokady, "raport nie mowi, ktora flaga blokuje strumien")
        self.assertIn("autonomous_hunting", blokady[0])


class KontroleTest(unittest.TestCase):
    """Kazda z pieciu kontrol musi dac sie ZOBACZYC, jak odrzuca - i jak przepuszcza."""

    def zbior(self, rate=1.0, cap=1.5, capacity=3, status="active", **nadpisz):
        bank = {
            "surplus_economy": {"daily_network_surplus_units": rate},
            "banks": [{"id": "spy_test_01", "rate_per_day": rate, "growth_cap_per_day": cap,
                       **nadpisz}],
        }
        instances = {"spy_test_01": {
            "id": "spy_test_01", "status": status,
            "status_flags": ["autonomous_hunting"],
            "resources": {"necrotic_reservoir": {
                "current": capacity, "capacity": capacity,
                "decay": {"interval_seconds": 86400, "units": 1},
                "hunting_recovery": {"interval_seconds": 86400, "units": 3,
                                     "requires": ["autonomous_hunting"]},
            }},
        }}
        return bank, instances

    def test_poprawny_zbior_przechodzi(self):
        bank, instances = self.zbior()
        problems, liczby = recon.check(bank, instances, {})
        self.assertEqual(problems, {}, f"kontrola blokuje poprawny zbior: {problems}")
        self.assertEqual(liczby["nadwyzka_policzona"], 1.0)

    def test_deklarowana_nadwyzka_musi_sie_zgadzac_z_suma(self):
        """Tak wyszlo, ze nota mowila 14,5, suma pliku 20,0, a siec generuje 16,5."""
        bank, instances = self.zbior()
        bank["surplus_economy"]["daily_network_surplus_units"] = 14.5
        problems, _ = recon.check(bank, instances, {})
        self.assertIn("deklarowana_nadwyzka", problems)
        self.assertIn("14.5", problems["deklarowana_nadwyzka"][0])

    def test_stawka_finansowana_z_rezerwy_lucana_nie_wchodzi_do_sumy(self):
        """Zuk 01: 3,5 na dobe z rezerwy LUCANA (retcon_000141) nie jest nadwyzka SIECI,
        bo to ta sama energia liczona dwa razy."""
        bank, instances = self.zbior(rate=3.5, funded_by="lucan_reserve")
        bank["surplus_economy"]["daily_network_surplus_units"] = 0.0
        problems, liczby = recon.check(bank, instances, {})
        self.assertEqual(problems, {})
        self.assertEqual(liczby["nadwyzka_policzona"], 0.0)

    def test_aktywny_wezel_bez_wpisu_w_rejestrze(self):
        bank, instances = self.zbior()
        bank["banks"] = []
        bank["surplus_economy"]["daily_network_surplus_units"] = 0.0
        problems, _ = recon.check(bank, instances, {})
        self.assertIn("wezel_aktywny_bez_wpisu", problems)

    def test_martwy_wezel_zostawiony_w_rejestrze(self):
        """Piec wezlow poza rejestrem to zniszczone okazy i tak ma byc - ale odwrotnie
        nie: zniszczony wezel nie moze dalej generowac nadwyzki."""
        bank, instances = self.zbior(status="destroyed")
        bank["surplus_economy"]["daily_network_surplus_units"] = 0.0
        problems, _ = recon.check(bank, instances, {})
        self.assertIn("wezel_martwy_z_wpisem", problems)
        self.assertIn("destroyed", problems["wezel_martwy_z_wpisem"][0])

    def test_sufit_rozwoju_to_polowa_pojemnosci(self):
        """growth_intake_cap w tym samym pliku mowi: najwyzej POLOWA pojemnosci zbiornika."""
        bank, instances = self.zbior(cap=3.0, capacity=3)
        problems, _ = recon.check(bank, instances, {})
        self.assertIn("sufit_rozwoju", problems)

    def test_ubywajacy_zbiornik_jest_naruszeniem(self):
        """Klasa retcon_000145 i retcon_000146: wezel tracil rezerwe bez podstawy w kanonie."""
        bank, instances = self.zbior()
        instances["spy_test_01"]["status_flags"] = []  # bramka zeru przestaje przechodzic
        problems, _ = recon.check(bank, instances, {})
        self.assertIn("zbiornik_ubywa", problems)
        self.assertIn("autonomous_hunting", problems["zbiornik_ubywa"][0])

    def test_prawdziwe_repo_przechodzi_wszystkie_piec(self):
        problems, liczby = recon.check()
        self.assertEqual(problems, {}, f"rejestr wzrostu ma naruszenia: {problems}")
        self.assertEqual(liczby["nadwyzka_deklarowana"], liczby["nadwyzka_policzona"])
