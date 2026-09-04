"""Testy etapu 7: podzial system/narrator.md na rdzen normatywny i appendiks.

narrator.md siedzi w always_load, czyli wchodzi do KAZDEJ tury, a 79% jego objetosci
stanowily opisy mechanizmow awarii, cytaty reklamacji gracza i pomiary. Kazda kalibracja
trwale obciazala kazda kolejna ture: 3 083 B -> 18 796 B w dziewietnascie dni. Petla byla
samowzmacniajaca - poprawka po awarii podnosila szanse nastepnej.

Te testy pilnuja, zeby podzial sie nie zdegradowal: appendiks nie moze wrocic do
always_load, rdzen nie moze znowu spuchnac, a zadna regula nie moze wypasc z rdzenia
przy przenoszeniu opisu do appendiksu.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

CORE = ROOT / "system" / "narrator.md"
APPENDIX = ROOT / "system" / "narrator-appendix.md"
ACTIVE = ROOT / "campaigns" / "lucan" / "context" / "active.yaml"

# Rdzen wchodzi do kazdej tury. Prog jest celem, nie ozdoba: przed podzialem plik mial
# 18 796 B i sam zjadal 46% budzetu kontekstu.
CORE_LIMIT_BYTES = 9_000


class NarratorSplitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.core = CORE.read_text(encoding="utf-8")
        self.appendix = APPENDIX.read_text(encoding="utf-8")
        self.active = yaml.safe_load(ACTIVE.read_text(encoding="utf-8-sig"))

    def test_appendiks_istnieje_i_nie_jest_pusty(self):
        self.assertGreater(len(self.appendix), 10_000)

    def test_appendiks_NIE_jest_w_always_load(self):
        always = self.active.get("always_load") or []
        self.assertNotIn("system/narrator-appendix.md", always,
                         "appendiks wrocil do always_load - podzial przestal cokolwiek dawac")

    def test_appendiks_jest_osiagalny_warunkowo(self):
        conditional = [ref for key, refs in self.active.items()
                       if key.startswith("load_when_") and isinstance(refs, list)
                       for ref in refs]
        self.assertIn("system/narrator-appendix.md", conditional,
                      "appendiks nie jest osiagalny z zadnego triggera - czyli jest martwy")

    def test_rdzen_zostaje_maly(self):
        size = CORE.stat().st_size
        self.assertLess(size, CORE_LIMIT_BYTES,
                        f"rdzen spuchl do {size} B - historia incydentow idzie do appendiksu, "
                        f"nie do pliku wczytywanego w kazdej turze")

    def test_rdzen_odsyla_do_appendiksu(self):
        self.assertIn("narrator-appendix.md", self.core,
                      "rdzen nie mowi, gdzie leza uzasadnienia - reguly wygladaja na bezpodstawne")

    def test_kazda_regula_z_appendiksu_ma_slad_w_rdzeniu(self):
        """Retcon opisany w appendiksie musi byc wymieniony w rdzeniu.

        Inaczej regula wypada z pliku wczytywanego co ture i zyje tylko w tekscie,
        ktory czyta sie wyjatkowo - czyli wraca dokladnie ten problem, ktory naprawiamy.
        """
        w_appendiksie = set(re.findall(r"retcon_\d{6}", self.appendix))
        w_rdzeniu = set(re.findall(r"retcon_\d{6}", self.core))
        # Appendiks cytuje tez retcony poboczne (tlo awarii); wymagamy sladu dla tych,
        # ktore sa TYTULAMI sekcji, bo to one niosa norme.
        tytulowe = set(re.findall(r"^## .*?(retcon_\d{6})", self.appendix, re.M))
        self.assertTrue(tytulowe, "appendiks nie ma sekcji tytulowanych retconem")
        brak = sorted(tytulowe - w_rdzeniu)
        self.assertEqual(brak, [], f"reguly bez sladu w rdzeniu: {brak}")
        self.assertLessEqual(len(w_rdzeniu), len(w_appendiksie) + 4)

    def test_rdzen_trzyma_pierwotne_sekcje_normatywne(self):
        for naglowek in ("Obowiązkowy przebieg odpowiedzi w świecie", "Popychanie gry do przodu",
                         "Forma", "Neutralność przyczynowa", "Decyzje gracza",
                         "Rozwój zamiast rehabilitacji"):
            self.assertIn(naglowek, self.core, f"z rdzenia wypadla sekcja: {naglowek}")

    def test_appendiks_mowi_ze_tekst_jest_doslowny(self):
        self.assertIn("dosłown", self.appendix.casefold())
        self.assertIn("context plan", self.appendix)


if __name__ == "__main__":
    unittest.main()
