"""Readability measurement: fixtures first, then the real literacy pages."""

from __future__ import annotations

from pathlib import Path

import checks
import config
import readability


def test_prose_strips_tables_code_and_headings() -> None:
    text = (
        "# A heading\n"
        "| a | b |\n"
        "|---|---|\n"
        "| 1 | 2 |\n"
        "```python\n"
        "score = 1\n"
        "```\n"
        "This is plain prose. It has a [link text](target.md) in it.\n"
    )
    prose = readability.prose_only(text)
    assert "A heading" not in prose
    assert "| 1 | 2 |" not in prose
    assert "score = 1" not in prose
    assert "link text" in prose
    assert "target.md" not in prose


def test_simple_text_scores_high() -> None:
    flesch, words, sentences = readability.score_text(
        "The cat sat on the mat. The dog ran. We went home. It was a good day.\n"
    )
    assert flesch > 80
    assert words >= 10
    assert sentences >= 3


def test_long_words_lower_the_score() -> None:
    easy = "We look at the room. The room is big. We use the room each day.\n"
    hard = (
        "Institutionalisation characterisation responsibilities implementation "
        "interoperability reconciliation quantisation standardisation methodologies.\n"
    )
    assert readability.score_text(hard)[0] < readability.score_text(easy)[0]


def test_missing_page_is_reported_not_passed(tmp_path: Path) -> None:
    score = readability.score_file(tmp_path / "absent.md", label="docs/absent.md")
    assert not score.present
    assert score.flesch is None
    assert not score.meets_target


def test_summarise_counts() -> None:
    scores = [
        readability.ReadabilityScore("a.md", 80.0, 10, 1, True),
        readability.ReadabilityScore("b.md", 40.0, 10, 1, True),
        readability.ReadabilityScore("c.md", None, 0, 0, False),
    ]
    summary = readability.summarise(scores)
    assert summary["pages"] == 3
    assert summary["measured"] == 2
    assert summary["min"] == 40.0
    assert summary["max"] == 80.0
    assert summary["below_target"] == 2


def test_every_literacy_page_is_measured() -> None:
    scores = readability.score_literacy_pages(checks.PROJECT_DIR, config.LITERACY_PAGES)
    assert [s.page for s in scores] == list(config.LITERACY_PAGES)
    assert all(s.present for s in scores), [s.page for s in scores if not s.present]


def test_literacy_pages_meet_the_target() -> None:
    """The spec's target: Flesch reading ease >= 50 on the plain-English guides."""
    scores = readability.score_literacy_pages(checks.PROJECT_DIR, config.LITERACY_PAGES)
    below = [(s.page, round(s.flesch, 1)) for s in scores if not s.meets_target]  # type: ignore[arg-type]
    assert below == [], below
    summary = readability.summarise(scores)
    assert summary["min"] is not None and summary["min"] >= config.READABILITY_TARGET


def test_generated_pages_are_not_gated() -> None:
    """Technical pages are excluded on purpose; the gate only covers the guides."""
    assert not any(p.startswith("docs/generated") for p in config.LITERACY_PAGES)
