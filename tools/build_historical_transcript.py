"""Build one searchable historical run from the three recovered text logs.

The input files are preserved verbatim under migration/sources/raw.  The
combined transcript contains only story-log material and keeps the full
post-cutoff branch; provenance and the canonical boundary live in a separate
manifest so they do not pollute line-number references.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "campaigns" / "lucan" / "migration" / "sources"

EXPECTED_SHA256 = {
    "In_Character.txt": "46c4ad990e55b4cce76030587bee0c70df63ad7f0ea629c981e1cd753c9df9cf",
    "luka_A.txt": "81ca4e50f9654cd3cc7be438308da36736063712c9b8970f4c2af5fff8a6c130",
    "luka_B.txt": "66f8d13d721bbf6b8114d9b3b91d143837e835daef241825b2b2426377eff0c5",
}

# Inclusive, one-based source ranges selected after overlap analysis.
SEGMENTS = (
    ("In_Character.txt", 1, 1200),
    ("luka_A.txt", 1, 480),
    ("luka_B.txt", 1, 12012),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return text.splitlines()


def write_utf8(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def assert_known_inputs(paths: dict[str, Path]) -> None:
    for name, path in paths.items():
        digest = sha256(path)
        if digest != EXPECTED_SHA256[name]:
            raise SystemExit(f"{name}: unexpected SHA-256 {digest}; expected {EXPECTED_SHA256[name]}")


def assert_overlap(lines: dict[str, list[str]]) -> None:
    # In_Character continues into luka_A after a short unique bridge in A.
    if lines["In_Character.txt"][1202:1211] != lines["luka_A.txt"][80:89]:
        raise SystemExit("In_Character/luka_A overlap check failed")
    # luka_B is luka_A's continuation with two redundant blank lines removed.
    if lines["luka_A.txt"][480:629] != lines["luka_B.txt"][0:149]:
        raise SystemExit("luka_A/luka_B first overlap check failed")
    if lines["luka_A.txt"][631:818] != lines["luka_B.txt"][149:336]:
        raise SystemExit("luka_A/luka_B second overlap check failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path.home() / "Desktop",
        help="Directory containing In_Character.txt, luka_A.txt and luka_B.txt",
    )
    parser.add_argument("--force", action="store_true", help="Replace generated project copies")
    args = parser.parse_args()

    inputs = {name: args.source_dir / name for name in EXPECTED_SHA256}
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise SystemExit("Missing input files: " + ", ".join(missing))
    assert_known_inputs(inputs)

    raw_dir = SOURCE_ROOT / "raw"
    normalized_dir = SOURCE_ROOT / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    generated = [
        *(raw_dir / name for name in inputs),
        *(normalized_dir / name.replace(".txt", ".utf8.txt") for name in inputs),
        normalized_dir / "historical-full-run.utf8.txt",
        normalized_dir / "historical-full-run.manifest.yaml",
    ]
    existing = [path for path in generated if path.exists()]
    if existing and not args.force:
        raise SystemExit("Generated files already exist; pass --force: " + ", ".join(map(str, existing)))

    source_lines = {name: read_lines(path) for name, path in inputs.items()}
    assert_overlap(source_lines)

    for name, path in inputs.items():
        shutil.copyfile(path, raw_dir / name)
        write_utf8(normalized_dir / name.replace(".txt", ".utf8.txt"), source_lines[name])

    combined: list[str] = []
    manifest_segments: list[dict[str, object]] = []
    output_line = 1
    for name, first, last in SEGMENTS:
        selected = source_lines[name][first - 1 : last]
        combined.extend(selected)
        output_last = output_line + len(selected) - 1
        manifest_segments.append(
            {
                "source": name,
                "source_lines": f"{first}-{last}",
                "output_lines": f"{output_line}-{output_last}",
                "selection_reason": {
                    "In_Character.txt": "campaign_start_through_last_unique_early_scene",
                    "luka_A.txt": "unique_bridge_before_luka_B_overlap",
                    "luka_B.txt": "broad_continuation_including_post_cutoff_branch",
                }[name],
            }
        )
        output_line = output_last + 1

    output_path = normalized_dir / "historical-full-run.utf8.txt"
    write_utf8(output_path, combined)

    cutoff_output_line = 1200 + 480 + 11409
    manifest = {
        "schema_version": 1,
        "id": "source_compiled_historical_run",
        "kind": "derived_deduplicated_transcript",
        "path": "campaigns/lucan/migration/sources/normalized/historical-full-run.utf8.txt",
        "sha256": sha256(output_path),
        "lines": len(combined),
        "segments": manifest_segments,
        "canonical_range": f"line:1-{cutoff_output_line}",
        "post_cutoff_range": f"line:{cutoff_output_line + 1}-{len(combined)}",
        "canonical_cutoff_mapping": {
            "compiled_line": cutoff_output_line,
            "source": "luka_B.txt",
            "source_line": 11409,
        },
        "excluded_material": [
            {
                "source": "In_Character.txt",
                "source_lines": "1201-1859",
                "reason": "sampled_later_duplicates_and_meta_discussion",
            },
            {
                "source": "luka_A.txt",
                "source_lines": "481-828",
                "reason": "overlap_with_luka_B_or_trailing_duplicate_snippets",
            },
        ],
        "authority": "inherits_component_sources_no_new_canonical_authority",
        "automatic_context": False,
    }
    manifest_path = normalized_dir / "historical-full-run.manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    print(f"Wrote {output_path} ({len(combined)} lines, {output_path.stat().st_size} bytes)")
    print(f"SHA-256 {manifest['sha256']}")
    print(f"Canonical cutoff: compiled line {cutoff_output_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
