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
