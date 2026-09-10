"""Context/perspective regressions. These do not claim to evaluate model prose quality."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import build_npc_digests as digests
import gm_runtime as runtime
import prose_check
import test_gm_runtime as fixtures


class ContextTest(unittest.TestCase):
    def test_brief_export_and_plan_load_the_same_sources(self):
        campaign = runtime.DEFAULT_CAMPAIGN_ROOT
        brief = runtime.session_brief(campaign, full=True)
        plan = runtime.context_plan(campaign, [])
        refs = {row["ref"] for row in plan["base"] + plan["participant_cards"]}
        self.assertEqual(refs, {row["ref"] for row in brief["documents"]})
        self.assertEqual(plan["bytes"]["total"],
                         sum(len(row["content"].encode("utf-8")) for row in brief["documents"]))
        self.assertEqual(brief["context_total_bytes"], plan["bytes"]["total"])
        self.assertEqual(set(brief["participant_refs"]),
                         {row["ref"] for row in plan["participant_cards"]})
        for npc in brief["participants"]:
            if npc.get("digest_ref"):
                self.assertIn(npc["digest_ref"], refs)
                self.assertNotIn(npc["entity_ref"], refs)

    def test_npc_without_digest_loads_card_and_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            card = Path(tmp) / "npc.yaml"
            voice = Path(tmp) / "voices" / "npc.yaml"
            voice.parent.mkdir()
            card.write_text("id: npc_test\n", encoding="utf-8")
            voice.write_text("npc_id: npc_test\n", encoding="utf-8")
            with mock.patch.object(runtime, "participant_card_refs", return_value=[str(card)]):
                refs = runtime.participant_context_refs(Path(tmp), {})
            self.assertEqual(refs, [str(card), str(voice)])

    def test_budget_is_configurable_and_validated(self):
        self.assertEqual(runtime.context_budget({}), runtime.CONTEXT_BUDGET_BYTES)
        self.assertEqual(runtime.context_budget({"context_policy": {"source_budget_bytes": 65536}}), 65536)
        for value in (0, -1, True, "98304", 1.5):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeError):
                runtime.context_budget({"context_policy": {"source_budget_bytes": value}})

    def test_conditional_rule_already_in_base_is_not_counted_twice(self):
        campaign = runtime.DEFAULT_CAMPAIGN_ROOT
        active = runtime.load_yaml(campaign / "context/active.yaml")
        active["load_when_repeat"] = ["AGENTS.md", *active["always_load"]]
        real_load = runtime.load_yaml
        def load(path):
            return active if Path(path) == campaign / "context/active.yaml" else real_load(path)
        with mock.patch.object(runtime, "load_yaml", side_effect=load):
            base = runtime.context_plan(campaign, [])
            repeated = runtime.context_plan(campaign, ["repeat", "repeat"])
        self.assertEqual(base["bytes"]["total"], repeated["bytes"]["total"])
        self.assertEqual(repeated["conditional"], [])


class KnowledgeTest(unittest.TestCase):
    def test_semantic_summary_keeps_the_qualifier_even_with_small_cap(self):
        summary = "Widział kapłana dawniej. Nie wie, czy kapłan przychodzi nadal."
        fact = {"fact_id": "visits", "source_event_id": "event_turn_1",
                "claim": "Długi protokół. " * 50, "recall_summary": summary}
        result = digests.scisnij_wpisy([fact], "card.yaml", cap=12)[0]
        self.assertEqual(result["claim"], summary)
        self.assertTrue(result["claim_summarized"])
        self.assertEqual(result["claim_full"], "card.yaml#visits")
        self.assertNotIn("claim_truncated", result)
        self.assertEqual(fact["recall_summary"], summary)  # no mutation of canonical input

    def test_unsummarized_fact_is_marked_incomplete_with_source(self):
        fact = {"fact_id": "visits", "source_event_id": "event_turn_1",
                "claim": "Widział kapłana. Nie wie, czy kapłan przychodzi nadal."}
        result = digests.scisnij_wpisy([fact], "card.yaml", cap=18)[0]
        self.assertTrue(result["claim_truncated"])
        self.assertEqual(result["claim_full"], "card.yaml#visits")

    def test_digest_check_never_deletes_obsolete_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            stale = Path(tmp) / "stale.yaml"
            stale.write_text("old digest", encoding="utf-8")
            with mock.patch.object(digests, "DIGESTS", Path(tmp)), \
                 mock.patch.object(digests, "ROOT", Path(tmp)), \
                 mock.patch.object(digests, "build", return_value={}), \
                 mock.patch.object(sys, "argv", ["build_npc_digests.py", "--check"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(digests.main(), 1)
            self.assertEqual(stale.read_text(), "old digest")


class ProseGateTest(unittest.TestCase):
    def test_internal_references_rejected_but_world_language_allowed(self):
        for token in ("retcon_000164", "capability_scan", "voice_contract#body",
                      "outcome.audit", "knowledge.confirmed", "state/time.yaml"):
            with self.subTest(token=token), self.assertRaises(runtime.RuntimeError):
                runtime.validate_prose_contract({"prose": "Strażnik wskazał " + token})
        runtime.validate_prose_contract({"prose":
            "— Protokół został w gildii. Pieczęć nadal świeci.\nW korytarzu pachniało wilgotnym wapnem."})

    def run_gate(self, events):
        with mock.patch.object(prose_check, "wpisy", return_value=events), \
             mock.patch.object(sys, "argv", ["prose_check.py", "--new-only", "--quiet"]), \
             contextlib.redirect_stdout(io.StringIO()):
            return prose_check.main()

    def test_audit_only_turn_cannot_evade_gate(self):
        self.assertEqual(self.run_gate([{"id": "event_turn_257", "audit": "x" * 2001}]), 1)

    def test_new_only_checks_older_than_last_twenty(self):
        bad = {"id": "event_turn_257", "prose": "voice_contract", "audit": ""}
        good = [{"id": f"event_turn_{n}", "prose": "Cisza.", "audit": ""} for n in range(258, 283)]
        self.assertEqual(self.run_gate([bad, *good]), 1)

    def test_old_prose_is_exempt_without_moving_audit_baseline(self):
        self.assertEqual(self.run_gate([{"id": "event_turn_248", "audit": "x" * 6000}]), 0)
        self.assertEqual(self.run_gate([{"id": "event_turn_256", "prose": "voice_contract"}]), 0)


class SceneTransitionTest(unittest.TestCase):
    # Reuse only setup/teardown, not the existing test suite.
    setUp = fixtures.GameMasterRuntimeTests.setUp
    tearDown = fixtures.GameMasterRuntimeTests.tearDown

    def prepare(self):
        self.location = self.campaign / "locations/destination/location.yaml"
        fixtures.write_yaml(self.location, {"id": "loc_destination"})
        runtime.resolve_turn(self.campaign, {
            "turn_id": "turn_transition", "actor_id": "spidey",
            "declared_action": "Spidey wchodzi do sąsiedniej komnaty.",
            "fiction_verdict": "automatic", "time_seconds": 0,
        }, False)
        return {"intent_achieved": True, "arrangement": "unchanged", "perspective": "spidey",
                "summary": "Spidey w sąsiedniej komnacie.",
                "scene_update": {"location_ref": str(self.location), "participants": ["spidey"]},
                "operations": [{"op": "set", "instance_id": "spidey", "path": "position",
                                "value": {"location_id": "loc_destination"}}]}

    def test_transition_is_committed_with_presence_and_position(self):
        outcome = self.prepare()
        before = (self.campaign / "state/instances/target.yaml").read_bytes()
        runtime.commit_turn(self.campaign, "turn_transition", outcome, False)
        scene = runtime.scene_document(self.campaign)
        self.assertEqual(scene["participants"], ["spidey"])
        self.assertEqual(scene["location_ref"], str(self.location))
        self.assertEqual(runtime.scene_position_warnings(self.campaign, scene), [])
        self.assertEqual(before, (self.campaign / "state/instances/target.yaml").read_bytes())

    def test_invalid_scene_update_rejects_all_pending_writes(self):
        outcome = self.prepare()
        outcome["scene_update"]["participants"] = ["unknown_npc"]
        before = (self.campaign / "state/instances/spidey.yaml").read_bytes()
        with self.assertRaises(runtime.RuntimeError):
            runtime.commit_turn(self.campaign, "turn_transition", outcome, False)
        self.assertEqual(before, (self.campaign / "state/instances/spidey.yaml").read_bytes())
        self.assertEqual((self.campaign / "journal/events.jsonl").read_text(), "")

    def test_position_mismatch_is_reported_without_teleporting_npc(self):
        self.prepare()
        path = self.campaign / "state/instances/spidey.yaml"
        actor = runtime.load_yaml(path)
        actor["position"] = {"location_id": "loc_elsewhere"}
        fixtures.write_yaml(path, actor)
        before = path.read_bytes()
        scene = {"location_ref": str(self.location), "participants": ["spidey"]}
        warnings = runtime.scene_position_warnings(self.campaign, scene)
        self.assertTrue(any("scene_position_mismatch:spidey" in value for value in warnings))
        self.assertEqual(before, path.read_bytes())

    def test_existing_non_location_file_is_rejected_before_commit(self):
        outcome = self.prepare()
        outcome["scene_update"]["location_ref"] = str(self.campaign / "state/time.yaml")
        with self.assertRaises(runtime.RuntimeError):
            runtime.commit_turn(self.campaign, "turn_transition", outcome, False)
        self.assertEqual((self.campaign / "journal/events.jsonl").read_text(), "")


if __name__ == "__main__":
    unittest.main()
