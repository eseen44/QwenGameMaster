"""Zapadka: zaden plik regul nie moze osierociec.

Audyt 2026-09-04: szesc z czternastu plikow system/*.md nie bylo osiagalnych z zadnego
triggera ladowania - w tym 15 KB mechaniki klatw i 10 KB regul wzrostu slug - a
system/canon-policy.md i system/runtime.md nie mialy ANI JEDNEJ referencji w calym repo.
Regula, do ktorej nie prowadzi zadna droga, nie dziala.

Do tego state/growth-banks.yaml nie byl w `load` z briefu i wlasnie dlatego tura 178
wymyslila stawki od nowa (retcon_000114). Teraz jest osiagalny przez tag.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime

ACTIVE = ROOT / "campaigns" / "lucan" / "context" / "active.yaml"

# Pliki, ktore NIE sa regulami dla narratora - dokumentacja dla czlowieka pracujacego
# nad repo. Dopisanie tu czegokolwiek jest swiadomym wylaczeniem z zapadki.
NIE_REGULY = {
    "system/fixtures/vertical-slice/README.md",
    "system/mechanics/LOGIC-AUDIT-v1.md",
}


def osiagalne() -> set[str]:
    active = yaml.safe_load(ACTIVE.read_text(encoding="utf-8-sig"))
    refs = set(active.get("always_load") or [])
    for key, value in active.items():
        if key.startswith("load_when_") and isinstance(value, list):
            refs |= {ref for ref in value if isinstance(ref, str)}
    return refs


class RulesReachableTest(unittest.TestCase):
    def test_kazdy_plik_regul_jest_osiagalny(self):
        refs = osiagalne()
        tekst = "\n".join((ROOT / name).read_text(encoding="utf-8")
                          for name in ("AGENTS.md", "SKILL-gramy.md"))
        sieroty = []
        for path in sorted((ROOT / "system").rglob("*.md")):
            ref = path.relative_to(ROOT).as_posix()
            if ref in NIE_REGULY:
                continue
            if ref in refs or ref in tekst or path.name in tekst:
                continue
            sieroty.append(f"{ref} ({path.stat().st_size} B)")
        self.assertEqual(sieroty, [],
                         "pliki regul bez zadnej drogi ladowania: " + "; ".join(sieroty))

    def test_kazdy_ref_z_triggera_istnieje(self):
        brak = [ref for ref in sorted(osiagalne()) if not gm_runtime.ref_path(ref).is_file()]
        self.assertEqual(brak, [], f"trigger wskazuje na nieistniejacy plik: {brak}")

    def test_growth_banks_jest_osiagalny(self):
        """retcon_000114: tura 178 wymyslila stawki, bo tego pliku nie bylo w load."""
        refs = osiagalne()
        self.assertTrue(
            any("growth-banks" in ref for ref in refs),
            "state/growth-banks.yaml znowu nieosiagalny - to jest miejsce prawdy dla "
            "nadwyzki i stawek dobowych, a jego pominiecie juz raz kosztowalo cofniete tury")

    def test_mechanika_klatw_i_magii_jest_osiagalna(self):
        refs = osiagalne()
        for nazwa in ("system/curses.md", "system/magic.md", "system/metamagic.md",
                      "system/companion-growth.md", "system/canon-policy.md"):
            self.assertIn(nazwa, refs, f"{nazwa} nieosiagalny z zadnego triggera")

    def test_appendiks_narratora_nie_wrocil_do_always_load(self):
        active = yaml.safe_load(ACTIVE.read_text(encoding="utf-8-sig"))
        self.assertNotIn("system/narrator-appendix.md", active.get("always_load") or [])

    def test_always_load_zostaje_male(self):
        """always_load wchodzi do KAZDEJ tury - prog jest celem, nie ozdoba."""
        active = yaml.safe_load(ACTIVE.read_text(encoding="utf-8-sig"))
        total = sum(gm_runtime.ref_path(ref).stat().st_size
                    for ref in (active.get("always_load") or [])
                    if gm_runtime.ref_path(ref).is_file())
        self.assertLess(total, 12_000, f"always_load spuchl do {total} B")


if __name__ == "__main__":
    unittest.main()
