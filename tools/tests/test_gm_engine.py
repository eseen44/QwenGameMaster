from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gm_engine  # noqa: E402


class GameMasterEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = gm_engine.Registry(
            [
                ROOT / "system" / "mechanics",
                ROOT / "system" / "fixtures" / "vertical-slice",
                ROOT / "campaigns" / "lucan" / "migration" / "mechanics",
            ]
        )

    def test_registry_and_build_validate(self) -> None:
        self.assertEqual(gm_engine.validate_registry(self.registry), [])
        spidey = gm_engine.compile_entity("fixture_spidey", self.registry)
        self.assertEqual(spidey["classification"]["operational_rank"], "D")
        self.assertIn("capability_spidey_bite", spidey["capabilities"])
        self.assertEqual(spidey["resources"]["necrotic_reservoir"]["capacity"], 12)
        self.assertEqual(spidey["link"]["passive_connection_cost"], 0)

    def test_spidey_cannot_decapitate_horse_and_roll_is_forbidden(self) -> None:
        result = gm_engine.assess(
            "fixture_spidey",
            "capability_spidey_bite",
            "fixture_horse",
            "intent_decapitate",
            [],
            self.registry,
        )
        self.assertEqual(result["verdict"], "impossible")
        self.assertFalse(result["roll_allowed"])
        self.assertIn("insufficient_tool_or_jaw_span", result["blocking_reasons"])
        self.assertLess(result["comparison"]["rating"], result["comparison"]["defense"])

    def test_spidey_can_conditionally_kill_sleeping_horse_by_necrosis(self) -> None:
        result = gm_engine.assess(
            "fixture_spidey",
            "capability_spidey_bite",
            "fixture_horse",
            "intent_kill",
            ["condition_sleeping"],
            self.registry,
        )
        self.assertEqual(result["verdict"], "conditional")
        self.assertTrue(result["roll_allowed"])
        self.assertEqual(result["best_path"], "necrotic_deterioration")
        self.assertEqual(result["effect_ref"], "effect_spidey_necrosis")
        self.assertIn("reach_contact", result["delivery_requirements"])
        self.assertEqual(result["test_guidance"]["scope"], "effect_resolution")
        self.assertEqual(result["test_guidance"]["suggested_difficulty"], 41)
        self.assertEqual(result["delivery_comparison"]["verdict"], "automatic")
        toxin_path = next(
            item for item in result["alternative_paths"] if item["path_id"] == "paralytic_shutdown"
        )
        self.assertEqual(toxin_path["verdict"], "impossible")
        self.assertEqual(toxin_path["blockers"][0]["reason"], "effect_cannot_reach_lethal_magnitude")
        self.assertEqual(
            result["resource_costs"],
            [{"pool": "necrotic_reservoir", "units": 2}],
        )
        self.assertEqual(result["resource_shortfalls"], [])

    def test_spidey_selects_paralytic_payload_on_demand(self) -> None:
        spidey = gm_engine.compile_entity("candidate_companion_spidey", self.registry)
        bite = self.registry.require("capability_spidey_bite", "capability")
        self.assertEqual(bite["effect_selection"]["mode"], "one_payload_per_bite")
        self.assertTrue(bite["effect_selection"]["controlled_on_demand"])
        self.assertEqual(spidey["resources"]["paralytic_toxin_reservoir"]["capacity"], 4)
        result = gm_engine.assess(
            "candidate_companion_spidey",
            "capability_spidey_bite",
            "fixture_human",
            "intent_apply_condition",
            [],
            self.registry,
        )
        self.assertEqual(result["best_path"], "apply_paralytic_toxin")
        self.assertEqual(
            result["resource_costs"],
            [{"pool": "paralytic_toxin_reservoir", "units": 1}],
        )

    def test_varkhen_cannot_be_overpowered_without_leverage(self) -> None:
        result = gm_engine.assess(
            "fixture_boros",
            "capability_boros_pick_strike",
            "fixture_varkhen",
            "intent_breach",
            [],
            self.registry,
        )
        self.assertEqual(result["verdict"], "impossible")
        self.assertFalse(result["roll_allowed"])

    def test_varkhen_attrition_becomes_possible_after_stacked_leverage(self) -> None:
        result = gm_engine.assess(
            "fixture_boros",
            "capability_boros_pick_strike",
            "fixture_varkhen",
            "intent_breach",
            [
                "condition_varkhen_dormant",
                "condition_varkhen_numbed",
                "condition_varkhen_pinned",
                "condition_recovery_suppressed",
            ],
            self.registry,
        )
        self.assertEqual(result["verdict"], "conditional")
        self.assertTrue(result["roll_allowed"])
        self.assertGreaterEqual(result["comparison"]["margin"], 5)

    def test_numb_is_a_conditional_delivery_against_human(self) -> None:
        result = gm_engine.assess(
            "fixture_lucan",
            "capability_lucan_numb",
            "fixture_human",
            "intent_incapacitate",
            [],
            self.registry,
        )
        self.assertEqual(result["verdict"], "conditional")
        self.assertEqual(result["best_path"], "neuromuscular_suppression")
        self.assertEqual(result["resource_costs"], [{"pool": "lucan_necrotic_energy", "units": 0.1}])

    def test_confusion_is_visible_sustained_control_not_a_cantrip(self) -> None:
        capability = self.registry.require("capability_lucan_confusion", "capability")
        result = gm_engine.assess(
            "fixture_lucan_cemetery",
            "capability_lucan_confusion",
            "fixture_corpse_handler",
            "intent_apply_condition",
            [],
            self.registry,
        )
        self.assertFalse(capability["casting_profile"]["subtle"])
        self.assertTrue(capability["casting_profile"]["concentration"] == "required")
        self.assertIn("mutual_eye_contact", result["delivery_requirements"])
        self.assertEqual(result["resource_costs"], [{"pool": "lucan_necrotic_energy", "units": 3}])

    def test_ranged_bone_chill_costs_more_and_hits_less_hard(self) -> None:
        close_effect = self.registry.require("effect_bone_chill", "effect")
        ranged_effect = self.registry.require("effect_bone_chill_ranged", "effect")
        self.assertEqual(close_effect["resource_cost"]["units"], 1)
        self.assertEqual(ranged_effect["resource_cost"]["units"], 2)
        self.assertLess(ranged_effect["application_rating"], close_effect["application_rating"])
        self.assertLess(ranged_effect["initial_magnitude"], close_effect["initial_magnitude"])

    def test_geo_is_a_point_one_cost_cantrip_per_scan(self) -> None:
        result = gm_engine.assess(
            "candidate_pc_lucan_cutoff",
            "capability_lucan_geo_protocol",
            "candidate_old_crypt_structure",
            "intent_detect_structure",
            [],
            self.registry,
        )
        self.assertEqual(result["resource_costs"], [{"pool": "lucan_necrotic_energy", "units": 0.1}])

    def test_self_repair_is_a_first_level_spell_with_limited_scope(self) -> None:
        result = gm_engine.assess(
            "candidate_pc_lucan_cutoff",
            "capability_lucan_basic_self_repair",
            "candidate_pc_lucan_cutoff",
            "intent_repair_living_tissue",
            [],
            self.registry,
        )
        effect = self.registry.require("effect_lucan_basic_self_repair", "effect")
        self.assertEqual(result["verdict"], "automatic_with_cost")
        self.assertFalse(result["roll_allowed"])
        self.assertEqual(result["resource_costs"], [{"pool": "lucan_necrotic_energy", "units": 1}])
        self.assertEqual(effect["repair_profile"]["one_cast"], "mild_injury_or_one_step_of_moderate_injury")

    def test_vital_overdrive_is_one_nonstacking_burst(self) -> None:
        result = gm_engine.assess(
            "candidate_pc_lucan_cutoff",
            "capability_lucan_vital_overdrive",
            "candidate_pc_lucan_cutoff",
            "intent_temporary_physical_enhancement",
            [],
            self.registry,
        )
        condition = self.registry.require("condition_lucan_vital_overdrive", "condition")
        self.assertEqual(result["verdict"], "automatic_with_cost")
        self.assertFalse(result["roll_allowed"])
        self.assertEqual(result["resource_costs"], [{"pool": "lucan_necrotic_energy", "units": 1}])
        self.assertEqual(condition["stacking"]["maximum_stacks"], 1)
        self.assertEqual(condition["duration"]["maximum_actions"], 1)

    def test_collector_scale_bone_chill_uses_bruteforce_amplification(self) -> None:
        result = gm_engine.amplify_capability(
            "capability_lucan_bone_chill",
            6,
            ["intensity", "area", "range", "persistence"],
            self.registry,
            expertise=32,
            available_energy=5_000,
            channel_intervals=3,
            linked_channel_capacity=20,
            energy_source="collector_overflow",
        )
        self.assertEqual(result["verdict"], "conditional")
        self.assertEqual(result["energy"]["required_per_interval"], 1024)
        self.assertEqual(result["energy"]["required"], 3072)
        self.assertTrue(result["channeling"]["continuous"])
        self.assertAlmostEqual(result["channeling"]["flow_per_second"], 170.666666667)
        self.assertAlmostEqual(result["channeling"]["load_ratio"], 8.533333333)
        self.assertEqual(
            result["channeling"]["load_state"],
            "extreme_overload_permanent_change_possible",
        )
        self.assertEqual(result["energy"]["source"], "collector_overflow")
        self.assertFalse(result["energy"]["draws_from_personal_reserve"])
        self.assertFalse(result["special_education_required"])

    def test_global_bone_chill_is_possible_but_absurdly_inefficient(self) -> None:
        result = gm_engine.amplify_capability(
            "capability_lucan_bone_chill",
            10,
            ["intensity", "area", "range", "duration", "persistence"],
            self.registry,
            expertise=85,
            available_energy=300_000,
        )
        self.assertTrue(result["technically_possible"])
        self.assertEqual(result["energy"]["required"], 262_144)
        self.assertEqual(result["energy"]["cost_ratio_to_optimized"], 512)

    def test_amplification_without_energy_blocks_the_roll(self) -> None:
        result = gm_engine.amplify_capability(
            "capability_lucan_bone_chill",
            6,
            ["intensity", "area", "range", "persistence"],
            self.registry,
            expertise=32,
            available_energy=15,
        )
        self.assertEqual(result["verdict"], "possible_only_with_new_leverage")
        self.assertFalse(result["roll_allowed"])

    def test_stone_wall_requires_leverage_not_a_lucky_roll(self) -> None:
        result = gm_engine.assess(
            "fixture_boros",
            "capability_boros_pick_strike",
            "fixture_stone_wall",
            "intent_breach",
            [],
            self.registry,
        )
        self.assertEqual(result["verdict"], "possible_only_with_new_leverage")
        self.assertFalse(result["roll_allowed"])

    def test_generator_enforces_layered_d_rank_gimmick(self) -> None:
        generated = gm_engine.generate_entity(
            "generated_test_spider",
            "Generated test spider",
            "archetype_tiny_spider",
            "D",
            "infiltrator",
            "necrotic_ambusher",
            ["direct_combat", "area_attacks"],
            self.registry,
        )
        self.assertEqual(generated["status"], "proposed")
        self.assertEqual(generated["classification"]["operational_rank"], "D")
        self.assertIn("direct_combat_is_a_failure_mode", generated["traits"])
        self.assertIn("area_attacks_bypass_small_target_advantage", generated["traits"])
        self.assertEqual(generated["capabilities"], ["capability_necrotic_spider_bite"])
        self.assertLessEqual(max(generated["ratings"].values()), 49)

    def test_generator_can_apply_source_linked_transformation_layer(self) -> None:
        generated = gm_engine.generate_entity(
            "generated_undead_sentinel",
            "Generated undead sentinel",
            "archetype_tiny_spider",
            "D",
            "sentinel",
            "sparse_web_monitor",
            ["stationary_network", "low_direct_offense"],
            self.registry,
            ["modifier_necromantic_animation"],
            ["source_fixture#line:1-2"],
        )
        self.assertIn("undead", generated["traits"])
        self.assertEqual(generated["generation"]["source_refs"], ["source_fixture#line:1-2"])

    def test_generator_rejects_gimmick_without_meaningful_weaknesses(self) -> None:
        with self.assertRaisesRegex(gm_engine.EngineError, "at least 2"):
            gm_engine.generate_entity(
                "invalid_spider",
                "Invalid spider",
                "archetype_tiny_spider",
                "D",
                "infiltrator",
                "necrotic_ambusher",
                [],
                self.registry,
            )

    def test_source_linked_campaign_replay_passes(self) -> None:
        result = gm_engine.run_replay("campaign_lucan_replay_v1", self.registry)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["summary"], {"passed": 42, "failed": 0, "total": 42})


if __name__ == "__main__":
    unittest.main()
