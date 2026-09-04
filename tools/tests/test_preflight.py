"""Testy zapadki etapu 12: preflight i instalator hookow.

Hook, ktory nie blokuje, jest dekoracja - a instalator, ktory nadpisuje cudze hooki, jest
pulapka. Oba przypadki sa tu sprawdzone.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import install_hooks
import preflight

ZEPSUTY = "schema_version: 1\nwpisy:\n  - {id: x, claim: Wie, ze to sie rozpadnie}\n"
ZDROWY = "schema_version: 1\nwpisy:\n  - {id: x, claim: 'Wie, ze to sie nie rozpadnie'}\n"


class PreflightScopeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def plik(self, name: str, body: str) -> Path:
        path = self.dir / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_pusty_zakres_przechodzi(self):
        code, message = preflight.prose_keys_check([])
        self.assertEqual(code, 0)

    def test_zdrowy_plik_w_zakresie_przechodzi(self):
        code, _ = preflight.prose_keys_check([self.plik("ok.yaml", ZDROWY)])
        self.assertEqual(code, 0)

    def test_zepsuty_plik_w_zakresie_BLOKUJE(self):
        code, message = preflight.prose_keys_check([self.plik("zle.yaml", ZEPSUTY)])
        self.assertEqual(code, 1, "preflight przepuscil proze czytana jako klucze null")
        self.assertIn("fix_prose_keys", message)

    def test_pliki_nie_yaml_sa_pomijane(self):
        code, _ = preflight.prose_keys_check([self.plik("readme.md", ZEPSUTY)])
        self.assertEqual(code, 0)

    def test_wykrywanie_dziennika(self):
        root = Path("/repo")
        self.assertFalse(preflight.journal_touched([root / "tools/x.py"]))
        self.assertTrue(preflight.journal_touched([root / "campaigns/lucan/journal/events.jsonl"]))
        self.assertTrue(preflight.journal_touched([root / "campaigns/lucan/journal/transactions/a.yaml"]))


class InstallHooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.hooks = Path(self.tmp.name) / "hooks"
        self.hooks.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def uruchom(self, argv: list[str]) -> None:
        with mock.patch.object(install_hooks, "hooks_dir", return_value=self.hooks), \
             mock.patch.object(sys, "argv", ["install_hooks.py", *argv]), \
             mock.patch("builtins.print", lambda *a, **k: None):
            install_hooks.main()

    def test_instaluje_hooka(self):
        self.uruchom([])
        target = self.hooks / "pre-commit"
        self.assertTrue(target.exists())
        self.assertIn(install_hooks.MARKER, target.read_text(encoding="utf-8"))

    def test_nie_nadpisuje_cudzego_hooka(self):
        target = self.hooks / "pre-commit"
        target.write_text("#!/bin/sh\necho moj wlasny hook\n", encoding="utf-8")
        self.uruchom([])
        self.assertIn("moj wlasny hook", target.read_text(encoding="utf-8"),
                      "instalator nadpisal cudzy hook")

    def test_usuwa_tylko_swojego(self):
        target = self.hooks / "pre-commit"
        target.write_text("#!/bin/sh\necho cudzy\n", encoding="utf-8")
        self.uruchom(["--remove"])
        self.assertTrue(target.exists(), "instalator usunal cudzy hook")
        self.uruchom([])           # nadal odmowi, bo cudzy
        target.unlink()
        self.uruchom([])           # teraz zainstaluje
        self.uruchom(["--remove"])
        self.assertFalse(target.exists())

    def test_instalacja_jest_idempotentna(self):
        self.uruchom([])
        first = (self.hooks / "pre-commit").read_text(encoding="utf-8")
        self.uruchom([])
        self.assertEqual(first, (self.hooks / "pre-commit").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
