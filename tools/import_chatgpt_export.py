"""Extract one ChatGPT conversation and normalize its current branch for migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "campaigns" / "lucan" / "migration" / "sources"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_conversations(path: Path) -> list[dict[str, Any]]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            candidates = [
                name for name in archive.namelist() if name.endswith("conversations.json")
            ]
            if not candidates:
                raise ValueError("ZIP does not contain conversations.json")
            if len(candidates) > 1:
                candidates.sort(key=lambda value: (value.count("/"), len(value)))
            with archive.open(candidates[0]) as handle:
                data = json.load(handle)
    else:
        data = json.loads(path.read_text(encoding="utf-8-sig"))

    if isinstance(data, dict) and isinstance(data.get("conversations"), list):
        data = data["conversations"]
    if not isinstance(data, list):
        raise ValueError("Expected a list of conversations")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Every conversation must be a JSON object")
    return data


def conversation_id(conversation: dict[str, Any]) -> str | None:
    value = conversation.get("id") or conversation.get("conversation_id")
    return value if isinstance(value, str) else None


def select_conversation(
    conversations: list[dict[str, Any]], requested_id: str | None, requested_title: str | None
) -> dict[str, Any]:
    if requested_id:
        matches = [item for item in conversations if conversation_id(item) == requested_id]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f"Multiple conversations have id {requested_id}")
    if requested_title:
        matches = [item for item in conversations if item.get("title") == requested_title]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Multiple conversations have title {requested_title!r}; use --conversation-id"
            )
    details = []
    if requested_id:
        details.append(f"id={requested_id}")
    if requested_title:
        details.append(f"title={requested_title!r}")
    raise ValueError(f"Conversation not found ({', '.join(details)})")


def current_branch(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = conversation.get("mapping")
    current = conversation.get("current_node")
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("Conversation has no mapping")
    if not isinstance(current, str) or not current:
        raise ValueError("Conversation has no current_node")

    chain: list[dict[str, Any]] = []
    visited: set[str] = set()
    node_id: str | None = current
    while node_id:
        if node_id in visited:
            raise ValueError(f"Cycle detected at node {node_id}")
        visited.add(node_id)
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            raise ValueError(f"Missing parent node {node_id}")
        chain.append({"node_id": node_id, **node})
        parent = node.get("parent")
        if parent is not None and not isinstance(parent, str):
            raise ValueError(f"Invalid parent for node {node_id}")
        node_id = parent
    chain.reverse()
    return chain


def content_text(content: Any) -> str:
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        text = content.get("text")
        return text if isinstance(text, str) else ""
    rendered: list[str] = []
    for part in parts:
        if isinstance(part, str):
            rendered.append(part)
        elif isinstance(part, dict):
            if isinstance(part.get("text"), str):
                rendered.append(part["text"])
            else:
                kind = part.get("content_type") or part.get("type") or "attachment"
                rendered.append(f"[{kind}]")
    return "\n".join(piece for piece in rendered if piece).strip()


def normalize_messages(chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for branch_index, node in enumerate(chain):
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        if not isinstance(role, str):
            role = "unknown"
        record = {
            "branch_index": branch_index,
            "node_id": node["node_id"],
            "message_id": message.get("id"),
            "parent_node_id": node.get("parent"),
            "role": role,
            "name": author.get("name") if isinstance(author, dict) else None,
            "create_time": message.get("create_time"),
            "update_time": message.get("update_time"),
            "content_type": (
                message.get("content", {}).get("content_type")
                if isinstance(message.get("content"), dict)
                else None
            ),
            "text": content_text(message.get("content")),
            "status": message.get("status"),
            "metadata": message.get("metadata", {}),
        }
        records.append(record)
    return records


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def ensure_output_paths(output: Path, force: bool) -> dict[str, Path]:
    paths = {
        "raw": output / "raw" / "chatgpt-thread.json",
        "jsonl": output / "normalized" / "chatgpt-thread.jsonl",
        "txt": output / "normalized" / "chatgpt-thread.txt",
        "report": output / "import-report.json",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not force:
        rendered = ", ".join(str(path) for path in existing)
        raise ValueError(f"Output already exists; use --force to replace: {rendered}")
    return paths


def transcript_text(conversation: dict[str, Any], records: list[dict[str, Any]]) -> str:
    header = [
        f"Conversation: {conversation.get('title')}",
        f"Conversation ID: {conversation_id(conversation)}",
        f"Current branch messages: {len(records)}",
        "",
    ]
    body: list[str] = []
    for record in records:
        body.append(
            f"[{record['branch_index']:04d}] [{record['role'].upper()}] "
            f"node={record['node_id']} message={record['message_id']}"
        )
        body.append(record["text"] or "[NO TEXT CONTENT]")
        body.append("")
    return "\n".join(header + body).rstrip() + "\n"


def completeness_report(
    conversation: dict[str, Any],
    records: list[dict[str, Any]],
    input_path: Path,
    expected_min_messages: int,
) -> dict[str, Any]:
    combined = "\n".join(record["text"] for record in records).casefold()
    checks = {
        "message_count": {
            "observed": len(records),
            "expected_minimum": expected_min_messages,
            "pass": len(records) >= expected_min_messages,
        },
        "campaign_start_marker": {
            "marker": "hi, i'm mindy",
            "pass": "hi, i'm mindy" in combined,
        },
        "oren_marker": {"marker": "oren", "pass": "oren" in combined},
        "varkhen_marker": {"marker": "varkhen", "pass": "varkhen" in combined},
        "current_branch_resolved": {"pass": True},
    }
    return {
        "schema_version": 1,
        "imported_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "input": {
            "path": str(input_path.resolve()),
            "sha256": sha256_file(input_path),
        },
        "conversation": {
            "id": conversation_id(conversation),
            "title": conversation.get("title"),
            "current_node": conversation.get("current_node"),
            "mapping_nodes": len(conversation.get("mapping", {})),
            "current_branch_messages": len(records),
        },
        "checks": checks,
        "passes_automatic_completeness_gate": all(
            item["pass"] for item in checks.values()
        ),
        "manual_review_required": [
            "Confirm that this is the visible campaign branch.",
            "Locate and approve the successful takeover of Varkhen as canonical cutoff.",
            "Split all later material into the noncanonical branch.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract one ChatGPT conversation from a data export."
    )
    parser.add_argument("input", type=Path, help="ChatGPT export ZIP or conversations.json")
    parser.add_argument("--conversation-id", default=None)
    parser.add_argument("--title", default="E-rank Warlock Historia")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-min-messages", type=int, default=800)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file does not exist: {input_path}")
    try:
        conversations = load_conversations(input_path)
        conversation = select_conversation(conversations, args.conversation_id, args.title)
        chain = current_branch(conversation)
        records = normalize_messages(chain)
        if not records:
            raise ValueError("Current branch contains no messages")
        output_paths = ensure_output_paths(args.output.resolve(), args.force)
        report = completeness_report(
            conversation, records, input_path, args.expected_min_messages
        )
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc)) from exc

    atomic_write(
        output_paths["raw"],
        json.dumps(conversation, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write(
        output_paths["jsonl"],
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
    )
    atomic_write(output_paths["txt"], transcript_text(conversation, records))
    atomic_write(
        output_paths["report"], json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passes_automatic_completeness_gate"]:
        print("Automatic completeness gate FAILED; migration must remain blocked.")
        return 2
    print("Automatic completeness gate passed; manual cutoff review is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

