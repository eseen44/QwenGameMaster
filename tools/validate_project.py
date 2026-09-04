"""Validate the GameMaster file project without changing it."""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import yaml

import gm_engine
import gm_runtime


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PATHS = (
    "AGENTS.md",
    "README.md",
    "TODO.md",
    "system/narrator.md",
    "system/tests.md",
    "system/capabilities.md",
    "system/mechanics/scale.yaml",
    "system/locations-and-maps.md",
    "campaigns/lucan/campaign.yaml",
    "campaigns/lucan/context/active.yaml",
    "campaigns/lucan/context/scene.yaml",
    "campaigns/lucan/state/instances/index.yaml",
    "campaigns/lucan/companions/index.yaml",
    "campaigns/lucan/locations/index.yaml",
    "campaigns/lucan/journal/events.jsonl",
    "campaigns/lucan/journal/rolls.jsonl",
    "campaigns/lucan/journal/retcons.jsonl",
    "campaigns/lucan/migration/migration.yaml",
    "campaigns/lucan/migration/sources/manifest.yaml",
    "campaigns/lucan/migration/sources/audit.yaml",
    "campaigns/lucan/migration/packages/index.yaml",
    "campaigns/lucan/migration/approvals/index.yaml",
    "campaigns/lucan/migration/conflicts/index.yaml",
    "templates/location/maps/layout.yaml",
    "templates/location/maps/gm.svg",
    "templates/location/maps/player.svg",
)


def validate_utf8(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        errors.append(f"UTF-8: {path.relative_to(ROOT)}: {exc}")
        return None


def validate_yaml(path: Path, text: str, errors: list[str]) -> dict | None:
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"YAML: {path.relative_to(ROOT)}: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append(f"YAML: {path.relative_to(ROOT)}: root must be a mapping")
        return None
    if "schema_version" not in document:
        errors.append(f"YAML: {path.relative_to(ROOT)}: missing schema_version")
    return document


def validate_json(path: Path, text: str, errors: list[str]) -> None:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"JSON: {path.relative_to(ROOT)}: {exc}")
        return
    if not isinstance(document, dict):
        errors.append(f"JSON: {path.relative_to(ROOT)}: root must be an object")


def validate_layout(path: Path, document: dict, errors: list[str]) -> None:
    zones = document.get("zones", [])
    features = document.get("features", [])
    connections = document.get("connections", [])
    zone_ids = {
        item.get("id") for item in zones if isinstance(item, dict) and item.get("id")
    }
    feature_ids = {
        item.get("id") for item in features if isinstance(item, dict) and item.get("id")
    }
    for feature in features:
        if isinstance(feature, dict) and feature.get("zone_id") not in zone_ids:
            errors.append(
                f"MAP: {path.relative_to(ROOT)}: feature {feature.get('id')} "
                f"references missing zone {feature.get('zone_id')}"
            )
    for connection in connections:
        if isinstance(connection, dict) and connection.get("from_zone") not in zone_ids:
            errors.append(
                f"MAP: {path.relative_to(ROOT)}: connection {connection.get('id')} "
                f"references missing zone {connection.get('from_zone')}"
            )

    discovery_path = path.parent.parent / "discovery.yaml"
    if discovery_path.exists():
        try:
            discovery = yaml.safe_load(discovery_path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, yaml.YAMLError):
            return
        if isinstance(discovery, dict):
            for zone_id in discovery.get("known_zones", []):
                if zone_id not in zone_ids:
                    errors.append(
                        f"MAP: {discovery_path.relative_to(ROOT)}: unknown zone {zone_id}"
                    )
            for feature_id in discovery.get("observed_features", []):
                if feature_id not in feature_ids:
                    errors.append(
                        f"MAP: {discovery_path.relative_to(ROOT)}: unknown feature {feature_id}"
                    )
    player_path = path.parent / "player.svg"
    if player_path.exists():
        try:
            player_text = player_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            player_text = ""
        hidden_ids = [
            item.get("id")
            for item in zones + features + connections
            if isinstance(item, dict) and item.get("player_visible") is False
        ]
        for hidden_id in hidden_ids:
            if isinstance(hidden_id, str) and hidden_id in player_text:
                errors.append(
                    f"MAP: {player_path.relative_to(ROOT)} reveals hidden id {hidden_id}"
                )


def validate_jsonl(path: Path, text: str, errors: list[str]) -> None:
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"JSONL: {path.relative_to(ROOT)}:{line_number}: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(
                f"JSONL: {path.relative_to(ROOT)}:{line_number}: record must be an object"
            )
            continue
        record_id = record.get("id") or record.get("message_id") or record.get("node_id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(
                f"JSONL: {path.relative_to(ROOT)}:{line_number}: missing string id"
            )
        elif record_id in seen_ids:
            errors.append(
                f"JSONL: {path.relative_to(ROOT)}:{line_number}: duplicate id {record_id}"
            )
        else:
            seen_ids.add(record_id)


def load_yaml_path(relative: str, errors: list[str]) -> dict | None:
    path = ROOT / relative
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"MIGRATION: {relative}: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append(f"MIGRATION: {relative}: root must be a mapping")
        return None
    return document


def validate_migration(errors: list[str]) -> None:
    migration = load_yaml_path("campaigns/lucan/migration/migration.yaml", errors)
    manifest = load_yaml_path("campaigns/lucan/migration/sources/manifest.yaml", errors)
    package_index = load_yaml_path("campaigns/lucan/migration/packages/index.yaml", errors)
    approvals_doc = load_yaml_path("campaigns/lucan/migration/approvals/index.yaml", errors)
    active_context = load_yaml_path("campaigns/lucan/context/active.yaml", errors)
    campaign = load_yaml_path("campaigns/lucan/campaign.yaml", errors)
    if None in (migration, manifest, package_index, approvals_doc, active_context, campaign):
        return

    source_entries = manifest.get("sources", [])
    source_ids = [
        item.get("id") for item in source_entries if isinstance(item, dict)
    ]
    if len(source_ids) != len(set(source_ids)) or any(not item for item in source_ids):
        errors.append("MIGRATION: source ids must be non-empty and unique")
    for source_id in manifest.get("priority_order", []):
        if source_id not in source_ids:
            errors.append(f"MIGRATION: priority references missing source {source_id}")

    package_entries = package_index.get("packages", [])
    expected_ids = migration.get("activation", {}).get("required_packages", [])
    package_ids: list[str] = []
    revisions: dict[str, int] = {}
    package_statuses: dict[str, str] = {}
    fact_ids: set[str] = set()

    def validate_source_refs(refs: object, context: str) -> None:
        if not isinstance(refs, list) or not refs:
            errors.append(f"MIGRATION: {context}: source_refs must be a non-empty list")
            return
        for source_ref in refs:
            if not isinstance(source_ref, str):
                errors.append(f"MIGRATION: {context}: source_ref must be a string")
                continue
            source_id = source_ref.split("#", 1)[0]
            if source_id not in source_ids:
                errors.append(
                    f"MIGRATION: {context}: references missing source {source_id}"
                )
    for entry in package_entries:
        if not isinstance(entry, dict):
            errors.append("MIGRATION: every package index entry must be a mapping")
            continue
        package_id = entry.get("id")
        package_ref = entry.get("ref")
        if not isinstance(package_id, str) or not isinstance(package_ref, str):
            errors.append("MIGRATION: package entry requires string id and ref")
            continue
        package_ids.append(package_id)
        package_doc = load_yaml_path(package_ref, errors)
        if package_doc is None:
            continue
        if package_doc.get("package_id") != package_id:
            errors.append(f"MIGRATION: {package_ref}: package_id does not match index")
        revision = package_doc.get("revision")
        if not isinstance(revision, int) or revision < 1:
            errors.append(f"MIGRATION: {package_ref}: revision must be a positive integer")
        else:
            revisions[package_id] = revision
        package_statuses[package_id] = package_doc.get("status")
        for section in ("confirmed", "proposed", "conflicts", "missing"):
            if not isinstance(package_doc.get(section), list):
                errors.append(f"MIGRATION: {package_ref}: {section} must be a list")
        approval = package_doc.get("approval")
        if not isinstance(approval, dict) or approval.get("required") is not True:
            errors.append(f"MIGRATION: {package_ref}: approval is required")
        for section in ("confirmed", "proposed"):
            for fact in package_doc.get(section, []):
                if not isinstance(fact, dict):
                    errors.append(
                        f"MIGRATION: {package_ref}: {section} fact must be a mapping"
                    )
                    continue
                required = (
                    "id", "claim", "category", "source_refs", "confidence",
                    "cutoff_relation", "proposed_target", "package_id", "status",
                )
                missing = [field for field in required if not fact.get(field)]
                if missing:
                    errors.append(
                        f"MIGRATION: {package_ref}: fact {fact.get('id')} missing {', '.join(missing)}"
                    )
                fact_id = fact.get("id")
                if isinstance(fact_id, str):
                    if fact_id in fact_ids:
                        errors.append(f"MIGRATION: duplicate fact id {fact_id}")
                    fact_ids.add(fact_id)
                if fact.get("package_id") != package_id:
                    errors.append(
                        f"MIGRATION: {package_ref}: fact {fact_id} package_id mismatch"
                    )
                validate_source_refs(fact.get("source_refs"), f"{package_ref}:{fact_id}")

        milestones_ref = package_doc.get("milestones_ref")
        if milestones_ref:
            if not isinstance(milestones_ref, str):
                errors.append(f"MIGRATION: {package_ref}: milestones_ref must be a string")
            else:
                milestone_doc = load_yaml_path(milestones_ref, errors)
                if milestone_doc is not None:
                    milestones = milestone_doc.get("milestones", [])
                    if not isinstance(milestones, list) or not milestones:
                        errors.append(f"MIGRATION: {milestones_ref}: milestones must not be empty")
                    else:
                        orders = [item.get("order") for item in milestones if isinstance(item, dict)]
                        ids = [item.get("id") for item in milestones if isinstance(item, dict)]
                        if orders != list(range(1, len(milestones) + 1)):
                            errors.append(f"MIGRATION: {milestones_ref}: orders must be contiguous")
                        if len(ids) != len(set(ids)) or any(not item for item in ids):
                            errors.append(f"MIGRATION: {milestones_ref}: ids must be unique")
                        at_cutoff = [
                            item for item in milestones
                            if isinstance(item, dict) and item.get("cutoff_relation") == "at"
                        ]
                        if len(at_cutoff) != 1 or milestones[-1].get("cutoff_relation") != "at":
                            errors.append(
                                f"MIGRATION: {milestones_ref}: exactly the last milestone must be at cutoff"
                            )
                        for milestone in milestones:
                            if not isinstance(milestone, dict):
                                errors.append(
                                    f"MIGRATION: {milestones_ref}: milestone must be a mapping"
                                )
                                continue
                            if milestone.get("cutoff_relation") == "after":
                                errors.append(
                                    f"MIGRATION: {milestones_ref}: post-cutoff milestone included: {milestone.get('id')}"
                                )
                            validate_source_refs(
                                milestone.get("source_refs"),
                                f"{milestones_ref}:{milestone.get('id')}",
                            )
        for dependency in package_doc.get("depends_on", []):
            if dependency not in expected_ids:
                errors.append(
                    f"MIGRATION: {package_ref}: unknown dependency {dependency}"
                )

    if package_ids != expected_ids:
        errors.append("MIGRATION: package index order must match activation.required_packages")
    if len(package_ids) != len(set(package_ids)):
        errors.append("MIGRATION: package ids must be unique")

    approval_entries = approvals_doc.get("approvals", [])
    approval_ids: list[str] = []
    for approval in approval_entries:
        if not isinstance(approval, dict):
            errors.append("MIGRATION: every approval entry must be a mapping")
            continue
        package_id = approval.get("package_id")
        approval_ids.append(package_id)
        if package_id not in revisions:
            errors.append(f"MIGRATION: approval references missing package {package_id}")
            continue
        if approval.get("revision") != revisions[package_id]:
            errors.append(f"MIGRATION: approval revision mismatch for {package_id}")
        if package_statuses.get(package_id) == "approved" and approval.get("status") != "approved":
            errors.append(f"MIGRATION: approved package lacks approved record: {package_id}")
    if approval_ids != expected_ids:
        errors.append("MIGRATION: approvals order must match required packages")

    candidate_doc = load_yaml_path("campaigns/lucan/migration/candidates/index.yaml", errors)
    if candidate_doc is not None:
        candidate_ids = [
            item.get("id") for item in candidate_doc.get("candidates", [])
            if isinstance(item, dict)
        ]
        if len(candidate_ids) != len(set(candidate_ids)):
            errors.append("MIGRATION: candidate ids must be unique")
        for candidate_id in candidate_ids:
            if candidate_id not in fact_ids:
                errors.append(
                    f"MIGRATION: candidate index references missing fact {candidate_id}"
                )

    active_text = json.dumps(active_context, ensure_ascii=False)
    if "migration/sources" in active_text or "migration/noncanonical" in active_text:
        errors.append("MIGRATION: active context must not load sources or noncanonical branch")
    if migration.get("status", "").startswith("blocked"):
        if migration.get("activation", {}).get("active") is not False:
            errors.append("MIGRATION: blocked migration cannot be active")
        if campaign.get("status") == "active":
            errors.append("MIGRATION: campaign cannot be active while migration is blocked")


def validate_svg(path: Path, text: str, errors: list[str]) -> None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        errors.append(f"SVG: {path.relative_to(ROOT)}: {exc}")
        return
    if not root.tag.endswith("svg"):
        errors.append(f"SVG: {path.relative_to(ROOT)}: root element is not svg")


def validate_mechanics(errors: list[str]) -> None:
    try:
        registry = gm_engine.Registry(
            [
                ROOT / "system" / "mechanics",
                ROOT / "system" / "fixtures" / "vertical-slice",
                ROOT / "campaigns" / "lucan" / "migration" / "mechanics",
            ]
        )
        for error in gm_engine.validate_registry(registry):
            errors.append(f"MECHANICS: {error}")
    except gm_engine.EngineError as exc:
        errors.append(f"MECHANICS: {exc}")


def validate_runtime(errors: list[str]) -> None:
    campaign_root = ROOT / "campaigns" / "lucan"
    index_path = campaign_root / "state" / "instances" / "index.yaml"
    try:
        index = gm_runtime.load_yaml(index_path)
    except gm_runtime.RuntimeError as exc:
        errors.append(f"RUNTIME: {exc}")
        return
    seen: set[str] = set()
    instances: dict[str, dict] = {}
    for entry in index.get("instances", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            errors.append("RUNTIME: instance index entries require id")
            continue
        instance_id = entry["id"]
        if instance_id in seen:
            errors.append(f"RUNTIME: duplicate instance {instance_id}")
        seen.add(instance_id)
        ref = entry.get("ref")
        if not isinstance(ref, str):
            errors.append(f"RUNTIME: instance {instance_id} requires ref")
            continue
        path = gm_runtime.resolve_campaign_ref(campaign_root, ref)
        if not path.exists():
            errors.append(f"RUNTIME: instance {instance_id} references missing {ref}")
            continue
        try:
            instance = gm_runtime.load_yaml(path)
        except gm_runtime.RuntimeError as exc:
            errors.append(f"RUNTIME: {exc}")
            continue
        if instance.get("id") != instance_id or instance.get("object_type") != "entity_instance":
            errors.append(f"RUNTIME: instance identity mismatch in {ref}")
        else:
            instances[instance_id] = instance
        if not isinstance(instance.get("revision"), int) or instance["revision"] < 1:
            errors.append(f"RUNTIME: {instance_id} requires positive revision")
        for pool_id, pool in instance.get("resources", {}).items():
            if not isinstance(pool, dict):
                errors.append(f"RUNTIME: {instance_id}.{pool_id} must be a mapping")
                continue
            current, capacity = pool.get("current"), pool.get("capacity")
            if not isinstance(current, (int, float)) or not isinstance(capacity, (int, float)) or not 0 <= current <= capacity:
                errors.append(f"RUNTIME: {instance_id}.{pool_id} violates 0 <= current <= capacity")
        for condition in instance.get("conditions", []):
            if not isinstance(condition, dict) or not isinstance(condition.get("id"), str):
                errors.append(f"RUNTIME: {instance_id} has condition without id")
            elif not isinstance(condition.get("source_event_id"), str):
                errors.append(f"RUNTIME: {instance_id}.{condition['id']} lacks source_event_id")

    # The active scene is a compact operational record.  These checks catch two
    # errors that YAML/schema validation cannot see: a scene beginning after its
    # current campaign time, and a concealed companion left at a previous location.
    try:
        scene = gm_runtime.load_yaml(campaign_root / "context" / "scene.yaml")
        time_state = gm_runtime.load_yaml(campaign_root / "state" / "time.yaml")
        started_at = scene.get("started_at")
        current_datetime = time_state.get("current_datetime")
        if isinstance(started_at, str) and isinstance(current_datetime, str):
            try:
                if datetime.fromisoformat(started_at) > datetime.fromisoformat(current_datetime):
                    errors.append("RUNTIME: active scene starts after current campaign time")
            except ValueError:
                # Symbolic campaign labels such as day_0_pre_dawn are valid.
                pass
        lucan = instances.get("pc_lucan")
        if lucan:
            lucan_position = lucan.get("position", {})
            for participant_id in scene.get("participants", []):
                participant = instances.get(participant_id)
                if not participant:
                    continue
                position = participant.get("position", {})
                if position.get("formation") == "concealed_with_lucan" and (
                    position.get("location_id") != lucan_position.get("location_id")
                    or position.get("zone_id") != lucan_position.get("zone_id")
                ):
                    errors.append(
                        f"RUNTIME: concealed companion {participant_id} is not at Lucan's position"
                    )
    except gm_runtime.RuntimeError as exc:
        errors.append(f"RUNTIME: active scene: {exc}")

    npc_index = load_yaml_path("campaigns/lucan/entities/npcs/index.yaml", errors)
    if npc_index:
        for entry in npc_index.get("entities", []):
            if not isinstance(entry, dict) or not isinstance(entry.get("ref"), str):
                continue
            npc = load_yaml_path(entry["ref"], errors)
            if npc is None:
                continue
            for fact in npc.get("knowledge", {}).get("confirmed", []):
                if not isinstance(fact, dict) or not isinstance(fact.get("source_event_id"), str):
                    errors.append(f"KNOWLEDGE: {npc.get('id')} confirmed fact lacks source_event_id")
            forbidden = set(npc.get("knowledge", {}).get("forbidden_without_source", []))
            confirmed_ids = {
                fact.get("fact_id") for fact in npc.get("knowledge", {}).get("confirmed", [])
                if isinstance(fact, dict)
            }
            overlap = forbidden.intersection(confirmed_ids)
            if overlap:
                errors.append(f"KNOWLEDGE: {npc.get('id')} confirms forbidden facts {sorted(overlap)}")

    try:
        context = gm_runtime.refresh_context(campaign_root, write=False)
        if context["context_bytes"] > gm_runtime.CONTEXT_BUDGET_BYTES:
            errors.append("RUNTIME: active context exceeds 40 KB")
    except gm_runtime.RuntimeError as exc:
        errors.append(f"RUNTIME: context: {exc}")

    transactions = campaign_root / "journal" / "transactions"
    if transactions.exists():
        for path in transactions.glob("*.yaml"):
            transaction = load_yaml_path(path.relative_to(ROOT).as_posix(), errors)
            if transaction and transaction.get("status") not in {"resolved", "prepared", "committed", "aborted"}:
                errors.append(f"RUNTIME: invalid transaction status in {path.relative_to(ROOT)}")


def turn_number(event_id: object) -> int | None:
    """Numer tury z identyfikatora zdarzenia, np. event_turn_interlude_233 -> 233."""
    if not isinstance(event_id, str):
        return None
    digits = ""
    for chunk in event_id.replace("-", "_").split("_"):
        if chunk.isdigit():
            digits = chunk
    return int(digits) if digits else None


def validate_scene_card_freshness(errors: list[str]) -> None:
    """Karty postaci STOJACYCH W SCENIE musza byc mniej niz 20 tur w tyle.

    To jest udokumentowany tryb awarii retcon_000121: wpis w knowledge.confirmed jest
    ZDARZENIEM, nie stanem biezacym, wiec karta konczaca sie dawno przed biezaca tura zostaje
    przeczytana jako aktualna. Regula stala w narrator.md i powtorzyla sie mimo tego.
    Kontrola dotyczy WYLACZNIE uczestnikow biezacej sceny - te karty beda czytane w tej turze,
    a stan sam sie czysci po dopisaniu faktu. Reszta kart jest raportowana jako uwaga przez
    brief, nie jako blad, zeby walidator nie swiecil na czerwono bez przerwy.
    """
    PROG = 20
    try:
        scene = yaml.safe_load((ROOT / "campaigns/lucan/context/scene.yaml").read_text(encoding="utf-8-sig"))
        npc_index = yaml.safe_load((ROOT / "campaigns/lucan/entities/npcs/index.yaml").read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"FRESHNESS: {exc}")
        return
    if not isinstance(scene, dict) or not isinstance(npc_index, dict):
        return
    current = turn_number(scene.get("last_event_id"))
    if current is None:
        return

    by_id: dict[str, str] = {}
    for item in npc_index.get("entities") or npc_index.get("entries") or []:
        if isinstance(item, dict) and item.get("id") and item.get("ref"):
            by_id[item["id"]] = item["ref"]

    for participant in scene.get("participants") or []:
        npc_id = participant if isinstance(participant, str) else participant.get("id")
        ref = by_id.get(npc_id)
        if not ref:
            continue
        card_path = ROOT / ref
        if not card_path.exists():
            errors.append(f"FRESHNESS: {npc_id} wskazuje na brakujaca karte {ref}")
            continue
        try:
            card = yaml.safe_load(card_path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            errors.append(f"FRESHNESS: {ref}: {exc}")
            continue
        if not isinstance(card, dict):
            continue

        lifecycle = card.get("lifecycle")
        if not isinstance(lifecycle, dict):
            errors.append(
                f"FRESHNESS: {npc_id} stoi w scenie, a jego karta nie ma bloku lifecycle - "
                f"nie da sie stwierdzic, czy jest aktualna ({ref})"
            )
        else:
            seen = turn_number(lifecycle.get("last_confirmed_event_id"))
            if seen is not None and current - seen > PROG:
                errors.append(
                    f"FRESHNESS: {npc_id} stoi w scenie, a jego karta konczy sie na turze {seen} "
                    f"przy biezacej {current} ({current - seen} tur w tyle, prog {PROG}) - "
                    f"traktowac jako niekompletna albo dopisac fakty ({ref})"
                )

        relationship_ref = card.get("relationship_ref")
        if isinstance(relationship_ref, str):
            relationship_path = ROOT / relationship_ref
            if not relationship_path.exists():
                errors.append(f"FRESHNESS: {npc_id} wskazuje na brakujaca karte relacji {relationship_ref}")
                continue
            try:
                relationship = yaml.safe_load(relationship_path.read_text(encoding="utf-8-sig"))
            except (UnicodeDecodeError, yaml.YAMLError) as exc:
                errors.append(f"FRESHNESS: {relationship_ref}: {exc}")
                continue
            seen = turn_number((relationship or {}).get("last_event_id"))
            if seen is not None and current - seen > PROG:
                errors.append(
                    f"FRESHNESS: relacja {npc_id} z Lucanem stoi na turze {seen} przy biezacej "
                    f"{current} ({current - seen} tur w tyle) - osie i axis_change_log sa "
                    f"nieaktualne ({relationship_ref})"
                )


def validate_journal_guard(errors: list[str]) -> None:
    """Kanon dziennika nie moze ginac przy cofaniu tury.

    Regula "bledu historycznego nie kasuj" stala w AGENTS.md od poczatku i nic jej nie
    sprawdzalo, wiec szesc cofnietych tur zostalo usunietych albo nadpisanych, a pierwotna
    proza przetrwala wylacznie jako obiekty gita. tools/journal_guard.py to sprawdza;
    tutaj jest tylko wpiety, zeby chodzil bez proszenia.
    """
    guard = ROOT / "tools" / "journal_guard.py"
    if not guard.exists():
        errors.append("JOURNAL: brak tools/journal_guard.py")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(guard), "--quiet"],
            cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=180,
        )
    except subprocess.TimeoutExpired:
        errors.append("JOURNAL: journal_guard.py nie skonczyl w 180 s")
        return
    if result.returncode:
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("-"):
                errors.append(f"JOURNAL: {line.lstrip('- ').strip()}")
        if not any(e.startswith("JOURNAL:") for e in errors):
            errors.append(f"JOURNAL: journal_guard.py zwrocil {result.returncode}")


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).exists():
            errors.append(f"Missing required path: {relative}")

    counts = {"yaml": 0, "json": 0, "jsonl": 0, "svg": 0, "utf8": 0}
    # Katalogi ignorowane przez gita nie sa projektem i nie wolno ich walidowac.
    # .claude/worktrees/ trzyma nieaktualne kopie calego repo - do 2026-09-04 walidator
    # przechodzil je razem z reszta i zglaszal 1814 dodatkowych plikow YAML oraz dwa bledy
    # skladni z kopii sprzed poprawki. Narzedzie mierzylo wiec stan, ktorego nikt nie edytuje.
    SKIP_DIRS = {".git", ".claude", "__pycache__", ".pytest_cache", ".venv", "node_modules"}
    candidates = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not (SKIP_DIRS & set(path.parts))
    )
    for path in candidates:
        if path.suffix.lower() not in {".md", ".txt", ".yaml", ".jsonl", ".json", ".svg", ".ps1", ".py"}:
            continue
        text = validate_utf8(path, errors)
        if text is None:
            continue
        counts["utf8"] += 1
        suffix = path.suffix.lower()
        if suffix == ".yaml":
            counts["yaml"] += 1
            document = validate_yaml(path, text, errors)
            if document is not None and path.name == "layout.yaml":
                validate_layout(path, document, errors)
        elif suffix == ".json":
            counts["json"] += 1
            validate_json(path, text, errors)
        elif suffix == ".jsonl":
            counts["jsonl"] += 1
            validate_jsonl(path, text, errors)
        elif suffix == ".svg":
            counts["svg"] += 1
            validate_svg(path, text, errors)

    validate_migration(errors)
    validate_mechanics(errors)
    validate_runtime(errors)
    validate_scene_card_freshness(errors)
    validate_journal_guard(errors)

    if errors:
        print("GameMaster validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GameMaster validation OK")
    print(
        f"Checked {counts['utf8']} UTF-8 files, {counts['yaml']} YAML files, "
        f"{counts['json']} JSON examples, {counts['jsonl']} JSONL journals "
        f"and {counts['svg']} SVG maps."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
