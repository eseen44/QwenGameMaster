from __future__ import annotations

import json
import tempfile
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime


def write_yaml(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")


class GameMasterRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.campaign = Path(self.temp.name)
        write_yaml(
            self.campaign / "campaign.yaml",
            {"schema_version": 1, "id": "campaign_test", "status": "active"},
        )
        write_yaml(
            self.campaign / "context" / "active.yaml",
            {
                "schema_version": 1,
                "campaign_id": "campaign_test",
                "status": "active",
                "always_load": [],
                "active_refs": [],
                "search_terms": [],
            },
        )
        write_yaml(
            self.campaign / "context" / "scene.yaml",
            {
                "schema_version": 1,
                "campaign_id": "campaign_test",
                "status": "active",
                "scene_id": "scene_test",
                "location_ref": None,
                "tension": {"level": 0, "reason": None},
                "participants": ["spidey", "target"],
                "pressures": [],
                "immediate_questions": [],
                "pending_world_reactions": [],
                "last_event_id": None,
            },
        )
        write_yaml(
            self.campaign / "state" / "time.yaml",
            {
                "schema_version": 1,
                "campaign_id": "campaign_test",
                "status": "active",
                "current_datetime": "2026-08-14T12:00:00+02:00",
                "elapsed_seconds_total": 0,
                "last_event_id": None,
            },
        )
        write_yaml(
            self.campaign / "state" / "clocks.yaml",
            {
                "schema_version": 1,
                "campaign_id": "campaign_test",
                "status": "active",
                "clocks": [
                    {
                        "id": "clock_patrol",
                        "progress": 0,
                        "threshold": 1,
                        "seconds_per_step": 600,
                        "elapsed_seconds": 0,
                        "effect": "Patrol arrives.",
                        "world_test_required": True,
                        "triggered": False,
                    }
                ],
            },
        )
        for name, document in {
            "objectives.yaml": {"player_declared": [], "external_pressures": [], "completed": []},
            "resources.yaml": {"shared_resources": [], "transactions": []},
            "reputations.yaml": {"reputations": [], "attitudes": []},
        }.items():
            write_yaml(
                self.campaign / "state" / name,
                {"schema_version": 1, "campaign_id": "campaign_test", "status": "active", **document},
            )
        write_yaml(
            self.campaign / "state" / "instances" / "index.yaml",
            {
                "schema_version": 1,
                "campaign_id": "campaign_test",
                "status": "active",
                "instances": [
                    {"id": "spidey", "ref": "state/instances/spidey.yaml", "state": "active"},
                    {"id": "target", "ref": "state/instances/target.yaml", "state": "active"},
                ],
            },
        )
        write_yaml(
            self.campaign / "state" / "instances" / "spidey.yaml",
            {
                "schema_version": 1,
                "id": "spidey",
                "object_type": "entity_instance",
                "status": "active",
                "definition_ref": "candidate_companion_spidey",
                "revision": 1,
                "resources": {
                    "necrotic_reservoir": {"current": 8, "capacity": 12},
                    "paralytic_toxin_reservoir": {
                        "current": 4,
                        "capacity": 4,
                        "regeneration": {
                            "interval_seconds": 21600,
                            "units": 1,
                            "requires": ["functional_implanted_gland", "fed_or_energized_state"],
                        },
                    },
                },
                "conditions": [],
                "status_flags": ["functional_implanted_gland", "fed_or_energized_state"],
                "last_event_id": None,
            },
        )
        write_yaml(
            self.campaign / "state" / "instances" / "target.yaml",
            {
                "schema_version": 1,
                "id": "target",
                "object_type": "entity_instance",
                "status": "active",
                "definition_ref": "fixture_human",
                "revision": 1,
                "resources": {},
                "conditions": [],
                "last_event_id": None,
            },
        )
        (self.campaign / "journal").mkdir(parents=True, exist_ok=True)
        for name in ("events.jsonl", "rolls.jsonl", "retcons.jsonl"):
            (self.campaign / "journal" / name).write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def request(self, turn_id: str = "turn_test") -> dict:
        return {
            "schema_version": 1,
            "turn_id": turn_id,
            "declared_action": "Spidey gryzie człowieka toksycznymi kłami.",
            "actor_id": "spidey",
            "capability_id": "capability_spidey_bite",
            "target_id": "target",
            "intent_id": "intent_apply_condition",
            "stakes": "Paraliż albo alarm.",
            "scope": "execution",
            "time_class": "brief",
        }

    def outcome(self) -> dict:
        return {
            "schema_version": 1,
            "intent_achieved": True,
            "arrangement": "complicated",
            "perspective": "spidey",
            "summary": "Toksyna została dostarczona, ale nadchodzi patrol.",
            "operations": [
                {
                    "op": "add_condition",
                    "instance_id": "target",
                    "condition": {
                        "id": "paralytic_toxin",
                        "mechanics_ref": "condition_paralytic_toxin_stack",
                        "stacks": 1,
                        "maximum_stacks": 3,
                        "magnitude": 10,
                        "maximum_magnitude": 36,
                        "interval_seconds": 900,
                        "magnitude_per_interval": 4,
                    },
                }
            ],
            "new_decision": "Patrol jest blisko — co robisz?",
        }

    def test_parenthetical_preview_is_noop(self) -> None:
        result = gm_runtime.preview_turn(
            self.campaign,
            {"turn_id": "turn_meta", "declared_action": "(Sprawdzam stan Spideya.)"},
        )
        self.assertEqual(result["status"], "system_only_noop")
        self.assertEqual(result["time_seconds"], 0)

    def test_resolve_commit_is_idempotent_and_ticks_world(self) -> None:
        with mock.patch("gm_runtime.secrets.randbelow", return_value=49):
            transaction = gm_runtime.resolve_turn(self.campaign, self.request(), False)
        self.assertEqual(transaction["status"], "resolved")
        self.assertIsNotNone(transaction["roll"])
        committed = gm_runtime.commit_turn(self.campaign, "turn_test", self.outcome(), False)
        self.assertEqual(committed["status"], "committed")
        again = gm_runtime.commit_turn(self.campaign, "turn_test", self.outcome(), False)
        self.assertEqual(again["status"], "committed")
        spidey = gm_runtime.load_instance(self.campaign, "spidey")[1]
        target = gm_runtime.load_instance(self.campaign, "target")[1]
        self.assertEqual(spidey["resources"]["paralytic_toxin_reservoir"]["current"], 3)
        self.assertEqual(target["conditions"][0]["id"], "paralytic_toxin")
        self.assertEqual(target["conditions"][0]["stacks"], 1)
        events = (self.campaign / "journal" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(events), 1)
        scene = gm_runtime.scene_document(self.campaign)
        self.assertEqual(scene["pending_world_reactions"][0]["id"], "reaction_clock_patrol_1")

    def test_six_hours_regenerates_one_toxin_dose(self) -> None:
        spidey_path, spidey = gm_runtime.load_instance(self.campaign, "spidey")
        spidey["resources"]["paralytic_toxin_reservoir"]["current"] = 2
        write_yaml(spidey_path, spidey)
        request = {
            "turn_id": "turn_rest",
            "declared_action": "Lucan odpoczywa przez sześć godzin.",
            "fiction_verdict": "automatic",
            "time_seconds": 21600,
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "pc_lucan",
            "summary": "Mija sześć godzin.",
            "operations": [],
        }
        gm_runtime.commit_turn(self.campaign, "turn_rest", outcome, False)
        spidey = gm_runtime.load_instance(self.campaign, "spidey")[1]
        self.assertEqual(spidey["resources"]["paralytic_toxin_reservoir"]["current"], 3)

    def test_repeated_fractional_resource_costs_remain_stable(self) -> None:
        request = {
            "turn_id": "turn_fractional_cost",
            "declared_action": "Spidey wydaje trzy drobne porcje energii.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        gm_runtime.commit_turn(
            self.campaign,
            "turn_fractional_cost",
            {
                "intent_achieved": True,
                "arrangement": "unchanged",
                "perspective": "spidey",
                "summary": "Trzy drobne porcje energii zostały zużyte.",
                "operations": [
                    {
                        "op": "consume",
                        "instance_id": "spidey",
                        "pool": "necrotic_reservoir",
                        "units": 0.1,
                    }
                    for _ in range(3)
                ],
            },
            False,
        )
        current = gm_runtime.load_instance(self.campaign, "spidey")[1]["resources"][
            "necrotic_reservoir"
        ]["current"]
        self.assertEqual(current, 7.7)

    def test_stale_revision_rejects_whole_commit(self) -> None:
        request = {
            "turn_id": "turn_stale",
            "declared_action": "Spidey przesuwa się.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "spidey",
            "summary": "Spidey zmienia pozycję.",
            "operations": [
                {
                    "op": "set",
                    "instance_id": "spidey",
                    "path": "position.zone_id",
                    "value": "wall",
                    "expected_revision": 999,
                }
            ],
        }
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.commit_turn(self.campaign, "turn_stale", outcome, False)
        self.assertEqual(gm_runtime.load_instance(self.campaign, "spidey")[1]["revision"], 1)

    def test_recover_finishes_after_event_append_failure(self) -> None:
        request = {
            "turn_id": "turn_recover",
            "declared_action": "Mija chwila.",
            "fiction_verdict": "automatic",
            "time_seconds": 1,
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "world",
            "summary": "Mija sekunda.",
            "operations": [],
        }
        original = gm_runtime.append_jsonl_once
        with mock.patch("gm_runtime.append_jsonl_once", side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                gm_runtime.commit_turn(self.campaign, "turn_recover", outcome, False)
        self.assertEqual(
            gm_runtime.load_yaml(gm_runtime.transaction_path(self.campaign, "turn_recover"))["status"],
            "prepared",
        )
        with mock.patch("gm_runtime.append_jsonl_once", side_effect=original):
            recovered = gm_runtime.recover_turn(self.campaign, "turn_recover", False)
        self.assertEqual(recovered["status"], "committed")
        self.assertTrue(recovered["recovered"])

    def test_recall_and_context_budget(self) -> None:
        (self.campaign / "journal" / "events.jsonl").write_text(
            '{"id":"event_memory","summary":"Varkhen został przejęty."}\n', encoding="utf-8"
        )
        result = gm_runtime.recall(self.campaign, "Varkhen", 5)
        self.assertEqual(len(result["matches"]), 1)
        context = gm_runtime.refresh_context(self.campaign, write=False)
        self.assertLess(context["context_bytes"], gm_runtime.CONTEXT_BUDGET_BYTES)
        real_campaign = gm_runtime.ROOT / "campaigns" / "lucan"
        if real_campaign.exists():
            real_context = gm_runtime.refresh_context(real_campaign, write=False)
            self.assertFalse(any(Path(ref).is_absolute() for ref in real_context["active_refs"]))

    def test_inline_json_request_and_outcome_inputs(self) -> None:
        parser = gm_runtime.build_parser()
        preview_args = parser.parse_args(
            ["turn", "preview", "--request-json", '{"turn_id":"inline","declared_action":"Rozgląda się."}']
        )
        self.assertEqual(gm_runtime.input_from_args(preview_args, "request")["turn_id"], "inline")
        commit_args = parser.parse_args(
            ["turn", "commit", "inline", "--outcome-json", '{"intent_achieved":true}']
        )
        self.assertTrue(gm_runtime.input_from_args(commit_args, "outcome")["intent_achieved"])

    def test_automatic_fiction_turn_does_not_roll(self) -> None:
        request = {
            "turn_id": "turn_obvious",
            "declared_action": "Lucan podnosi przedmiot leżący u jego stóp.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        transaction = gm_runtime.resolve_turn(self.campaign, request, False)
        self.assertIsNone(transaction["roll"])
        self.assertEqual((self.campaign / "journal" / "rolls.jsonl").read_text(encoding="utf-8"), "")

    def test_impossible_mechanical_action_does_not_roll(self) -> None:
        request = {
            "turn_id": "turn_impossible",
            "declared_action": "Spidey próbuje jednym ugryzieniem zdekapitować konia.",
            "actor_id": "spidey",
            "capability_id": "capability_spidey_bite",
            "target_id": "fixture_horse",
            "intent_id": "intent_decapitate",
            "time_seconds": 0,
        }
        transaction = gm_runtime.resolve_turn(self.campaign, request, False)
        self.assertEqual(transaction["preview"]["assessment"]["verdict"], "impossible")
        self.assertIsNone(transaction["roll"])

    def test_due_world_reaction_must_be_resolved(self) -> None:
        first = {
            "turn_id": "turn_clock",
            "declared_action": "Mija dziesięć minut.",
            "fiction_verdict": "automatic",
            "time_seconds": 600,
        }
        gm_runtime.resolve_turn(self.campaign, first, False)
        gm_runtime.commit_turn(
            self.campaign,
            "turn_clock",
            {
                "intent_achieved": True,
                "arrangement": "unchanged",
                "perspective": "world",
                "summary": "Mija dziesięć minut.",
                "operations": [],
            },
            False,
        )
        second = {
            "turn_id": "turn_after_clock",
            "declared_action": "Lucan czeka.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        gm_runtime.resolve_turn(self.campaign, second, False)
        outcome = {
            "intent_achieved": True,
            "arrangement": "worsened",
            "perspective": "world",
            "summary": "Patrol dociera na miejsce.",
            "operations": [],
        }
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.commit_turn(self.campaign, "turn_after_clock", outcome, False)
        outcome["resolved_world_reaction_ids"] = ["reaction_clock_patrol_1"]
        result = gm_runtime.commit_turn(self.campaign, "turn_after_clock", outcome, False)
        self.assertEqual(result["status"], "committed")

    def test_scene_close_creates_snapshot_and_minimal_next_scene(self) -> None:
        result = gm_runtime.close_scene(
            self.campaign,
            "scene_next",
            "Scena testowa zakończona.",
            None,
            ["spidey"],
            False,
        )
        self.assertTrue(Path(result["snapshot"]).exists())
        self.assertEqual(gm_runtime.scene_document(self.campaign)["scene_id"], "scene_next")

    def test_typical_local_turn_runtime_is_below_one_second(self) -> None:
        request = {
            "turn_id": "turn_fast",
            "declared_action": "Lucan wykonuje oczywistą krótką czynność.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "pc_lucan",
            "summary": "Czynność zostaje wykonana.",
            "operations": [],
        }
        started = time.perf_counter()
        gm_runtime.resolve_turn(self.campaign, request, False)
        gm_runtime.commit_turn(self.campaign, "turn_fast", outcome, False)
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_all_public_state_operations_share_one_revision(self) -> None:
        target_path, target = gm_runtime.load_instance(self.campaign, "target")
        target["position"] = {"zone_id": "old"}
        target["integrity"] = {"current": 10, "maximum": 10}
        target["conditions"] = [{"id": "temporary", "source_event_id": "event_old"}]
        write_yaml(target_path, target)
        resources = gm_runtime.load_yaml(self.campaign / "state" / "resources.yaml")
        resources["shared_resources"] = [{"id": "item_test", "owner_id": "a"}]
        write_yaml(self.campaign / "state" / "resources.yaml", resources)
        request = {
            "turn_id": "turn_operations",
            "declared_action": "Rozliczenie wielu trwałych zmian.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        outcome = {
            "intent_achieved": True,
            "arrangement": "mixed",
            "perspective": "world",
            "summary": "Stan zostaje rozliczony.",
            "operations": [
                {"op": "set", "instance_id": "target", "path": "position.zone_id", "value": "new"},
                {"op": "adjust", "instance_id": "target", "path": "integrity.current", "delta": -2},
                {"op": "remove_condition", "instance_id": "target", "condition_id": "temporary"},
                {"op": "add_condition", "instance_id": "target", "condition": {"id": "stacking", "stacks": 2, "maximum_stacks": 3, "magnitude": 5, "maximum_magnitude": 20}},
                {"op": "add_condition", "instance_id": "target", "condition": {"id": "stacking", "stacks": 2, "maximum_stacks": 3, "magnitude": 5, "maximum_magnitude": 20}},
                {"op": "advance_clock", "clock_id": "clock_patrol", "amount": 1},
                {"op": "transfer_item", "item_id": "item_test", "from_owner": "a", "to_owner": "b"},
                {"op": "change_relationship", "subject_id": "npc", "target_id": "pc", "delta": -5, "reason": "test"},
            ],
        }
        gm_runtime.commit_turn(self.campaign, "turn_operations", outcome, False)
        target = gm_runtime.load_instance(self.campaign, "target")[1]
        self.assertEqual(target["revision"], 2)
        self.assertEqual(target["integrity"]["current"], 8)
        self.assertEqual(target["conditions"][0]["stacks"], 3)
        resources = gm_runtime.load_yaml(self.campaign / "state" / "resources.yaml")
        self.assertEqual(resources["shared_resources"][0]["owner_id"], "b")
        reputations = gm_runtime.load_yaml(self.campaign / "state" / "reputations.yaml")
        self.assertEqual(reputations["attitudes"][0]["score"], -5)

    def test_real_migration_uses_user_accepted_history_scope(self) -> None:
        # The original assertion was `ready is False`, which only held while the
        # packages were still unapproved.  Activation flipped it and the test
        # started failing on a fact about the campaign, not about the code.  What
        # this test is actually named after is the scope decision: the missing
        # full chat export must never come back as a blocker.
        readiness = gm_runtime.migration_readiness(gm_runtime.DEFAULT_CAMPAIGN_ROOT)
        self.assertNotIn("blocker_full_chat_unavailable", readiness["blockers"])
        self.assertEqual(readiness["blockers"], [])
        self.assertEqual(readiness["approval_problems"], [])
        self.assertEqual(readiness["ready"], not readiness["blockers"])

    def test_retry_after_crash_reuses_the_journalled_roll(self) -> None:
        request = self.request("turn_crash")
        request["difficulty"] = 50
        original = gm_runtime.atomic_yaml

        def crash_on_transaction(path, document):
            if "transactions" in str(path):
                raise SystemError("simulated crash after the roll was journalled")
            return original(path, document)

        with mock.patch("gm_runtime.atomic_yaml", crash_on_transaction):
            with self.assertRaises(SystemError):
                gm_runtime.resolve_turn(self.campaign, request, False)
        journalled = gm_runtime.journal_record(
            self.campaign / "journal" / "rolls.jsonl", "roll_turn_crash"
        )
        self.assertIsNotNone(journalled)

        transaction = gm_runtime.resolve_turn(self.campaign, request, False)
        self.assertEqual(transaction["roll"], journalled)
        lines = [
            line
            for line in (self.campaign / "journal" / "rolls.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 1)

    def test_context_over_budget_warns_instead_of_failing_the_commit(self) -> None:
        request = {
            "turn_id": "turn_budget",
            "declared_action": "Lucan czeka bez presji.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "pc_lucan",
            "summary": "Nic się nie zmienia.",
            "operations": [],
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        with mock.patch.object(gm_runtime, "CONTEXT_BUDGET_BYTES", 1):
            committed = gm_runtime.commit_turn(self.campaign, "turn_budget", outcome, False)
        self.assertEqual(committed["status"], "committed")
        self.assertTrue(
            any(item.startswith("over_budget") for item in committed["context_warnings"])
        )
        context = gm_runtime.refresh_context(self.campaign, write=False)
        self.assertEqual(context["context_warnings"], [])
        with mock.patch.object(gm_runtime, "CONTEXT_BUDGET_BYTES", 1):
            with self.assertRaises(gm_runtime.RuntimeError):
                gm_runtime.refresh_context(self.campaign, write=False, strict=True)

    def test_iso_datetime_scalars_survive_the_yaml_round_trip_as_strings(self) -> None:
        # PyYAML's implicit timestamp resolver turns an unquoted ISO 8601
        # scalar into a datetime object on load. A real current_datetime
        # (as opposed to a placeholder like "day_0_pre_dawn") used to
        # round-trip through dump_yaml -> load_yaml once and then crash the
        # next commit's document_hash, which calls json.dumps and cannot
        # serialize datetime.
        time_path = self.campaign / "state" / "time.yaml"
        time_doc = gm_runtime.load_yaml(time_path)
        time_doc["current_datetime"] = "2026-08-15T05:00:00+02:00"
        write_yaml(time_path, time_doc)

        reloaded = gm_runtime.load_yaml(time_path)
        self.assertIsInstance(reloaded["current_datetime"], str)
        gm_runtime.document_hash(reloaded)  # must not raise on a datetime-like field

        gm_runtime.atomic_yaml(time_path, reloaded)
        round_tripped = gm_runtime.load_yaml(time_path)
        self.assertEqual(round_tripped["current_datetime"], "2026-08-15T05:00:00+02:00")

        request = {
            "turn_id": "turn_datetime_roundtrip",
            "declared_action": "Mija chwila.",
            "fiction_verdict": "automatic",
            "time_seconds": 60,
        }
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "world",
            "summary": "Czas mija bez zdarzen.",
            "operations": [],
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        committed = gm_runtime.commit_turn(self.campaign, "turn_datetime_roundtrip", outcome, False)
        self.assertEqual(committed["status"], "committed")
        advanced = gm_runtime.load_yaml(time_path)
        self.assertIsInstance(advanced["current_datetime"], str)

    def test_committed_turn_retry_repairs_a_stale_context(self) -> None:
        request = {
            "turn_id": "turn_stale",
            "declared_action": "Lucan porządkuje sprzęt.",
            "fiction_verdict": "automatic",
            "time_seconds": 0,
        }
        outcome = {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "pc_lucan",
            "summary": "Sprzęt uporządkowany.",
            "operations": [],
        }
        gm_runtime.resolve_turn(self.campaign, request, False)
        gm_runtime.commit_turn(self.campaign, "turn_stale", outcome, False)
        active_path = self.campaign / "context" / "active.yaml"
        stale = gm_runtime.load_yaml(active_path)
        stale["last_refreshed_event_id"] = "event_stale"
        write_yaml(active_path, stale)
        gm_runtime.commit_turn(self.campaign, "turn_stale", outcome, False)
        self.assertEqual(
            gm_runtime.load_yaml(active_path)["last_refreshed_event_id"], "event_turn_stale"
        )

    def test_summaries_drop_what_the_narrator_already_has(self) -> None:
        request = self.request("turn_summary")
        request["difficulty"] = 50
        transaction = gm_runtime.resolve_turn(self.campaign, request, False)
        summary = gm_runtime.transaction_summary(transaction)
        self.assertEqual(summary["turn_id"], "turn_summary")
        self.assertEqual(summary["roll"]["natural"], transaction["roll"]["natural_roll"])
        for dropped in ("request", "preview", "prepared_writes", "alternative_paths"):
            self.assertNotIn(dropped, summary)
        committed = gm_runtime.commit_turn(self.campaign, "turn_summary", self.outcome(), False)
        commit_summary = gm_runtime.transaction_summary(committed, self.campaign)
        self.assertEqual(commit_summary["status"], "committed")
        self.assertIn("state/instances/target.yaml", commit_summary["changed"])
        self.assertIn("reaction_clock_patrol_1", commit_summary["pending_world_reactions"])
        self.assertNotIn("prepared_writes", commit_summary)
        self.assertLess(
            len(json.dumps(commit_summary, ensure_ascii=False)),
            len(json.dumps(committed, ensure_ascii=False)) / 3,
        )

    def test_brief_opens_a_session_without_the_journal(self) -> None:
        brief = gm_runtime.session_brief(self.campaign, full=False)
        self.assertEqual(brief["campaign"], "campaign_test")
        self.assertEqual(brief["scene"]["id"], "scene_test")
        self.assertIn("AGENTS.md", brief["rules"])
        self.assertEqual(
            [item["id"] for item in brief["participants"]], ["spidey", "target"]
        )
        self.assertEqual(
            brief["participants"][0]["resources"]["paralytic_toxin_reservoir"], "4/4"
        )
        self.assertEqual([clock["id"] for clock in brief["clocks"]], ["clock_patrol"])
        rendered = json.dumps(brief, ensure_ascii=False)
        self.assertNotIn("source_refs", rendered)
        full = gm_runtime.session_brief(self.campaign, full=True)
        self.assertIn("documents", full)


if __name__ == "__main__":
    unittest.main()
