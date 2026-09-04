"""Testy etapu 6: load_when_* przestaje byc martwym pasazerem, a licznik klamac.

Do 2026-09-04 szesc kluczy load_when_* w context/active.yaml nie bylo czytane przez ANI
JEDNA linie kodu - refresh_context przepisywalo je przez deepcopy. Warunkowe wczytywanie
istnialo wylacznie jako dobra wola narratora. Do tego licznik kontekstu widzial mniejsza
czesc tury: nie widzial AGENTS.md, kart NPC stojacych w scenie (68 KB) ani zbiorow
warunkowych, i raportowal 53 KB przy realnej turze planowania wazacej 211 KB.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime

CAMPAIGN = TOOLS.parent / "campaigns" / "lucan"


class RefPathTest(unittest.TestCase):
    def test_ref_od_korzenia_repo(self):
        self.assertTrue(gm_runtime.ref_path("system/narrator.md").is_file())

    def test_ref_wzgledem_kampanii_tez_sie_rozwiazuje(self):
        """active.yaml miesza dwie konwencje; plik obowiazkowy przy planowaniu byl niewidzialny.

        UWAGA: pierwotnie ten test sprawdzal takze, ze plik wazy ponad 70 KB - czyli
        sprawdzal ROZMIAR PROBLEMU, nie regule. Etap 8 rozbil magazyn na sekcje i indeks
        ma dzis 4,3 KB, wiec asercja rozmiaru stala sie falszem. Zostaje niezmiennik:
        ref w konwencji kampanii MUSI sie rozwiazywac.
        """
        path = gm_runtime.ref_path("planning/act-03-defence.yaml")
        self.assertTrue(path.is_file(), f"nie rozwiazano refu wzgledem kampanii: {path}")
        sekcja = gm_runtime.ref_path("planning/act-03-defence/institutional_defence.yaml")
        self.assertTrue(sekcja.is_file(), "sekcja magazynu nie rozwiazuje sie w tej konwencji")

    def test_nieistniejacy_ref_wskazuje_sensowna_sciezke(self):
        path = gm_runtime.ref_path("nie/ma/mnie.yaml")
        self.assertFalse(path.exists())
        self.assertIn("nie", path.as_posix())


class ConditionalSetsTest(unittest.TestCase):
    def test_zbiory_sa_rozwiazywane_i_wazone(self):
        active = yaml.safe_load((CAMPAIGN / "context" / "active.yaml").read_text(encoding="utf-8-sig"))
        sets = gm_runtime.conditional_sets(active)
        self.assertIn("testing", sets)
        self.assertIn("choosing_a_plan", sets)
        for tag, entries in sets.items():
            for entry in entries:
                self.assertNotIn("missing", entry, f"{tag}: nierozwiazany ref {entry['ref']}")
                self.assertGreater(entry["bytes"], 0)

    def test_klucze_bez_prefiksu_nie_wchodza(self):
        sets = gm_runtime.conditional_sets({"always_load": ["a"], "load_when_x": ["system/narrator.md"]})
        self.assertEqual(list(sets), ["x"])


class ContextPlanTest(unittest.TestCase):
    def test_plan_bez_tagow_liczy_baze_i_karty(self):
        plan = gm_runtime.context_plan(CAMPAIGN, [])
        self.assertEqual(plan["bytes"]["conditional"], 0)
        self.assertGreater(plan["bytes"]["participant_cards"], 0,
                           "karty uczestnikow nie sa liczone - to byla najwieksza dziura licznika")
        self.assertEqual(plan["bytes"]["total"],
                         plan["bytes"]["base"] + plan["bytes"]["participant_cards"])

    def test_agents_md_jest_w_bazie(self):
        plan = gm_runtime.context_plan(CAMPAIGN, [])
        self.assertIn("AGENTS.md", [row["ref"] for row in plan["base"]])

    def test_tag_planowania_doklada_swoj_zbior(self):
        """Niezmiennik: tag doklada NIEPUSTY zbior i podnosi sume.

        Pierwotnie test wymagal, zeby zbior planowania wazyl ponad 70 KB - to bylo
        sprawdzanie rozmiaru problemu. Etap 8 zbil go do 6,8 KB i to jest sukces,
        nie regresja. Prog wielkosci pilnuje teraz test_stage8_granulation.
        """
        bez = gm_runtime.context_plan(CAMPAIGN, [])
        plan = gm_runtime.context_plan(CAMPAIGN, ["choosing_a_plan"])
        self.assertGreater(plan["bytes"]["conditional"], 0)
        self.assertGreater(plan["bytes"]["total"], bez["bytes"]["total"])
        self.assertEqual(plan["unknown_tags"], [])

    def test_nieznany_tag_jest_zglaszany_a_nie_ignorowany(self):
        plan = gm_runtime.context_plan(CAMPAIGN, ["nie_ma_takiego"])
        self.assertEqual(plan["unknown_tags"], ["nie_ma_takiego"])
        self.assertEqual(plan["bytes"]["conditional"], 0)

    def test_powtorzony_tag_nie_liczy_pliku_dwa_razy(self):
        raz = gm_runtime.context_plan(CAMPAIGN, ["testing"])["bytes"]["conditional"]
        dwa = gm_runtime.context_plan(CAMPAIGN, ["testing", "testing"])["bytes"]["conditional"]
        self.assertEqual(raz, dwa)


class BreakdownTest(unittest.TestCase):
    def test_refresh_daje_rozbicie_i_prawdziwa_sume(self):
        result = gm_runtime.refresh_context(CAMPAIGN, write=False)
        breakdown = result["context_breakdown"]
        for key in ("rules_always", "state_active", "participant_cards", "conditional_heaviest"):
            self.assertIn(key, breakdown)
        self.assertGreater(result["context_total_bytes"], result["context_bytes"],
                           "suma prawdziwa nie moze byc mniejsza od bramkowej")
        self.assertEqual(result["context_total_bytes"],
                         breakdown["rules_always"] + breakdown["state_active"]
                         + breakdown["participant_cards"])

    def test_ostrzezenie_o_prawdziwej_sumie_jest_informacyjne(self):
        """Bramka zostaje na context_bytes - inaczej walidator swiecilby bez przerwy."""
        result = gm_runtime.refresh_context(CAMPAIGN, write=False)
        total_warnings = [w for w in result["context_warnings"] if w.startswith("total_")]
        self.assertTrue(total_warnings)
        self.assertTrue(all(w.startswith("total_informational") for w in total_warnings))


if __name__ == "__main__":
    unittest.main()
