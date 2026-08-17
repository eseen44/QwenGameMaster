"""Deterministic capability engine for GameMaster YAML objects.

The engine answers whether an action is physically/mechanically available before
the d100 layer is allowed to resolve uncertainty. It deliberately does not roll.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOTS = (
    ROOT / "system" / "mechanics",
    ROOT / "system" / "fixtures" / "vertical-slice",
    ROOT / "campaigns" / "lucan" / "migration" / "mechanics",
)


class EngineError(ValueError):
    """A readable rules or object error."""


class _StringDatesLoader(yaml.SafeLoader):
    """SafeLoader that never auto-converts ISO-looking scalars to datetime/date.

    See the identical loader in gm_runtime.py for why: an unquoted ISO 8601
    timestamp round-tripped through yaml would otherwise become a Python
    datetime, which json.dumps (used for hashing) cannot serialize.
    """


_StringDatesLoader.yaml_implicit_resolvers = {
    key: [item for item in resolvers if item[0] != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=_StringDatesLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise EngineError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EngineError(f"{path}: YAML root must be a mapping")
    return data


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def get_path(document: dict[str, Any], dotted: str) -> Any:
    current: Any = document
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise EngineError(f"missing value at {dotted}")
        current = current[part]
    return current


def set_path(document: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    current = document
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise EngineError(f"cannot set {dotted}: {part} is not a mapping")
        current = child
    current[parts[-1]] = value


def adjust_path(document: dict[str, Any], dotted: str, delta: int | float) -> None:
    value = get_path(document, dotted)
    if not isinstance(value, (int, float)):
        raise EngineError(f"cannot adjust non-numeric value at {dotted}")
    adjusted = value + delta
    if dotted.split(".", 1)[0] in RATING_SECTIONS:
        adjusted = max(0, min(100, adjusted))
    set_path(document, dotted, adjusted)


class Registry:
    def __init__(self, roots: Iterable[Path]):
        self.roots = tuple(Path(root).resolve() for root in roots)
        self.objects: dict[str, dict[str, Any]] = {}
        self.paths: dict[str, Path] = {}
        for root in self.roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.yaml")):
                document = load_yaml(path)
                object_id = document.get("id")
                object_type = document.get("object_type")
                if not isinstance(object_id, str) or not isinstance(object_type, str):
                    continue
                if object_id in self.objects:
                    raise EngineError(
                        f"duplicate object id {object_id}: {self.paths[object_id]} and {path}"
                    )
                self.objects[object_id] = document
                self.paths[object_id] = path

    def require(self, object_id: str, object_type: str | None = None) -> dict[str, Any]:
        try:
            result = self.objects[object_id]
        except KeyError as exc:
            raise EngineError(f"unknown object id: {object_id}") from exc
        if object_type and result.get("object_type") != object_type:
            raise EngineError(
                f"{object_id} is {result.get('object_type')}, expected {object_type}"
            )
        return copy.deepcopy(result)


def apply_modifier(entity: dict[str, Any], modifier: dict[str, Any]) -> None:
    if modifier.get("object_type") != "modifier":
        raise EngineError(f"{modifier.get('id')} is not a modifier")
    deep_merge(entity, modifier.get("overrides", {}))
    for dotted, delta in modifier.get("adjustments", {}).items():
        adjust_path(entity, dotted, delta)
    for dotted, values in modifier.get("append", {}).items():
        try:
            target = get_path(entity, dotted)
        except EngineError:
            target = []
            set_path(entity, dotted, target)
        if not isinstance(target, list) or not isinstance(values, list):
            raise EngineError(f"modifier append at {dotted} requires lists")
        for value in values:
            if value not in target:
                target.append(copy.deepcopy(value))


def compile_build(build: dict[str, Any], registry: Registry) -> dict[str, Any]:
    if build.get("object_type") != "build":
        raise EngineError(f"{build.get('id')} is not a build")
    base_ref = build.get("base_ref")
    if not isinstance(base_ref, str):
        raise EngineError("build requires base_ref")
    entity = registry.require(base_ref, "archetype")
    entity["object_type"] = "entity"
    source_layers = [base_ref]
    for layer_ref in build.get("layers", []):
        if not isinstance(layer_ref, str):
            raise EngineError("layer refs must be strings")
        modifier = registry.require(layer_ref, "modifier")
        apply_modifier(entity, modifier)
        source_layers.append(layer_ref)
    deep_merge(entity, build.get("overrides", {}))
    entity["id"] = build["id"]
    entity["name"] = build.get("name", entity.get("name", build["id"]))
    entity["status"] = build.get("status", "proposed")
    entity["classification"] = copy.deepcopy(build.get("classification", {}))
    entity["build"] = {
        "base_ref": base_ref,
        "layers": source_layers[1:],
        "compiled_from": build["id"],
    }
    validate_entity(entity)
    return entity


def compile_entity(object_id: str, registry: Registry) -> dict[str, Any]:
    document = registry.require(object_id)
    if document.get("object_type") == "build":
        return compile_build(document, registry)
    if document.get("object_type") not in ("entity", "archetype"):
        raise EngineError(f"{object_id} cannot act as an entity")
    validate_entity(document)
    return document


RATING_SECTIONS = {"ratings", "defenses", "resistances"}


def _validate_ratings(node: Any, path: str, errors: list[str]) -> None:
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        child_path = f"{path}.{key}" if path else key
        if key in RATING_SECTIONS and isinstance(value, dict):
            for rating_name, rating in value.items():
                if not isinstance(rating, (int, float)) or not 0 <= rating <= 100:
                    errors.append(f"{child_path}.{rating_name} must be within 0..100")
        _validate_ratings(value, child_path, errors)


def validate_entity(entity: dict[str, Any]) -> None:
    errors: list[str] = []
    if not isinstance(entity.get("id"), str):
        errors.append("entity requires id")
    _validate_ratings(entity, "", errors)
    for pool_id, pool in entity.get("resources", {}).items():
        if not isinstance(pool, dict):
            errors.append(f"resource {pool_id} must be a mapping")
            continue
        current, capacity = pool.get("current"), pool.get("capacity")
        if not isinstance(current, (int, float)) or not isinstance(capacity, (int, float)):
            errors.append(f"resource {pool_id} requires numeric current and capacity")
        elif current < 0 or capacity < 0 or current > capacity:
            errors.append(f"resource {pool_id} must satisfy 0 <= current <= capacity")
    if errors:
        raise EngineError(f"{entity.get('id', '<entity>')}: " + "; ".join(errors))


def resolve_capability(
    actor: dict[str, Any], capability_id: str, registry: Registry
) -> dict[str, Any]:
    if capability_id not in actor.get("capabilities", []):
        raise EngineError(f"{actor['id']} does not have capability {capability_id}")
    return registry.require(capability_id, "capability")


def apply_conditions(
    actor: dict[str, Any],
    target: dict[str, Any],
    capability: dict[str, Any],
    condition_ids: list[str],
    registry: Registry,
) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    contexts = {"actor": actor, "target": target, "capability": capability}
    for condition_id in condition_ids:
        condition = registry.require(condition_id, "condition")
        for dotted, delta in condition.get("adjustments", {}).items():
            root, separator, remainder = dotted.partition(".")
            if not separator or root not in contexts:
                raise EngineError(f"condition {condition_id}: bad adjustment path {dotted}")
            adjust_path(contexts[root], remainder, delta)
        applied.append(condition)
    return applied


def compare(operator: str, left: Any, right: Any) -> bool:
    operations = {
        ">=": lambda: left >= right,
        "<=": lambda: left <= right,
        ">": lambda: left > right,
        "<": lambda: left < right,
        "==": lambda: left == right,
    }
    if operator not in operations:
        raise EngineError(f"unsupported comparison operator: {operator}")
    return bool(operations[operator]())


def margin_verdict(margin: float, scale: dict[str, Any]) -> dict[str, Any]:
    bands = sorted(scale["margin_bands"], key=lambda item: item["minimum"], reverse=True)
    for band in bands:
        if margin >= band["minimum"]:
            return band
    raise EngineError("scale has no margin band covering the result")


def evaluate_delivery(
    capability: dict[str, Any], target: dict[str, Any], scale: dict[str, Any]
) -> dict[str, Any] | None:
    delivery = capability.get("delivery", {})
    rating_path = delivery.get("rating_path")
    defense_path = delivery.get("target_defense_path")
    if not rating_path and not defense_path:
        return None
    if not isinstance(rating_path, str) or not isinstance(defense_path, str):
        raise EngineError(
            f"{capability.get('id')}: delivery needs both rating_path and target_defense_path"
        )
    rating = get_path(capability, rating_path)
    defense = get_path(target, defense_path)
    if not isinstance(rating, (int, float)) or not isinstance(defense, (int, float)):
        raise EngineError(f"{capability.get('id')}: delivery comparison must be numeric")
    margin = rating - defense
    band = margin_verdict(margin, scale)
    return {
        "rating_path": f"capability.{rating_path}",
        "defense_path": f"target.{defense_path}",
        "rating": rating,
        "defense": defense,
        "margin": margin,
        "band": band["id"],
        "verdict": band["verdict"],
    }


def evaluate_path(
    path: dict[str, Any],
    actor: dict[str, Any],
    target: dict[str, Any],
    capability: dict[str, Any],
    registry: Registry,
    scale: dict[str, Any],
) -> dict[str, Any]:
    context = {"actor": actor, "target": target, "capability": capability}
    effect = None
    if path.get("effect_ref"):
        effect = registry.require(path["effect_ref"], "effect")
        context["effect"] = effect
    blockers: list[dict[str, Any]] = []
    for limit in path.get("hard_limits", []):
        left_root, _, left_path = limit["left"].partition(".")
        right_root, _, right_path = limit["right"].partition(".")
        left = get_path(context[left_root], left_path)
        right = get_path(context[right_root], right_path)
        if not compare(limit["operator"], left, right):
            blockers.append(
                {
                    "reason": limit["reason"],
                    "left": {"path": limit["left"], "value": left},
                    "operator": limit["operator"],
                    "right": {"path": limit["right"], "value": right},
                }
            )
    resource_costs = list(capability.get("resource_costs", []))
    if effect and effect.get("resource_cost"):
        resource_costs.append(effect["resource_cost"])
    resource_shortfalls: list[dict[str, Any]] = []
    for cost in resource_costs:
        pool_id, units = cost.get("pool"), cost.get("units")
        pool = actor.get("resources", {}).get(pool_id)
        available = pool.get("current") if isinstance(pool, dict) else None
        if not isinstance(units, (int, float)) or not isinstance(available, (int, float)):
            resource_shortfalls.append(
                {"pool": pool_id, "required": units, "available": available}
            )
        elif available < units:
            resource_shortfalls.append(
                {"pool": pool_id, "required": units, "available": available}
            )
    rating_root, _, rating_path = path["rating_path"].partition(".")
    defense_root, _, defense_path = path["defense_path"].partition(".")
    rating = get_path(context[rating_root], rating_path)
    defense = get_path(context[defense_root], defense_path)
    if not isinstance(rating, (int, float)) or not isinstance(defense, (int, float)):
        raise EngineError(f"path {path['id']} rating and defense must be numeric")
    margin = rating - defense
    band = margin_verdict(margin, scale)
    effect_verdict = band["verdict"]
    delivery = evaluate_delivery(capability, target, scale)
    verdict = effect_verdict
    if delivery and VERDICT_PRIORITY[delivery["verdict"]] < VERDICT_PRIORITY[verdict]:
        verdict = delivery["verdict"]
    if blockers:
        verdict = "impossible"
    if not blockers and resource_shortfalls:
        verdict = "possible_only_with_new_leverage"
    return {
        "path_id": path["id"],
        "verdict": verdict,
        "rating": rating,
        "defense": defense,
        "margin": margin,
        "band": band["id"],
        "effect_verdict": effect_verdict,
        "delivery_comparison": delivery,
        "blockers": blockers,
        "resource_costs": resource_costs,
        "resource_shortfalls": resource_shortfalls,
        "effect_ref": path.get("effect_ref"),
    }


VERDICT_PRIORITY = {
    "impossible": 0,
    "possible_only_with_new_leverage": 1,
    "contested": 2,
    "conditional": 3,
    "automatic_with_cost": 4,
    "automatic": 5,
}


def expand_intent_paths(
    intent: dict[str, Any], capability: dict[str, Any], registry: Registry
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    capability_effects = [
        registry.require(effect_id, "effect")
        for effect_id in capability.get("effects", [])
    ]
    for path in intent.get("paths", []):
        vector = path.get("effect_vector")
        if not vector:
            expanded.append(path)
            continue
        matching = [effect for effect in capability_effects if effect.get("vector") == vector]
        for index, effect in enumerate(matching):
            concrete = copy.deepcopy(path)
            concrete.pop("effect_vector", None)
            concrete["effect_ref"] = effect["id"]
            if len(matching) > 1:
                concrete["id"] = f"{path['id']}:{effect['id']}"
            expanded.append(concrete)
    return expanded


def assess(
    actor_id: str,
    capability_id: str,
    target_id: str,
    intent_id: str,
    condition_ids: list[str],
    registry: Registry,
) -> dict[str, Any]:
    actor = compile_entity(actor_id, registry)
    target = compile_entity(target_id, registry)
    return assess_entities(
        actor,
        capability_id,
        target,
        intent_id,
        condition_ids,
        registry,
        actor_label=actor_id,
        target_label=target_id,
    )


def assess_entities(
    actor: dict[str, Any],
    capability_id: str,
    target: dict[str, Any],
    intent_id: str,
    condition_ids: list[str],
    registry: Registry,
    *,
    actor_label: str | None = None,
    target_label: str | None = None,
) -> dict[str, Any]:
    """Assess already compiled entities, including campaign runtime overlays."""

    actor_id = actor_label or actor.get("id", "<actor>")
    target_id = target_label or target.get("id", "<target>")
    validate_entity(actor)
    validate_entity(target)
    capability = resolve_capability(actor, capability_id, registry)
    intent = registry.require(intent_id, "intent")
    scale = registry.require("core_capability_scale", "scale")
    applied = apply_conditions(actor, target, capability, condition_ids, registry)
    intent_paths = expand_intent_paths(intent, capability, registry)
    paths = [
        evaluate_path(path, actor, target, capability, registry, scale)
        for path in intent_paths
        if not path.get("requires_capability_tag")
        or path["requires_capability_tag"] in capability.get("tags", [])
        if not path.get("effect_ref")
        or path["effect_ref"] in capability.get("effects", [])
    ]
    if not paths:
        raise EngineError(f"intent {intent_id} has no applicable path for {capability_id}")
    best = max(paths, key=lambda item: (VERDICT_PRIORITY[item["verdict"]], item["margin"]))
    requirements = list(capability.get("delivery", {}).get("requirements", []))
    verdict = best["verdict"]
    if requirements and best["delivery_comparison"] is None and verdict in (
        "automatic", "automatic_with_cost"
    ):
        verdict = "conditional"
    roll_allowed = verdict in ("conditional", "contested")
    delivery_comparison = best["delivery_comparison"]
    delivery_is_bottleneck = bool(
        delivery_comparison
        and (
            VERDICT_PRIORITY[delivery_comparison["verdict"]]
            < VERDICT_PRIORITY[best["effect_verdict"]]
            or (
                VERDICT_PRIORITY[delivery_comparison["verdict"]]
                == VERDICT_PRIORITY[best["effect_verdict"]]
                and delivery_comparison["margin"] <= best["margin"]
            )
        )
    )
    if verdict == "contested":
        test_guidance = {
            "scope": "delivery_resolution" if delivery_is_bottleneck else "effect_resolution",
            "suggested_difficulty": max(
                1,
                min(
                    100,
                    round(
                        50
                        - (
                            delivery_comparison["margin"]
                            if delivery_is_bottleneck
                            else best["margin"]
                        )
                    ),
                ),
            ),
            "note": "Apply actor-specific execution and In Character modifiers separately.",
        }
    elif verdict == "conditional":
        if delivery_comparison:
            governing_margin = (
                delivery_comparison["margin"] if delivery_is_bottleneck else best["margin"]
            )
            test_guidance = {
                "scope": "delivery_resolution" if delivery_is_bottleneck else "effect_resolution",
                "suggested_difficulty": max(1, min(100, round(50 - governing_margin))),
                "note": "Roll only the governing uncertainty; the other comparison is already established.",
            }
        else:
            test_guidance = {
                "scope": "delivery_requirements",
                "suggested_difficulty": None,
                "note": "Assess access, approach or positioning separately; do not reroll effect physics.",
            }
    else:
        test_guidance = {
            "scope": None,
            "suggested_difficulty": None,
            "note": "No d100 test is allowed or required for this mechanical comparison.",
        }
    return {
        "actor": actor_id,
        "capability": capability_id,
        "target": target_id,
        "intent": intent_id,
        "conditions": [item["id"] for item in applied],
        "verdict": verdict,
        "roll_allowed": roll_allowed,
        "test_guidance": test_guidance,
        "best_path": best["path_id"],
        "comparison": {
            "rating": best["rating"],
            "defense": best["defense"],
            "margin": best["margin"],
            "band": best["band"],
        },
        "delivery_comparison": delivery_comparison,
        "blocking_reasons": [item["reason"] for item in best["blockers"]],
        "hard_limit_details": best["blockers"],
        "delivery_requirements": requirements,
        "effect_ref": best["effect_ref"],
        "resource_costs": best["resource_costs"],
        "resource_shortfalls": best["resource_shortfalls"],
        "alternative_paths": [item for item in paths if item is not best],
        "rule": "A d100 roll may resolve uncertainty only when roll_allowed is true.",
    }


def validate_registry(registry: Registry) -> list[str]:
    errors: list[str] = []
    for object_id, document in registry.objects.items():
        try:
            object_type = document.get("object_type")
            if object_type == "build":
                compile_build(document, registry)
            elif object_type in ("entity", "archetype"):
                validate_entity(document)
            elif object_type == "capability":
                _validate_ratings(document, "", local_errors := [])
                if local_errors:
                    raise EngineError("; ".join(local_errors))
                for effect_ref in document.get("effects", []):
                    registry.require(effect_ref, "effect")
                delivery = document.get("delivery", {})
                if bool(delivery.get("rating_path")) != bool(
                    delivery.get("target_defense_path")
                ):
                    raise EngineError(
                        "delivery must define rating_path and target_defense_path together"
                    )
            elif object_type == "effect":
                rating = document.get("application_rating")
                if rating is not None and (
                    not isinstance(rating, (int, float)) or not 0 <= rating <= 100
                ):
                    raise EngineError("application_rating must be within 0..100")
            elif object_type == "amplification_scale":
                tiers = document.get("tiers", [])
                gaps = document.get("gap_penalties", [])
                if {row.get("tier") for row in tiers} != set(range(11)):
                    raise EngineError("amplification scale must define tiers 0 through 10")
                if {row.get("gap") for row in gaps} != set(range(11)):
                    raise EngineError("amplification scale must define gaps 0 through 10")
                if not document.get("axes") or document.get("additional_axis_multiplier", 0) < 1:
                    raise EngineError("amplification scale needs axes and a positive axis multiplier")
            elif object_type == "intent":
                if not document.get("paths"):
                    raise EngineError("intent requires at least one path")
            elif object_type == "replay":
                if not document.get("cases"):
                    raise EngineError("replay requires at least one case")
                replay_result = run_replay(object_id, registry)
                if replay_result["status"] != "passed":
                    failed_ids = [
                        item["id"] for item in replay_result["cases"] if not item["ok"]
                    ]
                    raise EngineError(f"replay failed: {', '.join(failed_ids)}")
        except EngineError as exc:
            errors.append(f"{object_id}: {exc}")
    return errors


def run_replay(replay_id: str, registry: Registry) -> dict[str, Any]:
    replay = registry.require(replay_id, "replay")
    results: list[dict[str, Any]] = []
    passed = 0
    for case in replay.get("cases", []):
        case_id = case.get("id")
        try:
            if case.get("mode") == "amplify":
                result = amplify_capability(
                    case["capability"],
                    case["target_tier"],
                    case.get("axes", []),
                    registry,
                    effect_id=case.get("effect"),
                    expertise=case.get("expertise"),
                    available_energy=case.get("available_energy"),
                    base_tier=case.get("base_tier"),
                    channel_intervals=case.get("channel_intervals", 1),
                    linked_channel_capacity=case.get("linked_channel_capacity"),
                    energy_source=case.get("energy_source"),
                )
            else:
                result = assess(
                    case["actor"],
                    case["capability"],
                    case["target"],
                    case["intent"],
                    case.get("conditions", []),
                    registry,
                )
            mismatches = []
            for dotted, expected in case.get("expected", {}).items():
                observed = get_path(result, dotted)
                if observed != expected:
                    mismatches.append(
                        {"path": dotted, "expected": expected, "observed": observed}
                    )
            ok = not mismatches
            if ok:
                passed += 1
            results.append(
                {
                    "id": case_id,
                    "source_refs": case.get("source_refs", []),
                    "ok": ok,
                    "mismatches": mismatches,
                    "result": result,
                }
            )
        except (EngineError, KeyError) as exc:
            results.append(
                {
                    "id": case_id,
                    "source_refs": case.get("source_refs", []),
                    "ok": False,
                    "mismatches": [{"error": str(exc)}],
                    "result": None,
                }
            )
    return {
        "replay_id": replay_id,
        "status": "passed" if passed == len(results) else "failed",
        "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
        "coverage": replay.get("coverage", {}),
        "cases": results,
    }


def amplify_capability(
    capability_id: str,
    target_tier: int,
    axes: list[str],
    registry: Registry,
    *,
    effect_id: str | None = None,
    expertise: int | float | None = None,
    available_energy: int | float | None = None,
    base_tier: int | None = None,
    channel_intervals: int = 1,
    linked_channel_capacity: int | float | None = None,
    energy_source: str | None = None,
) -> dict[str, Any]:
    """Price brute-force scaling of a known magical pattern without inventing a spell."""

    rule = registry.require("core_bruteforce_amplification", "amplification_scale")
    capability = registry.require(capability_id, "capability")
    effect_ids = list(capability.get("effects", []))
    if effect_id is None:
        if len(effect_ids) != 1:
            raise EngineError("amplification requires --effect when capability has multiple effects")
        effect_id = effect_ids[0]
    if effect_id not in effect_ids:
        raise EngineError(f"{effect_id} is not an effect of {capability_id}")
    effect = registry.require(effect_id, "effect")

    resolved_base_tier = capability.get("pattern_tier") if base_tier is None else base_tier
    if not isinstance(resolved_base_tier, int) or isinstance(resolved_base_tier, bool):
        raise EngineError("amplification needs an integer base pattern tier")
    if not isinstance(target_tier, int) or isinstance(target_tier, bool):
        raise EngineError("target tier must be an integer")
    if not 0 <= resolved_base_tier <= 10 or not resolved_base_tier <= target_tier <= 10:
        raise EngineError("target tier must be between the base tier and 10")

    allowed_axes = set(rule.get("axes", []))
    unique_axes = list(dict.fromkeys(axes or ["intensity"]))
    unknown_axes = [axis for axis in unique_axes if axis not in allowed_axes]
    if unknown_axes:
        raise EngineError(f"unknown amplification axes: {', '.join(unknown_axes)}")

    inferred_values = [
        value for value in capability.get("ratings", {}).values() if isinstance(value, (int, float))
    ]
    if isinstance(effect.get("application_rating"), (int, float)):
        inferred_values.append(effect["application_rating"])
    resolved_expertise = max(inferred_values, default=None) if expertise is None else expertise
    if not isinstance(resolved_expertise, (int, float)) or isinstance(resolved_expertise, bool):
        raise EngineError("amplification needs numeric expertise or inferable ratings")
    if available_energy is not None and (
        not isinstance(available_energy, (int, float))
        or isinstance(available_energy, bool)
        or available_energy < 0
    ):
        raise EngineError("available energy must be a non-negative number")
    if not isinstance(channel_intervals, int) or isinstance(channel_intervals, bool) or channel_intervals < 1:
        raise EngineError("channel intervals must be a positive integer")
    if linked_channel_capacity is not None and (
        not isinstance(linked_channel_capacity, (int, float))
        or isinstance(linked_channel_capacity, bool)
        or linked_channel_capacity <= 0
    ):
        raise EngineError("linked channel capacity must be a positive number")

    tier_rows = {row["tier"]: row for row in rule.get("tiers", [])}
    gap_rows = {row["gap"]: row for row in rule.get("gap_penalties", [])}
    gap = target_tier - resolved_base_tier
    if target_tier not in tier_rows or gap not in gap_rows:
        raise EngineError("amplification scale does not cover the requested tier or gap")
    optimized_cost = tier_rows[target_tier]["optimized_energy_cost"]
    expertise_required = tier_rows[target_tier]["minimum_expertise"]
    gap_multiplier = gap_rows[gap]["multiplier"]
    axis_multiplier = rule["additional_axis_multiplier"] ** max(0, len(unique_axes) - 1)
    required_per_interval = optimized_cost * gap_multiplier * axis_multiplier
    required_energy = required_per_interval * channel_intervals
    if isinstance(required_per_interval, float):
        required_per_interval = round(required_per_interval, 9)
    if isinstance(required_energy, float):
        required_energy = round(required_energy, 9)

    interval_seconds = rule.get("channel_interval_seconds", 6)
    flow_per_second = required_per_interval / interval_seconds
    if isinstance(flow_per_second, float):
        flow_per_second = round(flow_per_second, 9)
    safe_turnovers = rule.get("throughput", {}).get(
        "linked_capacity_safe_turnovers_per_second", 1
    )
    safe_flow_per_second = (
        None if linked_channel_capacity is None else linked_channel_capacity * safe_turnovers
    )
    load_ratio = (
        None
        if safe_flow_per_second is None
        else round(flow_per_second / safe_flow_per_second, 9)
    )
    load_state = "unmeasured"
    if load_ratio is not None:
        for band in rule.get("throughput", {}).get("load_bands", []):
            maximum = band.get("maximum_ratio")
            if maximum is None or load_ratio <= maximum:
                load_state = band["state"]
                break

    resource_costs = list(capability.get("resource_costs", []))
    if effect.get("resource_cost"):
        resource_costs.append(effect["resource_cost"])
    pools = {cost.get("pool") for cost in resource_costs if cost.get("pool")}
    if len(pools) > 1:
        raise EngineError("amplification currently requires a single energy pool")
    resource_pool = next(iter(pools), "unspecified_magical_energy")
    resolved_energy_source = energy_source or resource_pool

    expertise_sufficient = resolved_expertise >= expertise_required
    energy_sufficient = None if available_energy is None else available_energy >= required_energy
    ready = expertise_sufficient and energy_sufficient is True
    verdict = "conditional" if ready else "possible_only_with_new_leverage"
    instability = min(
        100,
        10
        + gap * 10
        + len(unique_axes) * 5
        + max(0, expertise_required - resolved_expertise) * 4,
    )
    risks = ["strong_magical_trace", "interruptible_energy_channel"]
    if len(unique_axes) > 1:
        risks.append("shape_instability")
    if gap >= 2:
        risks.append("channel_damage_or_backlash")
    if load_ratio is not None and load_ratio > 5:
        risks.append("permanent_channel_or_mental_scar")
    if load_ratio is not None and load_ratio > 10:
        risks.append("catastrophic_overload_risk_without_automatic_death")
    if not expertise_sufficient:
        risks.append("expertise_deficit_requires_external_leverage_or_accepting_failure_mode")

    return {
        "capability": capability_id,
        "effect": effect_id,
        "base_tier": resolved_base_tier,
        "target_tier": target_tier,
        "axes": unique_axes,
        "technically_possible": True,
        "special_education_required": False,
        "verdict": verdict,
        "roll_allowed": ready,
        "expertise": {
            "available": resolved_expertise,
            "required": expertise_required,
            "sufficient": expertise_sufficient,
        },
        "energy": {
            "pool": resource_pool,
            "source": resolved_energy_source,
            "draws_from_personal_reserve": resolved_energy_source == resource_pool,
            "available": available_energy,
            "required": required_energy,
            "required_per_interval": required_per_interval,
            "sufficient": energy_sufficient,
            "optimized_equivalent_cost": optimized_cost,
            "gap_multiplier": gap_multiplier,
            "axis_multiplier": axis_multiplier,
            "cost_ratio_to_optimized": required_energy / optimized_cost,
        },
        "channeling": {
            "continuous": channel_intervals > 1,
            "interval_seconds": interval_seconds,
            "intervals": channel_intervals,
            "cost_is_paid_each_interval": True,
            "flow_per_second": flow_per_second,
            "linked_channel_capacity": linked_channel_capacity,
            "safe_flow_per_second": safe_flow_per_second,
            "load_ratio": load_ratio,
            "load_state": load_state,
            "capacity_is_not_energy_source": True,
        },
        "instability": {"rating": instability, "risks": risks},
        "rule_ref": "core_bruteforce_amplification",
    }


def generate_entity(
    object_id: str,
    name: str,
    archetype: str,
    rank: str,
    role: str | None,
    gimmick: str | None,
    weaknesses: list[str],
    registry: Registry,
    extra_layers: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    layer_ids = []
    if role:
        layer_ids.append(f"role_{role}")
    if gimmick:
        layer_ids.append(f"gimmick_{gimmick}")
    layer_ids.extend(extra_layers or [])
    layer_ids.extend(f"weakness_{item}" for item in weaknesses)
    for layer_id in layer_ids:
        registry.require(layer_id, "modifier")
    build = {
        "schema_version": 1,
        "id": object_id,
        "name": name,
        "object_type": "build",
        "status": "proposed",
        "base_ref": archetype,
        "layers": layer_ids,
        "classification": {"operational_rank": rank},
    }
    entity = compile_build(build, registry)
    scale = registry.require("core_capability_scale", "scale")
    band = next((item for item in scale["rank_bands"] if item["id"] == rank), None)
    if band is None:
        raise EngineError(f"unknown rank: {rank}")
    generated_ratings = list(entity.get("ratings", {}).values())
    for capability_id in entity.get("capabilities", []):
        capability = registry.require(capability_id, "capability")
        generated_ratings.extend(capability.get("ratings", {}).values())
        for effect_id in capability.get("effects", []):
            effect = registry.require(effect_id, "effect")
            if isinstance(effect.get("application_rating"), (int, float)):
                generated_ratings.append(effect["application_rating"])
    peak = max(generated_ratings, default=0)
    if peak > band["narrow_signature_max"]:
        raise EngineError(
            f"generated peak {peak} exceeds {rank} narrow cap {band['narrow_signature_max']}"
        )
    required_weaknesses = scale.get("generation_constraints", {}).get(
        "required_meaningful_weaknesses", 0
    )
    if len(weaknesses) < required_weaknesses:
        raise EngineError(
            f"generation requires at least {required_weaknesses} meaningful weaknesses"
        )
    narrow_count = sum(value > band["typical_max"] for value in generated_ratings)
    maximum_narrow = scale.get("generation_constraints", {}).get(
        "maximum_narrow_signatures", 2
    )
    if narrow_count > maximum_narrow:
        raise EngineError(
            f"generated entity has {narrow_count} narrow peaks; maximum is {maximum_narrow}"
        )
    entity["generation"] = {
        "archetype": archetype,
        "role": role,
        "gimmick": gimmick,
        "weaknesses": weaknesses,
        "extra_layers": extra_layers or [],
        "source_refs": source_refs or [],
        "rank_constraints_ref": "core_capability_scale",
    }
    return entity


def dump_yaml(document: dict[str, Any]) -> str:
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False)


def registry_from_args(values: list[str] | None) -> Registry:
    roots = [Path(value) for value in values] if values else list(DEFAULT_DATA_ROOTS)
    return Registry(roots)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GameMaster capability engine")
    parser.add_argument(
        "--data-root", action="append", help="YAML object root; repeat as needed"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compile_command = commands.add_parser("compile", help="Compile a layered build")
    compile_command.add_argument("object_id")
    compile_command.add_argument("--output", type=Path)
    compile_command.add_argument("--force", action="store_true")

    assess_command = commands.add_parser("assess", help="Assess feasibility before d100")
    assess_command.add_argument("--actor", required=True)
    assess_command.add_argument("--capability", required=True)
    assess_command.add_argument("--target", required=True)
    assess_command.add_argument("--intent", required=True)
    assess_command.add_argument("--condition", action="append", default=[])

    validate_command = commands.add_parser("validate", help="Validate engine objects")
    validate_command.add_argument("--json", action="store_true")

    generate_command = commands.add_parser("generate", help="Generate a proposed entity")
    generate_command.add_argument("--id", required=True)
    generate_command.add_argument("--name", required=True)
    generate_command.add_argument("--archetype", required=True)
    generate_command.add_argument("--rank", required=True)
    generate_command.add_argument("--role")
    generate_command.add_argument("--gimmick")
    generate_command.add_argument("--weakness", action="append", default=[])
    generate_command.add_argument("--layer", action="append", default=[])
    generate_command.add_argument("--source-ref", action="append", default=[])
    generate_command.add_argument("--output", type=Path)
    generate_command.add_argument("--force", action="store_true")

    replay_command = commands.add_parser("replay", help="Run source-linked regression cases")
    replay_command.add_argument("replay_id")
    replay_command.add_argument("--details", action="store_true")

    amplify_command = commands.add_parser(
        "amplify", help="Price brute-force scaling of a known magical pattern"
    )
    amplify_command.add_argument("--capability", required=True)
    amplify_command.add_argument("--effect")
    amplify_command.add_argument("--target-tier", type=int, required=True)
    amplify_command.add_argument("--base-tier", type=int)
    amplify_command.add_argument("--axis", action="append", default=[])
    amplify_command.add_argument("--expertise", type=float)
    amplify_command.add_argument("--available-energy", type=float)
    amplify_command.add_argument("--channel-intervals", type=int, default=1)
    amplify_command.add_argument("--linked-channel-capacity", type=float)
    amplify_command.add_argument("--energy-source")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry = registry_from_args(args.data_root)
        if args.command == "compile":
            result = compile_entity(args.object_id, registry)
            rendered = dump_yaml(result)
            if args.output:
                if args.output.exists() and not args.force:
                    raise EngineError(
                        f"output already exists: {args.output}; use --force to replace it"
                    )
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                print(rendered, end="")
        elif args.command == "assess":
            result = assess(
                args.actor,
                args.capability,
                args.target,
                args.intent,
                args.condition,
                registry,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "validate":
            errors = validate_registry(registry)
            if args.json:
                print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
            elif errors:
                print("GameMaster mechanics validation FAILED")
                for error in errors:
                    print(f"- {error}")
            else:
                print(f"GameMaster mechanics validation OK ({len(registry.objects)} objects)")
            return 1 if errors else 0
        elif args.command == "generate":
            result = generate_entity(
                args.id,
                args.name,
                args.archetype,
                args.rank,
                args.role,
                args.gimmick,
                args.weakness,
                registry,
                args.layer,
                args.source_ref,
            )
            rendered = dump_yaml(result)
            if args.output:
                if args.output.exists() and not args.force:
                    raise EngineError(
                        f"output already exists: {args.output}; use --force to replace it"
                    )
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                print(rendered, end="")
        elif args.command == "replay":
            result = run_replay(args.replay_id, registry)
            if not args.details:
                result = {
                    "replay_id": result["replay_id"],
                    "status": result["status"],
                    "summary": result["summary"],
                    "coverage": result["coverage"],
                    "failed_cases": [
                        {"id": item["id"], "mismatches": item["mismatches"]}
                        for item in result["cases"]
                        if not item["ok"]
                    ],
                }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "passed" else 1
        elif args.command == "amplify":
            result = amplify_capability(
                args.capability,
                args.target_tier,
                args.axis,
                registry,
                effect_id=args.effect,
                expertise=args.expertise,
                available_energy=args.available_energy,
                base_tier=args.base_tier,
                channel_intervals=args.channel_intervals,
                linked_channel_capacity=args.linked_channel_capacity,
                energy_source=args.energy_source,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except EngineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
