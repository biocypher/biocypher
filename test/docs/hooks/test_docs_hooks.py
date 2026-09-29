"""Tests for dynamic tutorial catalog generation."""

import importlib.util
import sys

from pathlib import Path
from typing import Callable

import pytest

EMPTY_SECTION_COUNT = 3
HOOK_PATH = Path("mkdocs_hooks/docs_hooks.py")


def load_docs_hooks_module():
    """Load the docs hook module directly from its file path.

    Returns:
        The loaded ``docs_hooks`` module object.

    """
    spec = importlib.util.spec_from_file_location("docs_hooks_module", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def docs_hooks():
    """Provide the loaded docs hook module."""
    return load_docs_hooks_module()


@pytest.fixture
def tutorial_root(tmp_path: Path) -> Path:
    """Provide a temporary tutorial root."""
    path = tmp_path / "docs" / "learn" / "tutorials"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def write_markdown(tutorial_root: Path) -> Callable[[str, str], Path]:
    """Write Markdown files under the temporary tutorial root."""

    def _write(relative_path: str, content: str) -> Path:
        path = tutorial_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def populated_tutorial_root(
    tutorial_root: Path,
    write_markdown: Callable[[str, str], Path],
) -> Path:
    """Provide a tutorial tree with representative tagged and ignored pages."""
    write_markdown(
        "beginner.md",
        """---
tags:
  - tutorial
  - beginner
---
# Beginner Tutorial

**What you will do:** Build your first graph.
""",
    )

    write_markdown(
        "nested/advanced.md",
        """---
tags:
  - tutorial
  - advanced
---
# Advanced Tutorial
""",
    )

    write_markdown(
        "ignored.md",
        """---
tags:
  - beginner
---
# Ignored Page
""",
    )

    write_markdown(
        "legacy.md",
        """---
tags:
  - tutorial
  - beginner
  - legacy
---
# Legacy Tutorial

**What you will do:** This should be ignored.
""",
    )

    return tutorial_root


def test_discover_tutorials_groups_entries_by_level(docs_hooks, populated_tutorial_root: Path) -> None:
    """Collect only tagged tutorial pages and group them by difficulty level."""
    grouped_tutorials = docs_hooks.discover_tutorials(populated_tutorial_root)

    assert [entry.title for entry in grouped_tutorials["beginner"]] == [
        "Beginner Tutorial",
    ]
    assert grouped_tutorials["beginner"][0].focus == "Build your first graph."
    assert grouped_tutorials["beginner"][0].relative_path == "beginner.md"

    assert [entry.title for entry in grouped_tutorials["advanced"]] == [
        "Advanced Tutorial",
    ]
    assert grouped_tutorials["advanced"][0].focus == "Tutorial"
    assert grouped_tutorials["advanced"][0].relative_path == "nested/advanced.md"

    assert grouped_tutorials["intermediate"] == []


def test_render_catalog_includes_empty_sections(docs_hooks) -> None:
    """Render all catalog sections, including placeholders for empty levels."""
    markdown = docs_hooks.render_catalog(
        {
            "beginner": [],
            "intermediate": [],
            "advanced": [],
        },
    )

    assert "# Tutorial Catalog" in markdown
    assert "## Beginner" in markdown
    assert "## Intermediate" in markdown
    assert "## Advanced" in markdown
    assert markdown.count("| No tutorials yet | - | - |") == EMPTY_SECTION_COUNT
