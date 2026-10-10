"""Readability of the plain-English guides, measured with textstat.

Two deliberate choices:

* Tables, code blocks and link targets are stripped before scoring. A definition
  table is not prose, and scoring it produces a number that says nothing useful.
* Pages missing from this checkout return ``None`` and are reported as "not
  measured" rather than silently passing, so a renamed page cannot quietly drop
  out of the gate.

Flesch reading ease: higher is easier. 50 is the spec's target for the
literacy guides; the measured value for every page is printed, pass or fail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import textstat
from config import LITERACY_PAGES, READABILITY_TARGET

_FENCE = "~~~P20FENCE~~~"
_TABLE_ROW_START = ("|", "|-", "|:", "- ", ":-")
_HEADING = "#"
_LINK_TARGET = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")


@dataclass(frozen=True)
class ReadabilityScore:
    page: str
    flesch: float | None
    words: int
    sentences: int
    present: bool

    @property
    def meets_target(self) -> bool:
        return self.flesch is not None and self.flesch >= READABILITY_TARGET


def prose_only(text: str) -> str:
    """Strip the parts of a Markdown page that are not prose."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith(_FENCE):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            continue
        if stripped.startswith(_TABLE_ROW_START):
            continue
        if stripped.startswith(_HEADING):
            continue
        # Keep the words a reader sees, drop the link target and its syntax.
        line = _LINK_TARGET.sub(r"\1", line)
        line = line.replace("**", "").replace("`", "").replace("*", "")
        out.append(line)
    return "\n".join(out)


def score_text(text: str) -> tuple[float, int, int]:
    prose = prose_only(text)
    words = textstat.lexicon_count(prose, removepunct=True)
    sentences = max(1, textstat.sentence_count(prose))
    return float(textstat.flesch_reading_ease(prose)), int(words), sentences


def score_file(path: Path, label: str | None = None) -> ReadabilityScore:
    """Score one page. ``label`` is what the report calls it, so paths stay short."""
    rel = label or path.as_posix()
    if not path.is_file():
        return ReadabilityScore(page=rel, flesch=None, words=0, sentences=0, present=False)
    flesch, words, sentences = score_text(path.read_text(encoding="utf-8"))
    return ReadabilityScore(page=rel, flesch=flesch, words=words, sentences=sentences, present=True)


def score_literacy_pages(project_dir: Path, pages: tuple[str, ...] = LITERACY_PAGES) -> list[ReadabilityScore]:
    return [score_file(project_dir / rel, label=rel) for rel in pages]


def summarise(scores: list[ReadabilityScore]) -> dict[str, float | int | None]:
    measured = [s.flesch for s in scores if s.flesch is not None]
    return {
        "pages": len(scores),
        "measured": len(measured),
        "min": min(measured) if measured else None,
        "mean": round(sum(measured) / len(measured), 1) if measured else None,
        "max": max(measured) if measured else None,
        "below_target": sum(1 for s in scores if not s.meets_target),
    }
