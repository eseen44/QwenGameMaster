"""Testy etapu 8: rozbicie magazynu uzasadnien i skroty kart NPC.

Dwie najciezsze pozycje tury planowania: act-03-defence.yaml (78 517 B, deklarowany jako
OBOWIAZKOWY przy kazdym planowaniu, czyli 1,92 budzetu) i karty NPC stojacych w scenie
(68 465 B, czyli 167% budzetu, niewidziane przez licznik do etapu 6).

Obie naprawy sa NIEODWRACALNIE ADDYTYWNE co do tresci: magazyn rozbity surowymi liniami
1:1, skroty WYLICZANE z pelnych kart, ktore zostaja jedynym zrodlem prawdy.
"""

from __future__ import annotations

import collections
import re
import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_npc_digests as digests
import gm_runtime

DEFENCE_INDEX = ROOT / "campaigns/lucan/planning/act-03-defence.yaml"
DEFENCE_DIR = ROOT / "campaigns/lucan/planning/act-03-defence"
CARDS = ROOT / "campaigns/lucan/entities/npcs"


def parsed_words(node: object) -> collections.Counter:
    if isinstance(node, str):
        return collections.Counter(re.findall(r"\w+", node))
    if isinstance(node, dict):
        total = collections.Counter()
        for key, value in node.items():
            total += parsed_words(key) + parsed_words(value)
        return total
    if isinstance(node, list):
        total = collections.Counter()
        for value in node:
            total += parsed_words(value)
        return total
    return collections.Counter() if node is None else collections.Counter(re.findall(r"\w+", str(node)))


class DefenceStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = yaml.safe_load(DEFENCE_INDEX.read_text(encoding="utf-8-sig"))

    def test_indeks_jest_maly(self):
        size = DEFENCE_INDEX.stat().st_size
        self.assertLess(size, 8_000, f"indeks spuchl do {size} B - uzasadnienia ida do sekcji")

    def test_indeks_wymienia_kazda_sekcje_ktora_jest_na_dysku(self):
        na_dysku = {p.stem for p in DEFENCE_DIR.glob("*.yaml")}
        w_indeksie = {row["key"] for row in self.index["sections"]}
        self.assertEqual(na_dysku, w_indeksie,
                         "indeks rozjechal sie z katalogiem sekcji")

    def test_kazda_sekcja_wskazuje_z_powrotem_na_indeks(self):
        for path in sorted(DEFENCE_DIR.glob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
            self.assertEqual(document.get("part_of"),
                             "campaigns/lucan/planning/act-03-defence.yaml",
                             f"{path.name} nie wskazuje na indeks")
            self.assertIn("section", document)

    def test_refy_do_sekcji_rozwiazuja_sie(self):
        for row in self.index["sections"]:
            self.assertTrue((ROOT / row["ref"]).is_file(), f"ref sekcji nie istnieje: {row['ref']}")

    def test_nikt_nie_odwoluje_sie_juz_do_starych_kotwic(self):
        """Ref postaci "act-03-defence.yaml#sekcja" nie rozwiaze sie po rozbiciu."""
        winne = []
        for path in list((ROOT / "campaigns").rglob("*.yaml")) + list((ROOT / "campaigns").rglob("*.md")):
            if any(x in path.as_posix() for x in ("/transactions/", "/snapshots/", "/superseded/",
                                                  "/migration/sources/")):
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for match in re.findall(r"act-03-defence\.yaml#([a-z0-9_]+)", text):
                winne.append(f"{path.name}#{match}")
        self.assertEqual(winne, [], f"stare kotwice zostaly: {winne[:5]}")

    def test_planowanie_miesci_sie_w_rozsadnym_koszcie(self):
        """Prog pilnuje, zeby nie wrocil caly magazyn (78 517 B), a nie zeby zbior nie rosl.

        Podniesiony z 10 000 na 20 000 B, gdy uzasadnienia zobowiazan zostaly WYNIESIONE
        z state/obligations.yaml (wczytywanego w KAZDEJ turze) do tego zbioru warunkowego:
        -2 834 B z kazdej tury za +3 771 B tylko przy planowaniu. To jest zysk, nie regresja.
        """
        plan = gm_runtime.context_plan(ROOT / "campaigns" / "lucan", ["choosing_a_plan"])
        self.assertLess(plan["bytes"]["conditional"], 20_000,
                        "zbior planowania znowu wazy tyle, ile caly magazyn")


class DigestTest(unittest.TestCase):
    def test_skroty_sa_aktualne(self):
        files = digests.build(digests.RECENT_DEFAULT)
        stale = [p.name for p, body in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != body]
        self.assertEqual(stale, [], f"skroty nieaktualne: {stale}")

    def test_skrot_jest_istotnie_mniejszy_od_karty(self):
        files = digests.build(digests.RECENT_DEFAULT)
        self.assertTrue(files, "nie powstal zaden skrot")
        for path, body in files.items():
            full = ROOT / yaml.safe_load(body)["full_card"]
            self.assertLess(len(body.encode("utf-8")), full.stat().st_size,
                            f"skrot {path.name} nie jest mniejszy od karty")

    def test_skrot_trzyma_cala_czesc_jak_grac(self):
        card = yaml.safe_load((CARDS / "seraphine-vale.yaml").read_text(encoding="utf-8-sig"))
        digest = yaml.safe_load((CARDS / "digests" / "seraphine-vale.yaml").read_text(encoding="utf-8"))
        self.assertEqual(digest["portrayal"], card["portrayal"])
        self.assertEqual(digest["speech_traits"], card["speech_traits"])
        self.assertEqual(digest["agenda"], card["agenda"])
        self.assertEqual(digest["knowledge"]["forbidden_without_source"],
                         card["knowledge"]["forbidden_without_source"])

    def test_zaden_fakt_nie_wypada_ze_skrotu_bez_sladu(self):
        """Starszy fakt moze stracic szczegol, ale NIE moze zniknac z widoku."""
        card = yaml.safe_load((CARDS / "seraphine-vale.yaml").read_text(encoding="utf-8-sig"))
        digest = yaml.safe_load((CARDS / "digests" / "seraphine-vale.yaml").read_text(encoding="utf-8"))
        w_karcie = {entry.get("fact_id") for entry in card["knowledge"]["confirmed"]}
        w_skrocie = {entry.get("fact_id") for entry in digest["knowledge"]["recent_confirmed"]}
        w_indeksie = {line.split(" <- ")[0] for line in digest["knowledge"]["older_confirmed_index"]}
        brak = sorted(w_karcie - (w_skrocie | w_indeksie))
        self.assertEqual(brak, [], f"fakty niewidoczne w skrocie: {brak}")

    def test_skrot_mowi_ze_nie_jest_kanonem_i_wskazuje_karte(self):
        digest = yaml.safe_load((CARDS / "digests" / "seraphine-vale.yaml").read_text(encoding="utf-8"))
        self.assertIn("NIE TRAKTUJ JAKO KANONU", digest["digest_note"])
        self.assertTrue((ROOT / digest["full_card"]).is_file())

    def test_skrot_niesie_ostrzezenie_o_swiezosci(self):
        digest = yaml.safe_load((CARDS / "digests" / "seraphine-vale.yaml").read_text(encoding="utf-8"))
        self.assertIn("retcon_000121", digest["freshness"]["warning"])
        self.assertIsNotNone(digest["freshness"]["turns_behind"])

    def test_brief_podaje_skrot_i_oba_rozmiary(self):
        brief = gm_runtime.session_brief(ROOT / "campaigns" / "lucan", False)
        z_kartami = [p for p in brief["participants"] if "entity_ref" in p]
        self.assertTrue(z_kartami)
        for participant in z_kartami:
            if participant.get("digest_ref"):
                self.assertLess(participant["digest_bytes"], participant["full_card_bytes"])


if __name__ == "__main__":
    unittest.main()
