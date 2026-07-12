from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def test_canonical_documentation_layout_has_no_legacy_duplicates() -> None:
    required = {
        ROOT / "README.md",
        ROOT / "docs" / "authority.md",
        ROOT / "docs" / "ga-comparison.md",
        ROOT / "docs" / "telemetry-artifacts.md",
        ROOT / "benchmarks" / "cases" / "README.md",
    }
    removed = {
        ROOT / "EVALUATION.md",
        ROOT / "docs" / "dashboard-data-contract.md",
        ROOT / "docs" / "solution-metrics-presentation-boundary.md",
    }

    assert all(path.is_file() for path in required)
    assert not any(path.exists() for path in removed)


def test_markdown_relative_links_resolve_within_benchmark_repository() -> None:
    for document in ROOT.rglob("*.md"):
        for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8-sig")):
            assert (document.parent / target).is_file(), f"broken Markdown link: {document} -> {target}"


def test_user_documentation_does_not_require_parent_repository_docs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "../docs/" not in readme
    assert "parent checkout" not in readme
    assert "OptAgent source repository is not required" in readme


def test_user_commands_use_the_single_repository_entrypoint() -> None:
    documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    text = "\n".join(path.read_text(encoding="utf-8") for path in documents)

    assert "PYTHONPATH" not in text
    assert "python -m benchmarks." not in text
    assert "benchmark.py" in text


def test_repository_root_exposes_only_the_primary_python_script() -> None:
    assert [path.name for path in ROOT.glob("*.py")] == ["benchmark.py"]
