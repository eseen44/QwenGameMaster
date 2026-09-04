"""Testy zapory dziennika.

Sens tych testow jest waski i konkretny: zapora ma ZAPALAC SIE NA CZERWONO.
Pierwsza wersja journal_guard.py przechodzila na zielono przy usunietym wpisie i przy
podmienionej tresci wpisu, bo porownywala wylacznie pary (commit^, commit). Dokladnie ten
tryb awarii audyt znalazl w validate_project.py: walidator satysfakcjonowalny przez
konstrukcje. Te testy pilnuja, zeby nie wrocil.

Historia gita jest podstawiana przez mock funkcji journal_guard.git, wiec testy nie zaleza
od stanu repozytorium ani od zawartosci prawdziwego dziennika.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import journal_guard


def entry(event_id: str, summary: str) -> str:
    return json.dumps({"id": event_id, "summary": summary}, ensure_ascii=False)


HISTORIA = {
    "aaaaaaa": [entry("event_turn_001", "pierwsza"), entry("event_turn_002", "druga")],
    "bbbbbbb": [entry("event_turn_001", "pierwsza"), entry("event_turn_002", "druga"),
                entry("event_turn_003", "trzecia")],
}
HEAD = "bbbbbbb"


def fake_git(history: dict[str, list[str]]):
    """Podstawia git log/show/ls-tree dla plikow dziennika."""
    order = list(history)

    def run(*args: str) -> str:
        if args[0] == "log" and "--name-status" in args:
            return ""                                  # zero zmian plikow transakcji
        if args[0] == "log":
            return "\n".join(reversed(order))          # najnowszy pierwszy
        if args[0] == "ls-tree":
            return ""                                  # zero transakcji w HEAD
        if args[0] == "show":
            target = args[1]
            rev = target.split(":")[0]
            if rev == "HEAD":
                rev = HEAD
            if rev.endswith("^"):
                parent = rev[:-1]
                index = order.index(parent) if parent in order else 0
                if index == 0:
                    return ""
                rev = order[index - 1]
            return "\n".join(history.get(rev, [])) + "\n"
        return ""

    return run


class JournalGuardTest(unittest.TestCase):
    def uruchom(self, working_lines: list[str], archiwum: dict | None = None,
                history: dict | None = None) -> list[str]:
        problems: list[str] = []
        with mock.patch.object(journal_guard, "git", side_effect=fake_git(history or HISTORIA)), \
             mock.patch.object(journal_guard, "working_events",
                               return_value=journal_guard.parse_events("\n".join(working_lines))), \
             mock.patch.object(journal_guard, "load_manifest",
                               return_value=archiwum or {"events": [], "transactions": []}), \
             mock.patch.object(journal_guard, "SUPERSEDED", Path("/nieistniejace")), \
             mock.patch("builtins.print", lambda *a, **k: None):
            problems, _notes, _entries = journal_guard.collect_problems()
        return problems

    def test_stan_czysty_przechodzi(self):
        self.assertEqual(self.uruchom(HISTORIA[HEAD]), [])

    def test_usuniety_wpis_jest_wykryty(self):
        problems = self.uruchom(HISTORIA[HEAD][:-1])
        self.assertTrue(any("UTRACONY WPIS" in p and "event_turn_003" in p for p in problems),
                        f"zapora przepuscila usuniety wpis: {problems}")

    def test_usuniety_wpis_ze_srodka_jest_wykryty(self):
        problems = self.uruchom([HISTORIA[HEAD][0], HISTORIA[HEAD][2]])
        self.assertTrue(any("event_turn_002" in p for p in problems),
                        f"zapora przepuscila usuniety wpis ze srodka: {problems}")

    def test_podmieniona_tresc_jest_wykryta(self):
        working = [entry("event_turn_001", "pierwsza"),
                   entry("event_turn_002", "PODMIENIONE"),
                   entry("event_turn_003", "trzecia")]
        problems = self.uruchom(working)
        self.assertTrue(any("UCHYLONA WERSJA BEZ ARCHIWUM" in p and "event_turn_002" in p
                            for p in problems),
                        f"zapora przepuscila podmieniona tresc: {problems}")

    def test_podmieniona_tresc_przechodzi_gdy_stara_wersja_jest_w_archiwum(self):
        stara = journal_guard.canonical(entry("event_turn_002", "druga"))
        archiwum = {"events": [{"event_id": "event_turn_002",
                                "content_sha256": journal_guard.sha(stara),
                                "file": "events/x.json"}],
                    "transactions": []}
        working = [entry("event_turn_001", "pierwsza"),
                   entry("event_turn_002", "PONOWNIE ROZEGRANE"),
                   entry("event_turn_003", "trzecia")]
        problems = [p for p in self.uruchom(working, archiwum) if "ARCHIWUM NIEKOMPLETNE" not in p]
        self.assertEqual(problems, [], f"zapora blokuje poprawnie zarchiwizowany retcon: {problems}")


if __name__ == "__main__":
    unittest.main()
