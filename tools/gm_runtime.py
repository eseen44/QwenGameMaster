"""Transactional campaign runtime for GameMaster.

The mechanics engine establishes what is possible.  This module owns mutable
campaign instances, immutable turn records, time, clocks and compact context.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

import gm_engine
from roll_d100 import character_modifier


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CAMPAIGN_ROOT = ROOT / "campaigns" / "lucan"
CONTEXT_BUDGET_BYTES = 40 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
CRISIS_SURFER_TAGS = {
    "time_pressure",
    "multiple_simultaneous_failures",
    "environmental_chaos",
    "others_panicking",
    "resource_triage",
    "rapidly_changing_situation",
}


class _StringDatesLoader(yaml.SafeLoader):
    """SafeLoader that never auto-converts ISO-looking scalars to datetime/date.

    PyYAML's implicit timestamp resolver silently turns any unquoted
    ISO 8601-looking string (current_datetime, created_at, ...) into a
    datetime object on load.  Every campaign document is later re-hashed
    with json.dumps, which cannot serialize datetime — so a value that
    round-trips through dump_yaml -> load_yaml once crashes the very next
    commit that touches it.  All campaign timestamps are plain strings by
    convention; keep them that way through the loader instead of relying on
    every call site to re-stringify.
    """


_StringDatesLoader.yaml_implicit_resolvers = {
    key: [item for item in resolvers if item[0] != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
ARRANGEMENTS = {"improved", "worsened", "complicated", "mixed", "unchanged"}
TIME_SECONDS = {
    0: {"instant": 0, "brief": 300, "significant": 3600},
    1: {"instant": 0, "brief": 120, "significant": 600},
    2: {"instant": 0, "brief": 30, "significant": 120},
    3: {"instant": 0, "brief": 6, "significant": 30},
}


class RuntimeError(ValueError):
    """Readable state or transaction error."""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def stable_number(value: int | float) -> int | float:
    """Keep fractional campaign resources readable after repeated decimal costs."""
    if isinstance(value, float):
        value = round(value, 9)
        if value == 0:
            return 0
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=_StringDatesLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: YAML root must be a mapping")
    return value


def load_optional_yaml(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    return load_yaml(path) if path.exists() else copy.deepcopy(default)


def dump_yaml(document: dict[str, Any]) -> str:
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    atomic_text(path, dump_yaml(document))


def document_hash(document: dict[str, Any]) -> str:
    rendered = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def file_document_hash(path: Path) -> str | None:
    return document_hash(load_yaml(path)) if path.exists() else None


def require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise RuntimeError(f"{label} must use only letters, digits, dot, dash or underscore")
    return value


def campaign_is_active(campaign_root: Path) -> bool:
    campaign = load_yaml(campaign_root / "campaign.yaml")
    return campaign.get("status") == "active"


def require_writable_campaign(campaign_root: Path, allow_noncanonical: bool) -> None:
    if not campaign_is_active(campaign_root) and not allow_noncanonical:
        raise RuntimeError(
            "campaign is not active; use --allow-noncanonical only for migration rehearsal"
        )


def instance_index_path(campaign_root: Path) -> Path:
    return campaign_root / "state" / "instances" / "index.yaml"


def load_instance_index(campaign_root: Path) -> dict[str, Any]:
    return load_optional_yaml(
        instance_index_path(campaign_root),
        {"schema_version": 1, "campaign_id": "campaign_lucan", "status": "needs_review", "instances": []},
    )


def resolve_campaign_ref(campaign_root: Path, ref: str) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    if ref.replace("\\", "/").startswith("campaigns/"):
        return ROOT / path
    return campaign_root / path


def project_ref(path: Path) -> str:
    """Return a portable repository-relative ref when the path belongs to the repo."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def find_instance_path(campaign_root: Path, instance_id: str) -> Path | None:
    for entry in load_instance_index(campaign_root).get("instances", []):
        if isinstance(entry, dict) and entry.get("id") == instance_id:
            ref = entry.get("ref")
            if not isinstance(ref, str):
                raise RuntimeError(f"instance index entry {instance_id} has no ref")
            return resolve_campaign_ref(campaign_root, ref)
    return None


def find_named_entity_path(campaign_root: Path, entity_id: str) -> Path | None:
    """Resolve an NPC or fixture card independently from runtime instances."""
    index = load_optional_yaml(campaign_root / "entities" / "npcs" / "index.yaml", {})
    for collection in ("entities", "fixtures"):
        for entry in index.get(collection, []):
            if isinstance(entry, dict) and entry.get("id") == entity_id:
                ref = entry.get("ref")
                if not isinstance(ref, str):
                    raise RuntimeError(f"named entity index entry {entity_id} has no ref")
                return resolve_campaign_ref(campaign_root, ref)
    return None


def load_instance(campaign_root: Path, instance_id: str) -> tuple[Path, dict[str, Any]]:
    path = find_instance_path(campaign_root, instance_id)
    if path is None or not path.exists():
        raise RuntimeError(f"unknown campaign instance: {instance_id}")
    instance = load_yaml(path)
    if instance.get("id") != instance_id or instance.get("object_type") != "entity_instance":
        raise RuntimeError(f"invalid instance file for {instance_id}")
    return path, instance


def runtime_registry() -> gm_engine.Registry:
    return gm_engine.Registry(gm_engine.DEFAULT_DATA_ROOTS)


def compile_runtime_entity(
    campaign_root: Path, entity_id: str, registry: gm_engine.Registry
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    path = find_instance_path(campaign_root, entity_id)
    if path is None:
        return gm_engine.compile_entity(entity_id, registry), None
    instance = load_yaml(path)
    definition_ref = instance.get("definition_ref")
    if not isinstance(definition_ref, str):
        raise RuntimeError(f"instance {entity_id} requires definition_ref")
    entity = gm_engine.compile_entity(definition_ref, registry)
    for key in (
        "ratings", "defenses", "resistances", "resources", "traits", "capabilities",
        "anatomy", "thresholds", "integrity", "position",
    ):
        if key in instance:
            entity[key] = copy.deepcopy(instance[key])
    entity["id"] = entity_id
    entity["runtime_revision"] = instance.get("revision")
    return entity, instance


def scene_document(campaign_root: Path) -> dict[str, Any]:
    return load_yaml(campaign_root / "context" / "scene.yaml")


def action_seconds(request: dict[str, Any], scene: dict[str, Any]) -> int:
    if "time_seconds" in request:
        seconds = request["time_seconds"]
        if not isinstance(seconds, int) or seconds < 0:
            raise RuntimeError("time_seconds must be a non-negative integer")
        return seconds
    time_class = request.get("time_class", "brief")
    if time_class == "extended":
        raise RuntimeError("extended actions require explicit time_seconds")
    tension = scene.get("tension", {}).get("level", 0)
    if tension not in TIME_SECONDS or time_class not in TIME_SECONDS[tension]:
        raise RuntimeError(f"unsupported time class {time_class!r} at tension {tension}")
    return TIME_SECONDS[tension][time_class]


def system_only_message(text: str) -> bool:
    stripped = text.strip()
    if not (stripped.startswith("(") and stripped.endswith(")")):
        return False
    depth = 0
    for index, character in enumerate(stripped):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0 and index != len(stripped) - 1:
                return False
        if depth < 0:
            return False
    return depth == 0


def crisis_surfer_modifiers(actor: dict[str, Any], request: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply Lucan's learned response to generic stress and exploitable chaos."""
    if "crisis_surfer" not in actor.get("traits", []):
        return []
    situation_tags = request.get("situation_tags", [])
    if not isinstance(situation_tags, list) or any(not isinstance(tag, str) for tag in situation_tags):
        raise RuntimeError("situation_tags must be a list of strings")
    exploitable = request.get("crisis_exploitable", False)
    if not isinstance(exploitable, bool):
        raise RuntimeError("crisis_exploitable must be boolean")
    modifiers = request.get("modifiers", [])
    if not isinstance(modifiers, list):
        raise RuntimeError("modifiers must be a list")
    generic_stress_penalty = sum(
        int(item.get("value", 0))
        for item in modifiers
        if isinstance(item, dict)
        and item.get("category") == "stress"
        and isinstance(item.get("value"), int)
        and item["value"] < 0
    )
    result: list[dict[str, Any]] = []
    if generic_stress_penalty:
        result.append(
            {
                "source": "perk_crisis_surfer_ignore_generic_stress",
                "value": -generic_stress_penalty,
            }
        )
    crisis_signals = sorted(set(situation_tags) & CRISIS_SURFER_TAGS)
    if exploitable and len(crisis_signals) >= 2:
        result.append(
            {
                "source": "perk_crisis_surfer_exploits_active_chaos",
                "value": 10,
                "situation_tags": crisis_signals,
            }
        )
    return result


def preview_turn(campaign_root: Path, request: dict[str, Any]) -> dict[str, Any]:
    turn_id = require_id(request.get("turn_id"), "turn_id")
    declaration = request.get("declared_action")
    if not isinstance(declaration, str) or not declaration.strip():
        raise RuntimeError("declared_action is required")
    scene = scene_document(campaign_root)
    parenthetical = system_only_message(declaration)
    parenthetical_action = request.get("parenthetical_action", False)
    if not isinstance(parenthetical_action, bool):
        raise RuntimeError("parenthetical_action must be boolean")
    if parenthetical_action and not parenthetical:
        raise RuntimeError("parenthetical_action requires a fully parenthetical declaration")
    if parenthetical and not parenthetical_action:
        return {
            "turn_id": turn_id,
            "status": "system_only_noop",
            "time_seconds": 0,
            "roll_allowed": False,
            "state_changes_allowed": False,
            "reason": "Parenthetical system contact or thought stops the scene unless marked as an instant internal action.",
        }

    required = ("actor_id", "capability_id", "target_id", "intent_id")
    # An automatic turn still needs an actor in the event journal.  ``actor_id``
    # alone must therefore not opt into the capability engine; only a requested
    # capability, target or mechanical intent does.  Previously the two concerns
    # were coupled, so narration-only turns either lost their actor or failed as
    # malformed mechanical requests.
    mechanical_fields = ("capability_id", "target_id", "intent_id")
    has_mechanics = any(request.get(field) is not None for field in mechanical_fields)
    if has_mechanics and not all(isinstance(request.get(field), str) for field in required):
        raise RuntimeError("mechanical turns require actor_id, capability_id, target_id and intent_id")
    assessment: dict[str, Any]
    automatic_roll_modifiers: list[dict[str, Any]] = []
    if has_mechanics:
        registry = runtime_registry()
        actor, actor_instance = compile_runtime_entity(campaign_root, request["actor_id"], registry)
        automatic_roll_modifiers = crisis_surfer_modifiers(actor, request)
        target, target_instance = compile_runtime_entity(campaign_root, request["target_id"], registry)
        persistent_condition_ids: list[str] = []
        for instance in (actor_instance, target_instance):
            if not instance:
                continue
            for condition in instance.get("conditions", []):
                if not isinstance(condition, dict) or not isinstance(condition.get("mechanics_ref"), str):
                    continue
                persistent_condition_ids.extend(
                    [condition["mechanics_ref"]] * max(1, int(condition.get("stacks", 1)))
                )
        condition_ids = persistent_condition_ids + list(request.get("condition_ids", []))
        assessment = gm_engine.assess_entities(
            actor,
            request["capability_id"],
            target,
            request["intent_id"],
            condition_ids,
            registry,
            actor_label=request["actor_id"],
            target_label=request["target_id"],
        )
    else:
        assessment = {
            "verdict": request.get("fiction_verdict", "automatic"),
            "roll_allowed": False,
            "test_guidance": {"scope": None, "suggested_difficulty": None},
            "resource_costs": [],
            "rule": "Obvious fictional result; no mechanical roll.",
        }
    tension = scene.get("tension", {}).get("level", 0)
    time_state = load_optional_yaml(campaign_root / "state" / "time.yaml", {})
    roll_policy = time_state.get("roll_policy", {})
    rolls_disabled = isinstance(roll_policy, dict) and roll_policy.get("mode") == "disabled"
    # An explicit campaign-phase lock overrides local tension. This is used for
    # Lucan's interlude: capability limits, costs and missing leverage remain
    # real, but uncertainty is resolved by method and time rather than dice.
    # Tension zero retains the same no-roll behavior for ordinary downtime even
    # in campaigns without an explicit phase lock.
    if (rolls_disabled or tension == 0) and assessment.get("verdict") not in {
        "impossible",
        "possible_only_with_new_leverage",
    }:
        costs = assessment.get("resource_costs", [])
        assessment["verdict"] = "automatic_with_cost" if costs else "automatic"
        assessment["roll_allowed"] = False
        assessment["rule"] = (
            "Campaign phase disables rolls; resolve viable actions from capability, method, time and certain costs."
            if rolls_disabled
            else "Tension-zero scene: a viable action resolves without a roll."
        )
    seconds = 0 if parenthetical_action else action_seconds(request, scene)
    due = list(scene.get("pending_world_reactions", []))
    return {
        "turn_id": turn_id,
        "status": "preview",
        "scene_id": scene.get("scene_id"),
        "tension_level": tension,
        "roll_policy_mode": roll_policy.get("mode") if isinstance(roll_policy, dict) else None,
        "declaration": declaration,
        "parenthetical_action": parenthetical_action,
        "assessment": assessment,
        "roll_allowed": assessment.get("roll_allowed", False),
        "time_seconds": seconds,
        "world_reactions_due_before": due,
        "required_resource_costs": assessment.get("resource_costs", []),
        "automatic_roll_modifiers": automatic_roll_modifiers,
    }


def journal_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path}:{number}: {exc}") from exc
        if isinstance(record, dict) and isinstance(record.get("id"), str):
            result.add(record["id"])
    return result


def journal_record(path: Path, record_id: str) -> dict[str, Any] | None:
    """Return an already journalled record so a retry can never restate it."""
    if not path.exists():
        return None
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path}:{number}: {exc}") from exc
        if isinstance(record, dict) and record.get("id") == record_id:
            return record
    return None


def append_jsonl_once(path: Path, record: dict[str, Any]) -> None:
    if record["id"] in journal_ids(path):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def build_roll(
    preview: dict[str, Any], request: dict[str, Any], roll_id: str, event_id: str
) -> dict[str, Any] | None:
    assessment = preview["assessment"]
    if not assessment.get("roll_allowed"):
        return None
    difficulty = request.get("difficulty")
    if difficulty is None:
        difficulty = assessment.get("test_guidance", {}).get("suggested_difficulty")
    if difficulty is None:
        return None
    if not isinstance(difficulty, int) or not 1 <= difficulty <= 100:
        raise RuntimeError("difficulty must be an integer within 1..100")
    modifiers = copy.deepcopy(request.get("modifiers", []))
    if not isinstance(modifiers, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("source"), str)
        or not isinstance(item.get("value"), int)
        for item in modifiers
    ):
        raise RuntimeError("modifiers must contain source/value mappings")
    modifiers.extend(copy.deepcopy(preview.get("automatic_roll_modifiers", [])))
    score = request.get("character_score")
    if score is not None:
        if not isinstance(score, int) or not 0 <= score <= 10:
            raise RuntimeError("character_score must be within 0..10")
        modifiers.append({"source": "in_character_score", "value": character_modifier(score)})
    natural = secrets.randbelow(100) + 1
    modified = natural + sum(item["value"] for item in modifiers)
    return {
        "id": roll_id,
        "timestamp": now_iso(),
        "scene_id": preview.get("scene_id"),
        "subject": request.get("subject_id", request.get("actor_id")),
        "intent": request.get("stakes", request["declared_action"]),
        "scope": request.get("scope", assessment.get("test_guidance", {}).get("scope") or "execution"),
        "stakes": request.get("stakes", "Zmiana sytuacji zgodna z deklaracją tury."),
        "difficulty": difficulty,
        "natural_roll": natural,
        "character_score": score,
        "modifiers": modifiers,
        "modified_result": modified,
        "passes_threshold": modified >= difficulty,
        "critical": "critical_low" if natural == 1 else "critical_high" if natural == 100 else None,
        "interpretation": None,
        "event_id": event_id,
    }


def transaction_path(campaign_root: Path, turn_id: str) -> Path:
    return campaign_root / "journal" / "transactions" / f"{turn_id}.yaml"


def required_cost_operations(request: dict[str, Any], preview: dict[str, Any]) -> list[dict[str, Any]]:
    actor_id = request.get("actor_id")
    if not actor_id:
        return []
    return [
        {"op": "consume", "instance_id": actor_id, "pool": cost["pool"], "units": cost["units"]}
        for cost in preview.get("required_resource_costs", [])
        if isinstance(cost, dict) and cost.get("pool") and isinstance(cost.get("units"), (int, float))
    ]


def resolve_turn(
    campaign_root: Path, request: dict[str, Any], allow_noncanonical: bool
) -> dict[str, Any]:
    require_writable_campaign(campaign_root, allow_noncanonical)
    preview = preview_turn(campaign_root, request)
    if preview["status"] == "system_only_noop":
        return preview
    turn_id = preview["turn_id"]
    path = transaction_path(campaign_root, turn_id)
    if path.exists():
        raise RuntimeError(f"turn already exists: {turn_id}")
    event_id = f"event_{turn_id}"
    roll_id = f"roll_{turn_id}"
    rolls_path = campaign_root / "journal" / "rolls.jsonl"
    # A crash between the journal append and the transaction write used to make a
    # retry restate the roll: the journal kept the first result while the narrator
    # was handed a freshly drawn one.  A journalled roll always wins.
    roll = journal_record(rolls_path, roll_id)
    if roll is None:
        roll = build_roll(preview, request, roll_id, event_id)
        if roll:
            append_jsonl_once(rolls_path, roll)
    transaction = {
        "schema_version": 1,
        "id": turn_id,
        "object_type": "turn_transaction",
        "status": "resolved",
        "created_at": now_iso(),
        "scene_id": preview.get("scene_id"),
        "event_id": event_id,
        "roll_id": roll_id if roll else None,
        "request": request,
        "preview": preview,
        "roll": roll,
        "required_operations": required_cost_operations(request, preview),
        "time_operation": {"op": "advance_time", "seconds": preview["time_seconds"]},
        "outcome": None,
        "prepared_writes": [],
    }
    atomic_yaml(path, transaction)
    return transaction


def instance_requirements_met(instance: dict[str, Any], requirements: Iterable[str]) -> bool:
    flags = set(instance.get("status_flags", [])) | set(instance.get("traits", []))
    return all(requirement in flags for requirement in requirements)


def process_instance_time(instance: dict[str, Any], seconds: int) -> None:
    for pool in instance.get("resources", {}).values():
        if not isinstance(pool, dict):
            continue
        runtime = pool.setdefault("runtime", {})
        for field, direction in (("regeneration", 1), ("decay", -1), ("hunting_recovery", 1)):
            rule = pool.get(field)
            if not isinstance(rule, dict):
                continue
            if not instance_requirements_met(instance, rule.get("requires", [])):
                continue
            # FLAGA decay_suppressed FAKTYCZNIE TLUMI UBYTEK (etap 10).
            # Do 2026-09-04 byla dekoracja: companion_spidey mial ja w status_flags ORAZ
            # regule decay bez zadnego `requires`, wiec silnik ubywal mu rezerwy tak samo
            # jak wszystkim. To najgrozniejsza klasa bledu z audytu, bo klamie W STRONE
            # BEZPIECZENSTWA - autor napisal "ubytek wylaczony", odczytal to z pliku
            # i uwierzyl. Zmierzone skutki tej rozbieznosci: spy_wasp_01 0/3,
            # spy_cellar_spider_01 0/3, spy_hawk_moth_01 2/3 przy kanonie mowiacym
            # o najszybciej rosnacym wezle sieci.
            if field == "decay" and (
                "decay_suppressed" in set(instance.get("status_flags") or [])
                or pool.get("decay_suppressed") is True
            ):
                continue
            interval = rule.get("interval_seconds")
            units = rule.get("units")
            if not isinstance(interval, int) or interval <= 0 or not isinstance(units, (int, float)):
                continue
            elapsed_key = f"{field}_elapsed_seconds"
            elapsed = int(runtime.get(elapsed_key, 0)) + seconds
            ticks, runtime[elapsed_key] = divmod(elapsed, interval)
            if ticks:
                current = pool.get("current", 0) + direction * ticks * units
                pool["current"] = max(0, min(pool.get("capacity", current), current))
    retained: list[dict[str, Any]] = []
    for condition in instance.get("conditions", []):
        if not isinstance(condition, dict):
            continue
        condition = copy.deepcopy(condition)
        if isinstance(condition.get("expiry_remaining_seconds"), int):
            condition["expiry_remaining_seconds"] -= seconds
            if condition["expiry_remaining_seconds"] <= 0:
                continue
        interval = condition.get("interval_seconds")
        if isinstance(interval, int) and interval > 0:
            elapsed = int(condition.get("elapsed_seconds", 0)) + seconds
            ticks, condition["elapsed_seconds"] = divmod(elapsed, interval)
            if ticks and isinstance(condition.get("magnitude_per_interval"), (int, float)):
                maximum = condition.get("maximum_magnitude", 100)
                condition["magnitude"] = min(
                    maximum,
                    condition.get("magnitude", 0) + ticks * condition["magnitude_per_interval"],
                )
        retained.append(condition)
    instance["conditions"] = retained


def process_sustained_links(
    campaign_root: Path, changed: dict[Path, dict[str, Any]], seconds: int, event_id: str
) -> None:
    """Advance explicit, voluntary resource links between active instances.

    Links are opt-in campaign state, not an inferred side effect of a control bond.
    A depleted source simply misses that interval; it never creates a negative pool.
    """
    path = campaign_root / "state" / "sustained-links.yaml"
    if not path.exists():
        return
    document = load_mutable(campaign_root, changed, path)
    for link in document.get("links", []):
        if not isinstance(link, dict) or not link.get("active", False):
            continue
        interval = link.get("interval_seconds")
        source_units = link.get("source_units_per_interval")
        target_units = link.get("target_units_per_interval")
        if not isinstance(interval, int) or interval <= 0:
            continue
        if not isinstance(source_units, (int, float)) or source_units <= 0:
            continue
        if not isinstance(target_units, (int, float)) or target_units < 0:
            continue
        runtime = link.setdefault("runtime", {})
        elapsed = int(runtime.get("elapsed_seconds", 0)) + seconds
        ticks, runtime["elapsed_seconds"] = divmod(elapsed, interval)
        if not ticks:
            continue
        source_path = find_instance_path(campaign_root, link.get("source_instance_id"))
        target_path = find_instance_path(campaign_root, link.get("target_instance_id"))
        if source_path is None or target_path is None:
            link["last_error"] = "missing_source_or_target_instance"
            continue
        source = load_mutable(campaign_root, changed, source_path)
        target = load_mutable(campaign_root, changed, target_path)
        source_pool = source.get("resources", {}).get(link.get("source_pool_id"))
        target_pool = target.get("resources", {}).get(link.get("target_pool_id"))
        if not isinstance(source_pool, dict) or not isinstance(target_pool, dict):
            link["last_error"] = "missing_source_or_target_pool"
            continue
        affordable_ticks = min(ticks, int((source_pool.get("current", 0) + 1e-9) // source_units))
        free_capacity = max(0, target_pool.get("capacity", 0) - target_pool.get("current", 0))
        capacity_ticks = ticks if target_units == 0 else int((free_capacity + 1e-9) // target_units)
        applied_ticks = max(0, min(affordable_ticks, capacity_ticks))
        if applied_ticks:
            source_pool["current"] = stable_number(source_pool["current"] - source_units * applied_ticks)
            target_pool["current"] = stable_number(min(target_pool["capacity"], target_pool["current"] + target_units * applied_ticks))
            integrity_units = link.get("target_integrity_per_interval", 0)
            if isinstance(integrity_units, (int, float)) and integrity_units > 0:
                integrity = target.get("integrity")
                if isinstance(integrity, dict) and isinstance(integrity.get("current"), (int, float)) and isinstance(integrity.get("maximum"), (int, float)):
                    integrity["current"] = stable_number(min(integrity["maximum"], integrity["current"] + integrity_units * applied_ticks))
            for entity in (source, target):
                if entity.get("last_event_id") != event_id:
                    entity["revision"] = int(entity.get("revision", 0)) + 1
                entity["last_event_id"] = event_id
        runtime["successful_intervals"] = int(runtime.get("successful_intervals", 0)) + applied_ticks
        runtime["missed_intervals"] = int(runtime.get("missed_intervals", 0)) + (ticks - applied_ticks)
        link["last_event_id"] = event_id


def relative_to_campaign(campaign_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(campaign_root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"transaction write escapes campaign root: {path}") from exc


def load_mutable(
    campaign_root: Path, changed: dict[Path, dict[str, Any]], path: Path
) -> dict[str, Any]:
    path = path.resolve()
    if path not in changed:
        changed[path] = load_yaml(path)
    return changed[path]


def entity_for_operation(
    campaign_root: Path, changed: dict[Path, dict[str, Any]], operation: dict[str, Any]
) -> tuple[Path, dict[str, Any]]:
    instance_id = require_id(operation.get("instance_id"), "instance_id")
    path = find_instance_path(campaign_root, instance_id)
    if path is None:
        raise RuntimeError(f"operation references unknown instance {instance_id}")
    return path, load_mutable(campaign_root, changed, path)


def apply_operation(
    campaign_root: Path,
    changed: dict[Path, dict[str, Any]],
    operation: dict[str, Any],
    event_id: str,
) -> None:
    op = operation.get("op")
    if op in {"set", "adjust", "consume", "restore", "add_condition", "remove_condition"}:
        _, entity = entity_for_operation(campaign_root, changed, operation)
        expected = operation.get("expected_revision")
        if expected is not None and entity.get("revision") != expected:
            raise RuntimeError(
                f"stale revision for {entity['id']}: expected {expected}, found {entity.get('revision')}"
            )
        if op == "set":
            gm_engine.set_path(entity, operation["path"], copy.deepcopy(operation.get("value")))
        elif op == "adjust":
            gm_engine.adjust_path(entity, operation["path"], operation["delta"])
        elif op in {"consume", "restore"}:
            pool_id = operation.get("pool")
            pool = entity.get("resources", {}).get(pool_id)
            if not isinstance(pool, dict):
                raise RuntimeError(f"{entity['id']} has no resource pool {pool_id}")
            units = operation.get("units")
            if not isinstance(units, (int, float)) or units < 0:
                raise RuntimeError("resource units must be non-negative")
            current = pool.get("current")
            capacity = pool.get("capacity")
            if not isinstance(current, (int, float)) or not isinstance(capacity, (int, float)):
                raise RuntimeError(f"invalid resource pool {pool_id}")
            result = stable_number(current - units if op == "consume" else current + units)
            if result < 0:
                raise RuntimeError(f"insufficient {pool_id}: {current} < {units}")
            pool["current"] = min(capacity, result)
        elif op == "add_condition":
            condition = copy.deepcopy(operation.get("condition"))
            if not isinstance(condition, dict) or not isinstance(condition.get("id"), str):
                raise RuntimeError("add_condition requires a condition with id")
            conditions = entity.setdefault("conditions", [])
            existing = next((item for item in conditions if item.get("id") == condition["id"]), None)
            if existing:
                maximum = condition.get("maximum_stacks", existing.get("maximum_stacks", 1))
                existing["stacks"] = min(maximum, existing.get("stacks", 1) + condition.get("stacks", 1))
                existing["magnitude"] = min(
                    condition.get("maximum_magnitude", existing.get("maximum_magnitude", 100)),
                    existing.get("magnitude", 0) + condition.get("magnitude", 0),
                )
                existing["source_event_id"] = event_id
            else:
                condition.setdefault("stacks", 1)
                condition.setdefault("magnitude", 0)
                condition.setdefault("elapsed_seconds", 0)
                condition["source_event_id"] = event_id
                conditions.append(condition)
        elif op == "remove_condition":
            condition_id = operation.get("condition_id")
            entity["conditions"] = [
                item for item in entity.get("conditions", []) if item.get("id") != condition_id
            ]
        if entity.get("last_event_id") != event_id:
            entity["revision"] = int(entity.get("revision", 0)) + 1
        entity["last_event_id"] = event_id
        return

    if op == "advance_time":
        seconds = operation.get("seconds", 0)
        if not isinstance(seconds, int) or seconds < 0:
            raise RuntimeError("advance_time seconds must be a non-negative integer")
        if seconds == 0:
            return
        time_path = campaign_root / "state" / "time.yaml"
        time_doc = load_mutable(campaign_root, changed, time_path)
        time_doc["elapsed_seconds_total"] = int(time_doc.get("elapsed_seconds_total", 0)) + seconds
        current = time_doc.get("current_datetime")
        if isinstance(current, str):
            try:
                time_doc["current_datetime"] = (datetime.fromisoformat(current) + timedelta(seconds=seconds)).isoformat()
            except ValueError as exc:
                raise RuntimeError(f"invalid campaign current_datetime: {current}") from exc
        time_doc["elapsed_since_last_event"] = seconds
        time_doc["last_event_id"] = event_id
        for entry in load_instance_index(campaign_root).get("instances", []):
            if not isinstance(entry, dict) or entry.get("state") == "dead":
                continue
            ref = entry.get("ref")
            if not isinstance(ref, str):
                continue
            path = resolve_campaign_ref(campaign_root, ref)
            instance = load_mutable(campaign_root, changed, path)
            process_instance_time(instance, seconds)
            if instance.get("last_event_id") != event_id:
                instance["revision"] = int(instance.get("revision", 0)) + 1
            instance["last_event_id"] = event_id
        process_sustained_links(campaign_root, changed, seconds, event_id)
        advance_clocks_for_time(campaign_root, changed, seconds, event_id)
        return

    if op == "advance_clock":
        clocks_path = campaign_root / "state" / "clocks.yaml"
        clocks_doc = load_mutable(campaign_root, changed, clocks_path)
        clock = next((item for item in clocks_doc.get("clocks", []) if item.get("id") == operation.get("clock_id")), None)
        if clock is None:
            raise RuntimeError(f"unknown clock {operation.get('clock_id')}")
        clock["progress"] = min(clock["threshold"], clock.get("progress", 0) + operation.get("amount", 1))
        queue_clock_reaction(campaign_root, changed, clock, event_id)
        return

    if op == "transfer_item":
        resources_path = campaign_root / "state" / "resources.yaml"
        resources = load_mutable(campaign_root, changed, resources_path)
        resources.setdefault("transactions", []).append(
            {
                "id": f"transaction_{event_id}_{len(resources.get('transactions', [])) + 1}",
                "item_id": operation.get("item_id"),
                "quantity": operation.get("quantity", 1),
                "from_owner": operation.get("from_owner"),
                "to_owner": operation.get("to_owner"),
                "reason": operation.get("reason"),
                "event_id": event_id,
            }
        )
        for asset in resources.setdefault("shared_resources", []):
            if isinstance(asset, dict) and asset.get("id") == operation.get("item_id"):
                asset["owner_id"] = operation.get("to_owner")
                break
        return

    if op == "change_relationship":
        # npc_id jest skrotem uzywanym w praktyce ("nastawienie tego NPC do Lucana").
        # Do 2026-09-04 handler czytal wylacznie subject_id/target_id, wiec tura 083
        # zapisala npc_id: npc_hesk_dorn, a do pliku wpadl rekord NIKT WOBEC NIKOGO
        # ze score 25 i reason null - nazwisko zniknelo bez sladu i bez bledu.
        subject_id = operation.get("subject_id") or operation.get("npc_id")
        target_id = operation.get("target_id") or ("pc_lucan" if operation.get("npc_id") else None)
        if not subject_id or not target_id:
            raise RuntimeError(
                "change_relationship wymaga subject_id i target_id albo skrotu npc_id; "
                f"otrzymano {sorted(k for k in operation if k != 'op')}"
            )
        reputations_path = campaign_root / "state" / "reputations.yaml"
        reputations = load_mutable(campaign_root, changed, reputations_path)
        attitudes = reputations.setdefault("attitudes", [])
        relation = next(
            (
                item for item in attitudes
                if item.get("subject_id") == subject_id
                and item.get("target_id") == target_id
            ),
            None,
        )
        if relation is None:
            relation = {
                "subject_id": subject_id,
                "target_id": target_id,
                "score": 0,
                "history": [],
            }
            attitudes.append(relation)
        relation["score"] = max(-100, min(100, relation.get("score", 0) + operation.get("delta", 0)))
        relation.setdefault("history", []).append(
            {"delta": operation.get("delta", 0), "reason": operation.get("reason"), "event_id": event_id}
        )
        return
    raise RuntimeError(f"unsupported operation: {op}")


def queue_clock_reaction(
    campaign_root: Path,
    changed: dict[Path, dict[str, Any]],
    clock: dict[str, Any],
    event_id: str,
) -> None:
    if clock.get("triggered") or clock.get("progress", 0) < clock.get("threshold", 0):
        return
    clock["triggered"] = True
    scene_path = campaign_root / "context" / "scene.yaml"
    scene = load_mutable(campaign_root, changed, scene_path)
    reaction_id = f"reaction_{clock['id']}_{clock['threshold']}"
    if not any(item.get("id") == reaction_id for item in scene.setdefault("pending_world_reactions", [])):
        scene["pending_world_reactions"].append(
            {
                "id": reaction_id,
                "clock_id": clock["id"],
                "effect": clock.get("effect"),
                "world_test_required": bool(clock.get("world_test_required")),
                "trigger_event_id": event_id,
            }
        )


def advance_clocks_for_time(
    campaign_root: Path,
    changed: dict[Path, dict[str, Any]],
    seconds: int,
    event_id: str,
) -> None:
    clocks_path = campaign_root / "state" / "clocks.yaml"
    clocks_doc = load_mutable(campaign_root, changed, clocks_path)
    for clock in clocks_doc.get("clocks", []):
        interval = clock.get("seconds_per_step")
        if clock.get("triggered") or not isinstance(interval, int) or interval <= 0:
            continue
        elapsed = int(clock.get("elapsed_seconds", 0)) + seconds
        steps, clock["elapsed_seconds"] = divmod(elapsed, interval)
        if steps:
            clock["progress"] = min(clock["threshold"], clock.get("progress", 0) + steps)
            queue_clock_reaction(campaign_root, changed, clock, event_id)


def prepare_writes(
    campaign_root: Path, changed: dict[Path, dict[str, Any]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path, document in sorted(changed.items(), key=lambda item: str(item[0])):
        result.append(
            {
                "path": relative_to_campaign(campaign_root, path),
                "before_hash": file_document_hash(path),
                "after_hash": document_hash(document),
                "document": document,
            }
        )
    return result


def apply_prepared_writes(campaign_root: Path, writes: list[dict[str, Any]]) -> None:
    for write in writes:
        path = resolve_campaign_ref(campaign_root, write["path"])
        current_hash = file_document_hash(path)
        if current_hash == write["after_hash"]:
            continue
        if current_hash != write["before_hash"]:
            raise RuntimeError(f"state changed during transaction: {write['path']}")
        atomic_yaml(path, write["document"])


def event_from_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    outcome = transaction["outcome"]
    actor_id = transaction["request"].get("actor_id") or transaction["request"].get("subject_id")
    return {
        "id": transaction["event_id"],
        "timestamp": now_iso(),
        "scene_id": transaction.get("scene_id"),
        "type": "action_resolution",
        "summary": outcome["summary"],
        "actors": [actor_id] if isinstance(actor_id, str) else [],
        "location_id": outcome.get("location_id"),
        "time_advanced_seconds": transaction["time_operation"]["seconds"],
        "intent_achieved": outcome["intent_achieved"],
        "arrangement": outcome["arrangement"],
        "perspective": outcome["perspective"],
        "changes": outcome.get("operations", []),
        "roll_ids": [transaction["roll_id"]] if transaction.get("roll_id") else [],
        "superseded_by": None,
        # SLAD UZASADNIENIA PRZEZYWA COMMIT. Do 2026-09-04 to pole bylo wypelnione w 65 z 237
        # transakcji i w 0 z 235 wpisow dziennika - jedyne maszynowo sprawdzalne uzasadnienie
        # konsekwencji bylo wyrzucane dokladnie w momencie, w ktorym staje sie historia.
        # Bez tego nie da sie zaudytowac ani jednej tury po fakcie.
        # PROZA PISANA (etap 11). Gdy outcome poda `prose`, wpis dostaje krotka narracje
        # obok pelnego protokolu w `audit` - i to ona jest czytana przy otwarciu sesji.
        "prose": (outcome.get("prose") or "").strip() or None,
        "prose_source": "authored" if (outcome.get("prose") or "").strip() else "auto_extracted",
        "audit": outcome["summary"],
        "consequence_source_refs": list(outcome.get("consequence_source_refs") or []),
        "resolved_world_reaction_ids": list(outcome.get("resolved_world_reaction_ids") or []),
    }


def validate_outcome(outcome: dict[str, Any]) -> None:
    if not isinstance(outcome.get("intent_achieved"), bool):
        raise RuntimeError("outcome.intent_achieved must be boolean")
    if outcome.get("arrangement") not in ARRANGEMENTS:
        raise RuntimeError(f"outcome.arrangement must be one of {sorted(ARRANGEMENTS)}")
    if not isinstance(outcome.get("perspective"), str) or not outcome["perspective"]:
        raise RuntimeError("outcome.perspective is required")
    if not isinstance(outcome.get("summary"), str) or not outcome["summary"].strip():
        raise RuntimeError("outcome.summary is required")
    if not isinstance(outcome.get("operations", []), list):
        raise RuntimeError("outcome.operations must be a list")
    # ZAPORA NA PODWOJENIE CZASU (retcon_000118). commit dokleja transaction.time_operation
    # bezwarunkowo, wiec advance_time dopisany recznie do outcome.operations liczy sie DRUGI
    # RAZ. Zakaz stal w prozie AGENTS.md i w SKILL-gramy.md, a pomiar pokazuje 28 tur
    # z podwojnym advance_time, z czego retcon ratyfikowal tylko 5. Od teraz to warunek.
    for operation in outcome.get("operations", []):
        if isinstance(operation, dict) and operation.get("op") == "advance_time":
            raise RuntimeError(
                "outcome.operations nie moze zawierac advance_time - commit dokleja czas sam "
                "z request.time_seconds, a reczny wpis PODWAJA ture (retcon_000118). "
                "Usun ten wpis; czas bierze sie wylacznie z request.time_seconds."
            )
    source_refs = outcome.get("consequence_source_refs", [])
    if not isinstance(source_refs, list) or not all(
        isinstance(ref, str) and ref.strip() for ref in source_refs
    ):
        raise RuntimeError("outcome.consequence_source_refs must be a list of non-empty strings")


def validate_turn_identity(transaction: dict[str, Any]) -> None:
    """Kazda trwala tura ma actor_id, a test mechaniczny ma pelna trojke.

    AGENTS.md punkt 7 wymaga tego od dawna i nic tego nie sprawdzalo: "Kazda trwala tura ma
    actor_id, takze automatyczna i bez testu. Samo actor_id nie uruchamia silnika zdolnosci;
    test mechaniczny wymaga dodatkowo capability_id, target_id i intent_id".
    Tura bez actor_id konczy sie wpisem dziennika z pusta lista actors, czyli zdarzeniem
    bez sprawcy - i takich wpisow nie da sie pozniej przypisac do nikogo.

    UWAGA: 37 najstarszych tur (001-038) nie ma actor_id, bo powstaly przed ta konwencja.
    Bramka dziala WYLACZNIE przy commicie nowej tury, wiec historii nie unieważnia
    i nie wymaga migracji wstecz.
    """
    request = transaction.get("request") or {}
    if not (request.get("actor_id") or request.get("subject_id")):
        raise RuntimeError(
            "request.actor_id jest wymagane dla kazdej trwalej tury (AGENTS.md pkt 7) - "
            "bez niego wpis dziennika nie ma sprawcy"
        )
    triple = ("capability_id", "target_id", "intent_id")
    present = [key for key in triple if request.get(key)]
    if present and len(present) != len(triple):
        missing = [key for key in triple if not request.get(key)]
        raise RuntimeError(
            "test mechaniczny wymaga pelnej trojki capability_id + target_id + intent_id "
            f"(AGENTS.md pkt 7); brakuje: {', '.join(missing)}"
        )


def validate_source_refs_resolve(campaign_root: Path, outcome: dict[str, Any]) -> None:
    """Kazdy ref w consequence_source_refs musi wskazywac na cos, co ISTNIEJE.

    Do 2026-09-04 pole bylo sprawdzane wylacznie na "lista niepustych napisow", wiec
    wystarczylo napisac cokolwiek, zeby przejsc bramke z retcon_000058 (nie buduj ekspozycji
    z list, ktorych nie ma). Ta kontrola nie wylapie refu, ktory istnieje, ale nie mowi tego,
    co narrator twierdzi - to zostaje przy narratorze. Wylapie ref WYMYSLONY.
    """
    refs = outcome.get("consequence_source_refs") or []
    if not refs:
        return
    root = campaign_root.parent.parent

    retcon_ids: set[str] = set()
    retcons_path = campaign_root / "journal" / "retcons.jsonl"
    if retcons_path.exists():
        for line in retcons_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line:
                try:
                    retcon_ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue

    event_ids: set[str] = set()
    events_path = campaign_root / "journal" / "events.jsonl"
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line:
                try:
                    event_ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue

    # Deklaracja gracza i znaczniki pochodzenia nie maja pliku i nie da sie ich sprawdzic.
    PASS_PREFIX = ("player_declaration", "player_", "narrator_", "source_", "milestone_",
                   "candidate_", "http")
    unresolved: list[str] = []
    for ref in refs:
        text = ref.strip()
        base = text.split("#")[0].strip()
        if not base or text.startswith(PASS_PREFIX):
            continue
        if base in retcon_ids or base in event_ids:
            continue
        # JEDNOZNACZNY PREFIKS. Repo uzywa dwoch konwencji naraz - id bywa nagie
        # (event_turn_interlude_105) i z sufiksem opisowym
        # (event_turn_interlude_051_guard_and_contact_questions) - wiec ref pisany z pamieci
        # regularnie mija sie o sufiks. Prefiks pasujacy do DOKLADNIE JEDNEGO zdarzenia jest
        # jednoznaczny i rozwiazuje sie poprawnie; pasujacy do kilku jest odrzucany.
        # To nie biala lista: nieistniejaca tura nadal nie ma dopasowania.
        if base.startswith("event_"):
            matches = [event_id for event_id in event_ids if event_id.startswith(base)]
            if len(matches) == 1:
                continue
            if len(matches) > 1:
                unresolved.append(f"{text} (niejednoznaczny - pasuje do {len(matches)} zdarzen)")
                continue
        if "/" in base or base.endswith((".yaml", ".md", ".jsonl")):
            candidates = [root / base, campaign_root / base, campaign_root.parent / base]
            if any(candidate.exists() for candidate in candidates):
                continue
        unresolved.append(text)
    if unresolved:
        raise RuntimeError(
            "consequence_source_refs wskazuje na cos, czego nie ma: "
            + "; ".join(unresolved)
            + ". Uzasadnienie konsekwencji musi opierac sie na istniejacym pliku, zdarzeniu "
              "albo retconie (retcon_000058) - albo na jawnej deklaracji gracza "
              "(player_declaration:...)."
        )


def validate_interlude_outcome(transaction: dict[str, Any], outcome: dict[str, Any]) -> None:
    """Prevent narrator-created resistance during tension-zero preparation."""
    preview = transaction.get("preview", {})
    if preview.get("tension_level") != 0:
        return
    if outcome.get("arrangement") not in {"worsened", "complicated", "mixed"}:
        return
    if outcome.get("consequence_source_refs") or outcome.get("resolved_world_reaction_ids"):
        return
    raise RuntimeError(
        "tension-zero complication requires consequence_source_refs "
        "(canonical file/event/retcon or player_declaration:...)"
    )


def refresh_after_commit(campaign_root: Path, transaction: dict[str, Any]) -> dict[str, Any]:
    """Refresh the context without ever failing an already durable turn."""
    try:
        context = refresh_context(campaign_root, write=True)
    except (RuntimeError, gm_engine.EngineError) as exc:
        transaction["context_warnings"] = [f"refresh_failed:{exc}"]
        return transaction
    transaction["context_warnings"] = context.get("context_warnings", [])
    transaction["context_bytes"] = context.get("context_bytes")
    return transaction


def commit_turn(
    campaign_root: Path, turn_id: str, outcome: dict[str, Any], allow_noncanonical: bool
) -> dict[str, Any]:
    require_writable_campaign(campaign_root, allow_noncanonical)
    path = transaction_path(campaign_root, require_id(turn_id, "turn_id"))
    transaction = load_yaml(path)
    if transaction.get("status") == "committed":
        # Retrying a committed turn must still repair a context left stale by an
        # earlier failed refresh, otherwise the campaign never recovers.
        return refresh_after_commit(campaign_root, transaction)
    if transaction.get("status") == "aborted":
        raise RuntimeError(f"turn {turn_id} is aborted")
    if transaction.get("status") == "prepared":
        return recover_turn(campaign_root, turn_id, allow_noncanonical)
    if transaction.get("status") != "resolved":
        raise RuntimeError(f"turn {turn_id} cannot be committed from {transaction.get('status')}")
    validate_outcome(outcome)
    validate_interlude_outcome(transaction, outcome)
    validate_source_refs_resolve(campaign_root, outcome)
    validate_turn_identity(transaction)
    due = transaction.get("preview", {}).get("world_reactions_due_before", [])
    resolved_ids = set(outcome.get("resolved_world_reaction_ids", []))
    if due and not resolved_ids.intersection(item.get("id") for item in due if isinstance(item, dict)):
        raise RuntimeError("at least one due world reaction must be resolved in this turn")

    operations: list[dict[str, Any]] = []
    if outcome.get("apply_required_costs", True):
        operations.extend(transaction.get("required_operations", []))
    operations.extend(copy.deepcopy(outcome.get("operations", [])))
    operations.append(transaction["time_operation"])
    changed: dict[Path, dict[str, Any]] = {}
    for operation in operations:
        apply_operation(campaign_root, changed, operation, transaction["event_id"])
    scene_path = campaign_root / "context" / "scene.yaml"
    scene = load_mutable(campaign_root, changed, scene_path)
    if resolved_ids:
        scene["pending_world_reactions"] = [
            item for item in scene.get("pending_world_reactions", []) if item.get("id") not in resolved_ids
        ]
    if outcome.get("new_decision"):
        scene["immediate_questions"] = [outcome["new_decision"]]
    scene["last_event_id"] = transaction["event_id"]
    transaction["outcome"] = copy.deepcopy(outcome)
    transaction["outcome"]["operations"] = operations
    transaction["prepared_writes"] = prepare_writes(campaign_root, changed)
    transaction["status"] = "prepared"
    transaction["prepared_at"] = now_iso()
    atomic_yaml(path, transaction)
    apply_prepared_writes(campaign_root, transaction["prepared_writes"])
    append_jsonl_once(campaign_root / "journal" / "events.jsonl", event_from_transaction(transaction))
    transaction["status"] = "committed"
    transaction["committed_at"] = now_iso()
    atomic_yaml(path, transaction)
    return refresh_after_commit(campaign_root, transaction)


def abort_turn(
    campaign_root: Path, turn_id: str, reason: str, allow_noncanonical: bool
) -> dict[str, Any]:
    require_writable_campaign(campaign_root, allow_noncanonical)
    path = transaction_path(campaign_root, require_id(turn_id, "turn_id"))
    transaction = load_yaml(path)
    if transaction.get("status") == "committed":
        raise RuntimeError("committed turns cannot be aborted")
    if transaction.get("status") == "prepared":
        raise RuntimeError("prepared turns must be recovered, not aborted")
    transaction["status"] = "aborted"
    transaction["aborted_at"] = now_iso()
    transaction["abort_reason"] = reason
    atomic_yaml(path, transaction)
    return transaction


def recover_turn(
    campaign_root: Path, turn_id: str, allow_noncanonical: bool
) -> dict[str, Any]:
    require_writable_campaign(campaign_root, allow_noncanonical)
    path = transaction_path(campaign_root, require_id(turn_id, "turn_id"))
    transaction = load_yaml(path)
    if transaction.get("status") == "committed":
        return refresh_after_commit(campaign_root, transaction)
    if transaction.get("status") != "prepared":
        raise RuntimeError(f"only prepared transactions can be recovered, found {transaction.get('status')}")
    apply_prepared_writes(campaign_root, transaction.get("prepared_writes", []))
    append_jsonl_once(campaign_root / "journal" / "events.jsonl", event_from_transaction(transaction))
    transaction["status"] = "committed"
    transaction["committed_at"] = now_iso()
    transaction["recovered"] = True
    atomic_yaml(path, transaction)
    return refresh_after_commit(campaign_root, transaction)


def context_refs(campaign_root: Path, scene: dict[str, Any]) -> list[str]:
    def contextual_ref(relative: str) -> str:
        return project_ref(campaign_root / relative)

    refs: list[str] = [
        contextual_ref("context/scene.yaml"),
        contextual_ref("state/time.yaml"),
        contextual_ref("state/clocks.yaml"),
        contextual_ref("state/objectives.yaml"),
    ]
    for state_file in ("sustained-links.yaml", "obligations.yaml"):
        optional_state = campaign_root / "state" / state_file
        if optional_state.exists():
            refs.append(project_ref(optional_state))
    if isinstance(scene.get("location_ref"), str):
        refs.append(scene["location_ref"])
    index = load_instance_index(campaign_root)
    by_id = {item.get("id"): item.get("ref") for item in index.get("instances", []) if isinstance(item, dict)}
    for participant in scene.get("participants", []):
        participant_id = participant.get("id") if isinstance(participant, dict) else participant
        ref = by_id.get(participant_id)
        if isinstance(ref, str):
            refs.append(project_ref(resolve_campaign_ref(campaign_root, ref)))
    for ref in scene.get("active_refs", []):
        if isinstance(ref, str):
            refs.append(ref)
    return list(dict.fromkeys(refs))


def ref_path(ref: str, campaign_root: Path | None = None) -> Path:
    """Rozwiazuje ref do sciezki, probujac obu konwencji uzywanych w repo.

    context/active.yaml MIESZA dwie konwencje: czesc refow jest wzgledem korzenia repo
    ("system/tests.md", "campaigns/lucan/state/secrets.yaml"), a czesc wzgledem kampanii
    ("planning/act-03-defence.yaml"). Do 2026-09-04 rozwiazywany byl tylko pierwszy
    wariant, wiec plik deklarowany jako OBOWIAZKOWY w kazdej turze planowania - 78 517 B,
    czyli 1,92 budzetu - byl dla licznika kontekstu NIEWIDZIALNY i zglaszal sie jako brak.
    Zwracamy pierwszy wariant, ktory istnieje; gdy zaden, zwracamy wersje od korzenia repo,
    zeby komunikat o braku wskazywal sensowna sciezke.
    """
    path = Path(ref)
    if path.is_absolute():
        return path
    kandydaci = [ROOT / path]
    for root in (campaign_root, ROOT / "campaigns" / "lucan"):
        if root is not None:
            kandydaci.append(root / path)
    for kandydat in kandydaci:
        if kandydat.exists():
            return kandydat
    return kandydaci[0]


def refresh_context(campaign_root: Path, write: bool, strict: bool = False) -> dict[str, Any]:
    """Rebuild the minimal context.

    Overflowing the budget or losing a referenced file is reported, not raised.
    A committed turn is already durable when this runs, so raising here used to
    leave the campaign with a permanently stale ``active.yaml``: the retry saw
    ``status: committed`` and returned before ever refreshing.  ``strict`` is for
    validation runs that legitimately want a non-zero exit code.
    """
    scene = scene_document(campaign_root)
    active_path = campaign_root / "context" / "active.yaml"
    active = load_yaml(active_path)
    refs = context_refs(campaign_root, scene)
    forbidden = ("migration/sources", "migration/noncanonical")
    if any(any(token in ref.replace("\\", "/") for token in forbidden) for ref in refs):
        raise RuntimeError("active context may not load raw or noncanonical migration material")
    loaded_refs = list(active.get("always_load", [])) + refs
    missing = [ref for ref in loaded_refs if not ref_path(ref).exists()]
    sizes = {
        ref: ref_path(ref).stat().st_size for ref in loaded_refs if ref not in missing
    }
    total = sum(sizes.values())
    warnings: list[str] = []
    if missing:
        warnings.append(f"missing_refs:{','.join(missing)}")
    if total > CONTEXT_BUDGET_BYTES:
        warnings.append(f"over_budget:{total}>{CONTEXT_BUDGET_BYTES}")
    result = copy.deepcopy(active)
    result["active_refs"] = refs
    result["search_terms"] = [
        str(value) for value in scene.get("immediate_questions", []) + scene.get("pressures", [])
    ]
    result["last_refreshed_event_id"] = scene.get("last_event_id")
    result["context_bytes"] = total
    result["context_budget_bytes"] = CONTEXT_BUDGET_BYTES
    # UCZCIWA KSIEGOWOSC (etap 6). context_bytes liczy always_load + active_refs i tyle -
    # a tura widzi wiecej: AGENTS.md (wymieniony przez brief jako regula), karty NPC
    # stojacych w scenie (zmierzone 68 KB) i wybrany zbior load_when_*. Licznik pokazywal
    # 54 451 B przy realnej turze planowania wazacej ponad 160 000 B, czyli mierzyl
    # mniejsza czesc tury. context_bytes zostaje BEZ ZMIANY SEMANTYKI, bo na nim stoi
    # dzialajaca bramka walidatora; prawda dochodzi obok, jako rozbicie.
    cards = participant_card_refs(campaign_root, scene)
    card_sizes = {ref: ref_size(ref) or 0 for ref in cards}
    digest_sizes = {}
    for ref in cards:
        digest = npc_digest_ref(ref_path(ref))
        digest_sizes[ref] = (ref_size(digest) or 0) if digest else card_sizes[ref]
    agents_size = ref_size("AGENTS.md") or 0
    sets = conditional_sets(active)
    result["conditional_sets"] = {
        tag: {"refs": entries, "bytes": sum(e.get("bytes", 0) for e in entries)}
        for tag, entries in sets.items()
    }
    result["context_breakdown"] = {
        "rules_always": agents_size + sum(
            ref_size(ref) or 0 for ref in active.get("always_load", [])),
        "state_active": sum(sizes.get(ref, 0) for ref in refs),
        "participant_cards": sum(card_sizes.values()),
        # Skroty kart (etap 8): to samo, co narrator faktycznie potrzebuje przeczytac,
        # gdy nie siega po szczegol starszego faktu. Roznica jest miara etapu 8.
        "participant_digests": sum(digest_sizes.values()),
        "conditional_heaviest": max(
            ((tag, sum(e.get("bytes", 0) for e in entries)) for tag, entries in sets.items()),
            key=lambda item: item[1], default=("", 0))[1],
    }
    breakdown = result["context_breakdown"]
    result["context_total_bytes"] = (
        breakdown["rules_always"] + breakdown["state_active"] + breakdown["participant_cards"])
    if result["context_total_bytes"] > CONTEXT_BUDGET_BYTES:
        # Informacyjnie, NIE jako bramka: gdyby to blokowalo, walidator swiecilby na
        # czerwono bez przerwy i zostalby zignorowany. Bramka zostaje na context_bytes,
        # ktore da sie realnie zmniejszyc odchudzeniem active_refs i always_load.
        warnings.append(
            f"total_informational:{result['context_total_bytes']}>{CONTEXT_BUDGET_BYTES}")
    result["context_warnings"] = warnings
    # Naming the heaviest refs turns "over budget" into an actionable list.
    result["heaviest_refs"] = [
        {"ref": ref, "bytes": size}
        for ref, size in sorted(sizes.items(), key=lambda item: -item[1])[:5]
    ]
    if write:
        atomic_yaml(active_path, result)
    if strict and warnings:
        raise RuntimeError("; ".join(warnings))
    return result


def ref_size(ref: str) -> int | None:
    path = ref_path(ref)
    return path.stat().st_size if path.exists() else None


def conditional_sets(active: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Zbiory load_when_* z rozmiarami. Etap 6.

    Do 2026-09-04 te szesc kluczy bylo martwym pasazerem: refresh_context przepisywalo je
    przez copy.deepcopy i ZADNA linia kodu ich nie czytala, wiec warunkowe wczytywanie
    istnialo wylacznie jako dobra wola narratora - i SKILL-gramy.md zapisuje juz awarie
    tego mechanizmu. Teraz sa rozwiazywane, wazone i wypisywane, a `context plan --tag`
    zwraca dokladna liste plikow na dana ture.
    """
    out: dict[str, list[dict[str, Any]]] = {}
    for key, refs in active.items():
        if not key.startswith("load_when_") or not isinstance(refs, list):
            continue
        entries = []
        for ref in refs:
            if not isinstance(ref, str):
                continue
            size = ref_size(ref)
            entry: dict[str, Any] = {"ref": ref}
            if size is None:
                entry["missing"] = True
            else:
                entry["bytes"] = size
            entries.append(entry)
        out[key[len("load_when_"):]] = entries
    return out


def context_plan(campaign_root: Path, tags: list[str]) -> dict[str, Any]:
    """Dokladna lista plikow na ture o podanych tagach sytuacji. Etap 6.

    To jest wykonawcza czesc load_when_*: narrator pyta o liste, dostaje liste i sume
    bajtow, zamiast pamietac, ktory klucz dotyczy tej tury.
    """
    active = load_yaml(campaign_root / "context" / "active.yaml")
    scene = scene_document(campaign_root)
    sets = conditional_sets(active)
    unknown = [tag for tag in tags if tag not in sets]

    base = ["AGENTS.md"] + list(active.get("always_load", [])) + context_refs(campaign_root, scene)
    participants = participant_card_refs(campaign_root, scene)
    chosen: list[str] = []
    for tag in tags:
        for entry in sets.get(tag, []):
            if entry.get("ref") not in chosen:
                chosen.append(entry["ref"])

    def weigh(refs: list[str]) -> tuple[list[dict[str, Any]], int]:
        rows, total = [], 0
        for ref in dict.fromkeys(refs):
            size = ref_size(ref)
            rows.append({"ref": ref, "bytes": size} if size is not None else {"ref": ref, "missing": True})
            total += size or 0
        return rows, total

    base_rows, base_total = weigh(base)
    card_rows, card_total = weigh(participants)
    cond_rows, cond_total = weigh(chosen)
    grand = base_total + card_total + cond_total
    return {
        "tags": tags,
        "unknown_tags": unknown,
        "available_tags": sorted(sets),
        "base": base_rows,
        "participant_cards": card_rows,
        "conditional": cond_rows,
        "bytes": {
            "base": base_total,
            "participant_cards": card_total,
            "conditional": cond_total,
            "total": grand,
            "budget": CONTEXT_BUDGET_BYTES,
            "over_budget_by": max(0, grand - CONTEXT_BUDGET_BYTES),
        },
    }


def npc_digest_ref(card_path: Path) -> str | None:
    """Ref do skrotu karty, jesli istnieje (tools/build_npc_digests.py)."""
    candidate = card_path.parent / "digests" / card_path.name
    return project_ref(candidate) if candidate.exists() else None


def participant_card_refs(campaign_root: Path, scene: dict[str, Any]) -> list[str]:
    """Karty NPC stojacych w scenie. Licznik kontekstu ich nie widzial, a to 68 KB."""
    refs: list[str] = []
    for participant in scene.get("participants", []):
        pid = participant.get("id") if isinstance(participant, dict) else participant
        if not isinstance(pid, str):
            continue
        path = find_named_entity_path(campaign_root, pid)
        if path is not None and path.exists():
            refs.append(project_ref(path))
    return refs


def recent_prose(campaign_root: Path, limit: int) -> dict[str, Any]:
    """Tanie otwarcie sesji: proza ostatnich tur, bez protokolu audytowego. Etap 11.

    Do 2026-09-04 otwarcie sesji znaczylo przeczytanie czterech ostatnich pol `summary`,
    czyli 33 235 znakow, z ktorych ponad polowa byla protokolem: cytatami plikow,
    uzasadnieniami narratora i lista "czego narrator NIE zrobil". To bylo zle w dwie strony -
    kosztowalo budzet i podsuwalo rejestr ksiegowy jako wzorzec jezyka, czego skutki repo
    zdiagnozowalo dwa razy (retcon_000040, retcon_000136).
    """
    path = campaign_root / "journal" / "events.jsonl"
    if not path.exists():
        return {"turns": [], "chars": 0}
    events = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    out = []
    for event in events[-max(1, limit):]:
        prose = event.get("prose") or event.get("prose_auto") or ""
        out.append({
            "id": event.get("id"),
            "scene_id": event.get("scene_id"),
            "prose": prose,
            "prose_source": ("authored" if event.get("prose")
                             else event.get("prose_source", "auto_extracted")),
            "audit_chars": len(event.get("audit") or event.get("summary") or ""),
            "superseded_by": event.get("superseded_by"),
            "supersession_scope": event.get("supersession_scope"),
        })
    return {
        "turns": out,
        "chars": sum(len(row["prose"]) for row in out),
        "audit_chars_skipped": sum(row["audit_chars"] for row in out),
        "note": ("Proza, nie protokol. Pelny slad tury: pole `audit` we wpisie albo "
                 "journal/transactions/<turn_id>.yaml. Wpis oznaczony superseded_by jest "
                 "uchylony - sprawdz supersession_scope (aspect = poprawione jedno zdanie)."),
    }


def recall(campaign_root: Path, query: str, limit: int) -> dict[str, Any]:
    """Punktowe siegniecie w kanon historyczny.

    PRZEBUDOWANE 2026-09-04. Poprzednia wersja skanowala events.jsonl PRZED retcons.jsonl
    i przerywala na pierwszych `limit` trafieniach, wiec:
      - zwracala wylacznie NAJSTARSZE tury (dla frazy "Seraphine" 86,8% kampanii bylo
        nieosiagalne, biezaca scena tez),
      - nigdy nie dosiegala retconow, mimo ze zatwierdzony retcon jest kanonem NR 1
        (system/canon-policy.md), czyli oddawala fakty JUZ UCHYLONE jako jedyna odpowiedz,
      - pokazywala pierwsze 600 znakow linii, czesto BEZ szukanej frazy (2 z 5 trafien).
    Teraz: zbiera wszystkie trafienia, sortuje retcony przed dziennikiem, a w kazdym zrodle
    NAJNOWSZE przed najstarszymi, i wycina okno TEKSTU WOKOL FRAZY.
    """
    needle = query.casefold()
    if not needle:
        raise RuntimeError("recall wymaga niepustej frazy")

    def window(line: str, position: int, width: int = 560) -> str:
        start = max(0, position - width // 3)
        end = min(len(line), start + width)
        fragment = line[start:end].strip()
        return ("..." if start > 0 else "") + fragment + ("..." if end < len(line) else "")

    sources: list[tuple[int, Path]] = [
        (0, campaign_root / "journal" / "retcons.jsonl"),
        (1, campaign_root / "journal" / "events.jsonl"),
        (2, campaign_root / "journal" / "superseded" / "MANIFEST.json"),
    ]
    sources += [(3, path) for path in sorted((campaign_root / "journal" / "sessions").glob("*.md"))]

    found: list[dict[str, Any]] = []
    per_source: dict[str, int] = {}
    for rank, path in sources:
        if not path.exists():
            continue
        try:
            source_ref = path.relative_to(ROOT).as_posix()
        except ValueError:
            source_ref = str(path.resolve())
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for number, line in enumerate(lines, 1):
            position = line.casefold().find(needle)
            if position < 0:
                continue
            per_source[source_ref] = per_source.get(source_ref, 0) + 1
            found.append({
                "ref": f"{source_ref}#line:{number}",
                "kind": {0: "retcon", 1: "event", 2: "superseded", 3: "session"}[rank],
                "text": window(line.strip(), position),
                "_rank": rank,
                "_line": number,
            })

    # Retcony pierwsze (kanon nr 1), potem dziennik od NAJNOWSZYCH.
    found.sort(key=lambda item: (item["_rank"], -item["_line"]))

    # PODZIAL LIMITU, zeby zadne zrodlo nie wypchnelo drugiego. Sam priorytet retconow
    # odtwarzalby pierwotna awarie od drugiej strony: przy --limit 5 wszystkie piec
    # trafien bylo z retconow i biezaca scena znow byla nieosiagalna.
    quota = {"retcon": max(1, limit // 2)}
    shown: list[dict[str, Any]] = []
    taken: dict[str, int] = {}
    for item in found:
        cap = quota.get(item["kind"])
        if cap is not None and taken.get(item["kind"], 0) >= cap:
            continue
        shown.append(item)
        taken[item["kind"]] = taken.get(item["kind"], 0) + 1
        if len(shown) >= limit:
            break
    if len(shown) < limit:                      # dopelnij tym, co odrzucila kwota
        for item in found:
            if item not in shown:
                shown.append(item)
                if len(shown) >= limit:
                    break
    shown = shown[:limit]
    for item in shown:
        item.pop("_rank", None)
        item.pop("_line", None)
    return {
        "query": query,
        "matches": shown,
        "truncated": len(found) > limit,
        "total_matches": len(found),
        "matches_per_source": per_source,
    }


def close_scene(
    campaign_root: Path,
    new_scene_id: str,
    summary: str,
    location_ref: str | None,
    participants: list[str],
    allow_noncanonical: bool,
) -> dict[str, Any]:
    require_writable_campaign(campaign_root, allow_noncanonical)
    require_id(new_scene_id, "new_scene_id")
    scene_path = campaign_root / "context" / "scene.yaml"
    scene = load_yaml(scene_path)
    old_id = scene.get("scene_id") or "uninitialized_scene"
    snapshot = {
        "schema_version": 1,
        "id": f"snapshot_{old_id}",
        "object_type": "scene_snapshot",
        "closed_at": now_iso(),
        "summary": summary,
        "scene": scene,
        "active_context": load_yaml(campaign_root / "context" / "active.yaml"),
    }
    snapshot_path = campaign_root / "snapshots" / f"{old_id}.yaml"
    if snapshot_path.exists():
        raise RuntimeError(f"scene snapshot already exists: {old_id}")
    atomic_yaml(snapshot_path, snapshot)
    # Scena zaczyna sie w czasie KAMPANII, nie w czasie rzeczywistym. Zegar kampanii
    # zostaje w tyle za realnym (18.08 fikcji przy 30.08 na sciennym), wiec now_iso()
    # zapisywalo date z przyszlosci i validate_project.py odrzucal kazde zamkniecie
    # sceny: "active scene starts after current campaign time".
    campaign_time = load_yaml(campaign_root / "state" / "time.yaml").get("current_datetime")
    next_scene = {
        "schema_version": 1,
        "campaign_id": scene.get("campaign_id", "campaign_lucan"),
        "status": scene.get("status", "active"),
        "scene_id": new_scene_id,
        "location_ref": location_ref,
        "started_at": campaign_time or now_iso(),
        "tension": {"level": 0, "reason": None},
        "participants": participants,
        "pressures": [],
        "immediate_facts": [],
        "immediate_questions": [],
        "pending_world_reactions": [],
        "last_event_id": scene.get("last_event_id"),
        "previous_scene_snapshot_ref": relative_to_campaign(campaign_root, snapshot_path),
    }
    atomic_yaml(scene_path, next_scene)
    refresh_context(campaign_root, write=True)
    return {"closed_scene_id": old_id, "snapshot": str(snapshot_path), "new_scene": next_scene}


def migration_readiness(campaign_root: Path) -> dict[str, Any]:
    migration = load_yaml(campaign_root / "migration" / "migration.yaml")
    approvals = load_yaml(campaign_root / "migration" / "approvals" / "index.yaml")
    packages_index = load_yaml(campaign_root / "migration" / "packages" / "index.yaml")
    package_revisions: dict[str, int] = {}
    package_statuses: dict[str, str] = {}
    for entry in packages_index.get("packages", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("ref"), str):
            continue
        package = load_yaml(ROOT / entry["ref"])
        package_revisions[entry["id"]] = package.get("revision")
        package_statuses[entry["id"]] = package.get("status")
    approval_problems: list[str] = []
    for record in approvals.get("approvals", []):
        package_id = record.get("package_id")
        if record.get("revision") != package_revisions.get(package_id):
            approval_problems.append(f"revision_mismatch:{package_id}")
        if record.get("status") != "approved":
            approval_problems.append(f"not_approved:{package_id}")
        if package_statuses.get(package_id) != "approved":
            approval_problems.append(f"package_not_approved:{package_id}")
    blockers = [item.get("id") for item in migration.get("blockers", []) if isinstance(item, dict)]
    ready = not blockers and not approval_problems
    return {
        "migration_id": migration.get("migration_id"),
        "ready": ready,
        "blockers": blockers,
        "approval_problems": approval_problems,
        "activation_active": migration.get("activation", {}).get("active", False),
    }


def activate_migration(campaign_root: Path, manifest_path: Path, dry_run: bool) -> dict[str, Any]:
    readiness = migration_readiness(campaign_root)
    if not readiness["ready"]:
        raise RuntimeError(
            "migration activation refused: "
            + ", ".join(readiness["blockers"] + readiness["approval_problems"])
        )
    manifest = load_yaml(manifest_path)
    writes = manifest.get("writes")
    if not isinstance(writes, list) or not writes:
        raise RuntimeError("activation manifest requires non-empty writes")
    changed: dict[Path, dict[str, Any]] = {}
    for entry in writes:
        if not isinstance(entry, dict) or not isinstance(entry.get("target"), str) or not isinstance(entry.get("source"), str):
            raise RuntimeError("activation writes require target and source")
        target = resolve_campaign_ref(campaign_root, entry["target"])
        source = resolve_campaign_ref(campaign_root, entry["source"])
        try:
            target.resolve().relative_to(campaign_root.resolve())
            source.resolve().relative_to(campaign_root.resolve())
        except ValueError as exc:
            raise RuntimeError("activation manifest paths must stay within campaign root") from exc
        changed[target.resolve()] = load_yaml(source)
    campaign_path = campaign_root / "campaign.yaml"
    campaign = load_yaml(campaign_path)
    campaign["status"] = "active"
    changed[campaign_path.resolve()] = campaign
    migration_path = campaign_root / "migration" / "migration.yaml"
    migration = load_yaml(migration_path)
    migration["status"] = "activated"
    migration.setdefault("activation", {})["active"] = True
    migration["activation"]["activated_at"] = now_iso()
    migration["activation"]["activation_event_id"] = "event_migration_activation"
    changed[migration_path.resolve()] = migration
    for relative in ("context/active.yaml", "context/scene.yaml", "state/instances/index.yaml"):
        path = campaign_root / relative
        # A migration manifest may stage either context document.  Preserve that
        # staged content while applying the activation marker instead of
        # accidentally reloading and overwriting it from the pre-activation file.
        document = copy.deepcopy(changed.get(path.resolve(), load_yaml(path)))
        document["status"] = "active"
        if relative.endswith("index.yaml"):
            document["activation"] = True
        changed[path.resolve()] = document
    prepared = prepare_writes(campaign_root, changed)
    result = {**readiness, "dry_run": dry_run, "writes": [item["path"] for item in prepared]}
    if dry_run:
        return result
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_path = campaign_root / "snapshots" / f"pre-activation-{stamp}.yaml"
    snapshot = {
        "schema_version": 1,
        "id": f"snapshot_pre_activation_{stamp}",
        "object_type": "migration_activation_snapshot",
        "created_at": now_iso(),
        "documents": [
            {"path": item["path"], "document": load_yaml(resolve_campaign_ref(campaign_root, item["path"]))}
            for item in prepared
            if resolve_campaign_ref(campaign_root, item["path"]).exists()
        ],
    }
    atomic_yaml(snapshot_path, snapshot)
    transaction = {
        "schema_version": 1,
        "id": "migration_activation",
        "object_type": "migration_activation_transaction",
        "status": "prepared",
        "created_at": now_iso(),
        "prepared_writes": prepared,
        "snapshot_ref": relative_to_campaign(campaign_root, snapshot_path),
    }
    activation_tx = transaction_path(campaign_root, "migration_activation")
    atomic_yaml(activation_tx, transaction)
    apply_prepared_writes(campaign_root, prepared)
    append_jsonl_once(
        campaign_root / "journal" / "events.jsonl",
        {
            "id": "event_migration_activation",
            "timestamp": now_iso(),
            "scene_id": None,
            "type": "migration_activation",
            "summary": "Zatwierdzone pakiety migracyjne zostały atomowo aktywowane.",
            "actors": [],
            "changes": [{"ref": item["path"]} for item in prepared],
            "roll_ids": [],
            "superseded_by": None,
        },
    )
    transaction["status"] = "committed"
    transaction["committed_at"] = now_iso()
    atomic_yaml(activation_tx, transaction)
    result["snapshot"] = str(snapshot_path)
    result["activated"] = True
    return result


# --- Compact output -------------------------------------------------------
#
# Every byte printed here is re-sent to the model on every later turn of the
# conversation, so the default output carries decisions only.  Everything the
# narrator already wrote (the request), already saw (the preview) or can read
# from disk (the written documents) is dropped unless --verbose asks for it.


def roll_summary(roll: dict[str, Any] | None) -> dict[str, Any] | None:
    if not roll:
        return None
    return {
        "id": roll.get("id"),
        "natural": roll.get("natural_roll"),
        "modified": roll.get("modified_result"),
        "difficulty": roll.get("difficulty"),
        "passes": roll.get("passes_threshold"),
        "critical": roll.get("critical"),
    }


def assessment_summary(assessment: dict[str, Any]) -> dict[str, Any]:
    guidance = assessment.get("test_guidance") or {}
    summary: dict[str, Any] = {
        "verdict": assessment.get("verdict"),
        "roll_allowed": assessment.get("roll_allowed", False),
    }
    if guidance.get("scope"):
        summary["scope"] = guidance["scope"]
    if guidance.get("suggested_difficulty") is not None:
        summary["suggested_difficulty"] = guidance["suggested_difficulty"]
    # Alternative paths and hard-limit details only matter when the engine says
    # no; when it says yes they are several hundred tokens of confirmation.
    for key in ("blocking_reasons", "resource_shortfalls", "resource_costs"):
        if assessment.get(key):
            summary[key] = assessment[key]
    return summary


def scene_followups(campaign_root: Path) -> dict[str, Any]:
    try:
        scene = scene_document(campaign_root)
    except RuntimeError:
        return {}
    pending = [
        item.get("id") for item in scene.get("pending_world_reactions", []) if isinstance(item, dict)
    ]
    followups: dict[str, Any] = {}
    if pending:
        followups["pending_world_reactions"] = pending
    if scene.get("immediate_questions"):
        followups["immediate_questions"] = scene["immediate_questions"]
    return followups


def transaction_summary(
    transaction: dict[str, Any], campaign_root: Path | None = None
) -> dict[str, Any]:
    if transaction.get("object_type") != "turn_transaction":
        return preview_summary(transaction)
    preview = transaction.get("preview") or {}
    summary: dict[str, Any] = {
        "turn_id": transaction.get("id"),
        "status": transaction.get("status"),
        "event_id": transaction.get("event_id"),
        "time_seconds": (transaction.get("time_operation") or {}).get("seconds"),
    }
    summary.update(assessment_summary(preview.get("assessment") or {}))
    summary["roll"] = roll_summary(transaction.get("roll"))
    if transaction.get("status") == "resolved":
        due = preview.get("world_reactions_due_before") or []
        if due:
            summary["world_reactions_due"] = [
                item.get("id") for item in due if isinstance(item, dict)
            ]
    if transaction.get("status") == "committed":
        summary["changed"] = [
            write.get("path") for write in transaction.get("prepared_writes", [])
        ]
        summary["context_bytes"] = transaction.get("context_bytes")
        if campaign_root is not None:
            summary.update(scene_followups(campaign_root))
    if transaction.get("recovered"):
        summary["recovered"] = True
    if transaction.get("abort_reason"):
        summary["abort_reason"] = transaction["abort_reason"]
    if transaction.get("context_warnings"):
        summary["context_warnings"] = transaction["context_warnings"]
    return summary


def preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    if preview.get("status") == "system_only_noop":
        return {key: preview[key] for key in ("turn_id", "status", "reason") if key in preview}
    summary: dict[str, Any] = {
        "turn_id": preview.get("turn_id"),
        "status": preview.get("status"),
        "time_seconds": preview.get("time_seconds"),
    }
    summary.update(assessment_summary(preview.get("assessment") or {}))
    due = preview.get("world_reactions_due_before") or []
    if due:
        summary["world_reactions_due"] = [item.get("id") for item in due if isinstance(item, dict)]
    return summary


def context_summary(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_bytes": context.get("context_bytes"),
        "context_budget_bytes": context.get("context_budget_bytes"),
        "active_refs": len(context.get("active_refs", [])),
        "context_warnings": context.get("context_warnings", []),
        "heaviest_refs": context.get("heaviest_refs", []),
    }


# --- Session brief --------------------------------------------------------


def instance_digest(instance: dict[str, Any]) -> dict[str, Any]:
    digest: dict[str, Any] = {"id": instance.get("id")}
    pools = {}
    for pool_id, pool in (instance.get("resources") or {}).items():
        if isinstance(pool, dict) and "current" in pool:
            pools[pool_id] = f"{pool.get('current')}/{pool.get('capacity')}"
    if pools:
        digest["resources"] = pools
    conditions = [
        item.get("id") for item in instance.get("conditions", []) if isinstance(item, dict)
    ]
    if conditions:
        digest["conditions"] = conditions
    if instance.get("position"):
        digest["position"] = instance["position"]
    if instance.get("integrity"):
        digest["integrity"] = instance["integrity"]
    return digest


def objective_digest(objective: dict[str, Any]) -> dict[str, Any]:
    """Keep a goal useful in a fresh session without inlining its audit trail."""
    digest = {
        key: objective.get(key)
        for key in ("id", "status", "commitment")
        if objective.get(key) is not None
    }
    steps = [step for step in objective.get("steps", []) if isinstance(step, dict)]
    terminal_prefixes = ("done", "completed", "standing_decision", "solved")
    open_step_ids = [
        step.get("id")
        for step in steps
        if isinstance(step.get("id"), str)
        and not str(step.get("state", "pending")).startswith(terminal_prefixes)
    ]
    if open_step_ids:
        digest["open_step_ids"] = open_step_ids[:5]
        digest["open_step_count"] = len(open_step_ids)
    return digest


def interlude_scope_digest(scope: dict[str, Any]) -> dict[str, Any]:
    """Expose the current play boundary without copying objective metadata."""
    if not isinstance(scope, dict) or not scope:
        return {}
    return {
        key: scope.get(key)
        for key in ("detail_ref", "completion_gate", "rolls", "entry_rule", "workstreams")
        if scope.get(key) is not None
    }


def session_brief(campaign_root: Path, full: bool) -> dict[str, Any]:
    """One self-contained block that opens a fresh conversation.

    Conversation cost grows with the square of its length, because every turn
    resends the whole history.  Starting a new conversation per scene is the
    cheapest available fix, and it only works if reopening is a single step.
    """
    campaign = load_yaml(campaign_root / "campaign.yaml")
    scene = scene_document(campaign_root)
    context = refresh_context(campaign_root, write=False)
    time_doc = load_optional_yaml(campaign_root / "state" / "time.yaml", {})
    clocks_doc = load_optional_yaml(campaign_root / "state" / "clocks.yaml", {"clocks": []})
    objectives = load_optional_yaml(campaign_root / "state" / "objectives.yaml", {})
    obligations = load_optional_yaml(campaign_root / "state" / "obligations.yaml", {})

    participants: list[dict[str, Any]] = []
    participant_refs: list[str] = []
    for participant in scene.get("participants", []):
        participant_id = participant.get("id") if isinstance(participant, dict) else participant
        if not isinstance(participant_id, str):
            continue
        path = find_instance_path(campaign_root, participant_id)
        if path is not None and path.exists():
            digest = instance_digest(load_yaml(path))
            digest["state_ref"] = project_ref(path)
            participants.append(digest)
            continue
        entity_path = find_named_entity_path(campaign_root, participant_id)
        if entity_path is not None and entity_path.exists():
            entity = load_yaml(entity_path)
            entity_ref = project_ref(entity_path)
            participant_refs.append(entity_ref)
            digest = {
                "id": participant_id,
                "name": entity.get("name"),
                "role": entity.get("role"),
                "entity_ref": entity_ref,
            }
            # Karta relacji i swiezosc obu kart. Do 2026-09-04 brief nie wypisywal ani
            # relationship_ref, ani stanu swiezosci, wiec najgestszy zapis "co ta postac
            # o Lucanie mysli" (relationships/*.yaml, osie i axis_change_log) nie trafial
            # do narratora ani razu - karta seraphine--lucan.yaml stala 197 tur w tyle.
            digest_ref = npc_digest_ref(entity_path)
            if digest_ref:
                # SKROT KARTY (etap 8). Pelna karta Seraphiny wazy 60 675 B, skrot 19 404 B.
                # Skrot NIE JEST kanonem - trzyma czesc "jak grac" 1:1, najnowsze fakty
                # w calosci i indeks starszych. Szczegol starszego faktu dociagnij z karty.
                digest["digest_ref"] = digest_ref
                digest["digest_bytes"] = ref_size(digest_ref)
                digest["full_card_bytes"] = ref_size(entity_ref)
            relationship_ref = entity.get("relationship_ref")
            if isinstance(relationship_ref, str):
                digest["relationship_ref"] = relationship_ref
                relationship_path = campaign_root.parent.parent / relationship_ref
                if relationship_path.exists():
                    relationship = load_yaml(relationship_path)
                    digest["relationship_last_event_id"] = relationship.get("last_event_id")
                else:
                    digest["relationship_missing"] = True
            lifecycle = entity.get("lifecycle")
            if isinstance(lifecycle, dict):
                digest["card_last_confirmed_event_id"] = lifecycle.get("last_confirmed_event_id")
            else:
                digest["card_has_no_lifecycle"] = True
            participants.append(digest)
            continue
        participants.append({"id": participant_id, "missing_card": True})

    brief: dict[str, Any] = {
        "campaign": campaign.get("id"),
        "status": campaign.get("status"),
        "rules": ["AGENTS.md", *context.get("always_load", [])],
        "scene": {
            "id": scene.get("scene_id"),
            "location_ref": scene.get("location_ref"),
            "tension": (scene.get("tension") or {}).get("level"),
            "pressures": scene.get("pressures", []),
            "immediate_questions": scene.get("immediate_questions", []),
            "pending_world_reactions": [
                item.get("id")
                for item in scene.get("pending_world_reactions", [])
                if isinstance(item, dict)
            ],
        },
        "time": {
            "current_datetime": time_doc.get("current_datetime"),
            "elapsed_seconds_total": time_doc.get("elapsed_seconds_total"),
            "campaign_phase": time_doc.get("campaign_phase"),
            "roll_policy": (time_doc.get("roll_policy") or {}).get("mode"),
            "roll_policy_until": (time_doc.get("roll_policy") or {}).get("until"),
        },
        "clocks": [
            {
                "id": clock.get("id"),
                "progress": f"{clock.get('progress', 0)}/{clock.get('threshold')}",
                "effect": clock.get("effect"),
            }
            for clock in clocks_doc.get("clocks", [])
            if isinstance(clock, dict) and not clock.get("triggered")
        ],
        "current_scope": interlude_scope_digest(objectives.get("current_interlude_scope", {})),
        "objectives": [
            objective_digest(objective)
            for objective in objectives.get("player_declared", [])
            if isinstance(objective, dict)
        ],
        "obligations": [
            {
                key: obligation.get(key)
                for key in ("id", "status", "commitment")
                if obligation.get(key) is not None
            }
            for obligation in obligations.get("obligations", [])
            if isinstance(obligation, dict)
        ],
        "participants": participants,
        "participant_refs": list(dict.fromkeys(participant_refs)),
        "load": [
            {"ref": ref, "bytes": ref_path(ref).stat().st_size}
            for ref in context.get("active_refs", [])
            if ref_path(ref).exists()
        ],
        "context_bytes": context.get("context_bytes"),
        "context_budget_bytes": context.get("context_budget_bytes"),
        "context_warnings": context.get("context_warnings", []),
        "last_event_id": scene.get("last_event_id"),
    }
    if full:
        # For a browser chat with no filesystem: inline everything to paste once.
        brief["documents"] = [
            {"ref": ref, "content": ref_path(ref).read_text(encoding="utf-8-sig")}
            for ref in list(dict.fromkeys(
                list(context.get("always_load", []))
                + list(context.get("active_refs", []))
                + participant_refs
            ))
            if ref_path(ref).exists()
        ]
    return brief


def load_input(path: Path) -> dict[str, Any]:
    return load_yaml(path)


def load_json_input(value: str, label: str) -> dict[str, Any]:
    try:
        document = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} must be valid JSON: {exc.msg}") from exc
    if not isinstance(document, dict):
        raise RuntimeError(f"{label} JSON root must be an object")
    return document


def add_structured_input(parser: argparse.ArgumentParser, name: str) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(f"--{name}", type=Path)
    group.add_argument(f"--{name}-json", dest=f"{name}_json")


def input_from_args(args: argparse.Namespace, name: str) -> dict[str, Any]:
    inline = getattr(args, f"{name}_json", None)
    if inline is not None:
        return load_json_input(inline, f"--{name}-json")
    return load_input(getattr(args, name))


def add_campaign_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--campaign-root", type=Path, default=DEFAULT_CAMPAIGN_ROOT)


def add_noncanonical(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--allow-noncanonical", action="store_true")


def add_verbose(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the whole document instead of the decision summary.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GameMaster transactional campaign runtime")
    commands = parser.add_subparsers(dest="command", required=True)

    turn = commands.add_parser("turn")
    turn_commands = turn.add_subparsers(dest="turn_command", required=True)
    for name in ("preview", "resolve"):
        item = turn_commands.add_parser(name)
        add_structured_input(item, "request")
        add_campaign_root(item)
        add_verbose(item)
        if name == "resolve":
            add_noncanonical(item)
    commit = turn_commands.add_parser("commit")
    commit.add_argument("turn_id")
    add_structured_input(commit, "outcome")
    add_campaign_root(commit)
    add_noncanonical(commit)
    add_verbose(commit)
    abort = turn_commands.add_parser("abort")
    abort.add_argument("turn_id")
    abort.add_argument("--reason", required=True)
    add_campaign_root(abort)
    add_noncanonical(abort)
    add_verbose(abort)
    recover = turn_commands.add_parser("recover")
    recover.add_argument("turn_id")
    add_campaign_root(recover)
    add_noncanonical(recover)
    add_verbose(recover)

    brief = commands.add_parser("brief", help="One-block opening for a fresh conversation")
    brief.add_argument(
        "--full",
        action="store_true",
        help="Inline every referenced document, for a chat with no filesystem.",
    )
    add_campaign_root(brief)

    context = commands.add_parser("context")
    context_commands = context.add_subparsers(dest="context_command", required=True)
    refresh = context_commands.add_parser("refresh")
    refresh.add_argument("--dry-run", action="store_true")
    refresh.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the context is over budget or a ref is missing.",
    )
    add_campaign_root(refresh)
    add_verbose(refresh)

    plan = context_commands.add_parser(
        "plan", help="Dokladna lista plikow na ture o podanych tagach sytuacji (etap 6)")
    plan.add_argument("--tag", action="append", default=[],
                      help="tag sytuacji, np. testing, choosing_a_plan, time_matters")
    add_campaign_root(plan)
    add_verbose(plan)

    recent = commands.add_parser(
        "recent", help="Proza ostatnich tur bez protokolu audytowego (tanie otwarcie sesji)")
    recent.add_argument("--limit", type=int, default=4)
    add_campaign_root(recent)
    add_verbose(recent)

    recall_command = commands.add_parser("recall")
    recall_command.add_argument("query")
    recall_command.add_argument("--limit", type=int, default=10)
    add_campaign_root(recall_command)

    scene = commands.add_parser("scene")
    scene_commands = scene.add_subparsers(dest="scene_command", required=True)
    close = scene_commands.add_parser("close")
    close.add_argument("--new-scene-id", required=True)
    close.add_argument("--summary", required=True)
    close.add_argument("--location-ref")
    close.add_argument("--participant", action="append", default=[])
    add_campaign_root(close)
    add_noncanonical(close)

    migration = commands.add_parser("migration")
    migration_commands = migration.add_subparsers(dest="migration_command", required=True)
    migration_status = migration_commands.add_parser("status")
    add_campaign_root(migration_status)
    migration_activate = migration_commands.add_parser("activate")
    migration_activate.add_argument("--manifest", type=Path, required=True)
    migration_activate.add_argument("--dry-run", action="store_true")
    add_campaign_root(migration_activate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    campaign_root = args.campaign_root.resolve()
    verbose = getattr(args, "verbose", False)
    try:
        if args.command == "turn":
            if args.turn_command == "preview":
                result = preview_turn(campaign_root, input_from_args(args, "request"))
                summary = preview_summary(result)
            elif args.turn_command == "resolve":
                result = resolve_turn(campaign_root, input_from_args(args, "request"), args.allow_noncanonical)
                summary = transaction_summary(result)
            elif args.turn_command == "commit":
                result = commit_turn(
                    campaign_root, args.turn_id, input_from_args(args, "outcome"), args.allow_noncanonical
                )
                summary = transaction_summary(result, campaign_root)
            elif args.turn_command == "abort":
                result = abort_turn(campaign_root, args.turn_id, args.reason, args.allow_noncanonical)
                summary = transaction_summary(result)
            else:
                result = recover_turn(campaign_root, args.turn_id, args.allow_noncanonical)
                summary = transaction_summary(result, campaign_root)
            if not verbose:
                result = summary
        elif args.command == "brief":
            result = session_brief(campaign_root, args.full)
        elif args.command == "context":
            if args.context_command == "plan":
                result = context_plan(campaign_root, args.tag)
            else:
                result = refresh_context(
                    campaign_root, write=not args.dry_run, strict=args.strict
                )
                if not verbose:
                    result = context_summary(result)
        elif args.command == "recent":
            result = recent_prose(campaign_root, args.limit)
        elif args.command == "recall":
            result = recall(campaign_root, args.query, args.limit)
        elif args.command == "scene":
            result = close_scene(
                campaign_root,
                args.new_scene_id,
                args.summary,
                args.location_ref,
                args.participant,
                args.allow_noncanonical,
            )
        elif args.command == "migration":
            if args.migration_command == "status":
                result = migration_readiness(campaign_root)
            else:
                result = activate_migration(campaign_root, args.manifest, args.dry_run)
        else:
            raise RuntimeError(f"unsupported command {args.command}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, gm_engine.EngineError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
