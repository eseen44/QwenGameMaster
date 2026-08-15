from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import import_chatgpt_export as importer  # noqa: E402


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "chatgpt-export-mini.json"


class ImportChatGptExportTests(unittest.TestCase):
    def test_selects_current_branch_and_checks_markers(self) -> None:
        conversations = importer.load_conversations(FIXTURE)
        conversation = importer.select_conversation(
            conversations, "fixture-conversation-id", "E-rank Warlock Historia"
        )
        chain = importer.current_branch(conversation)
        records = importer.normalize_messages(chain)

        self.assertEqual([item["node_id"] for item in records], [
            "node-1", "node-2", "node-3", "node-4"
        ])
        self.assertNotIn("alternative-node", [item["node_id"] for item in records])

        report = importer.completeness_report(conversation, records, FIXTURE, 4)
        self.assertTrue(report["passes_automatic_completeness_gate"])

    def test_missing_parent_is_rejected(self) -> None:
        broken = {
            "current_node": "child",
            "mapping": {
                "child": {"parent": "missing", "children": [], "message": None}
            },
        }
        with self.assertRaisesRegex(ValueError, "Missing parent node"):
            importer.current_branch(broken)


if __name__ == "__main__":
    unittest.main()

