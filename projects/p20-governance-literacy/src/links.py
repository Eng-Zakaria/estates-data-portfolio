"""Internal link and anchor checker for the MkDocs site.

``mkdocs build --strict`` already fails on links it cannot resolve, but it does not
check that a heading anchor exists, and it says nothing useful in a report. This
checker walks every Markdown file in the site, resolves relative links and
anchors, and reports each problem with file and line.

Scope is deliberate: only in-site links are resolved. External URLs are counted
and listed, never fetched (CI must not depend on the network), and repository
paths outside this site are written as code spans precisely so they are not
mistaken for links.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LINK = re.compile(r"(?<!!)\[(?P<text>[^\]]*)\]\((?P<target>[^)]+)\)")
IMAGE = re.compile(r"!\[(?P<text>[^\]]*)\]\((?P<target>[^)]+)\)")
CODE_FENCE = re.compile(r"^\s*```")
HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*$")
FOCUS_LINK = re.compile(r"\{\.focus\}")

_EXTERNAL = re.compile(r"^(https?:|mailto:|tel:)")


@dataclass(frozen=True)
class LinkProblem:
    file: str
    line: int
    target: str
    reason: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.target} - {self.reason}"


@dataclass(frozen=True)
class LinkReport:
    problems: list[LinkProblem]
    checked_links: int
    external_links: int

    @property
    def ok(self) -> bool:
        return not self.problems


def slugify(heading: str) -> str:
    """MkDocs (python-markdown toc) slug: lowercase, drop punctuation, spaces to dashes."""
    text = heading.strip().lower()
    text = FOCUS_LINK.sub("", text)
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def anchors_in(text: str) -> set[str]:
    """Anchor slugs available in a Markdown file."""
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            anchors.add(slugify(match.group("text")))
    return anchors


def _iter_links(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        for match in LINK.finditer(stripped):
            out.append((number, match.group("target").strip()))
        for match in IMAGE.finditer(stripped):
            out.append((number, match.group("target").strip()))
    return out


def check_site(docs_dir: Path) -> LinkReport:
    """Resolve every in-site link in ``docs_dir``. Returns problems plus counts."""
    problems: list[LinkProblem] = []
    checked = 0
    external = 0
    anchor_cache: dict[Path, set[str]] = {}

    files = sorted(p for p in docs_dir.rglob("*.md"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(docs_dir).as_posix()
        for number, target in _iter_links(text):
            if _EXTERNAL.match(target):
                external += 1
                continue
            checked += 1
            file_part, _, anchor = target.partition("#")
            target_path = (path.parent / file_part).resolve() if file_part else path.resolve()
            try:
                target_rel = target_path.relative_to(docs_dir.resolve())
            except ValueError:
                problems.append(LinkProblem(rel, number, target, "points outside the site docs_dir"))
                continue
            if not target_path.exists():
                problems.append(LinkProblem(rel, number, target, f"no such file: {target_rel.as_posix()}"))
                continue
            if anchor:
                anchors = anchor_cache.setdefault(target_path, anchors_in(target_path.read_text(encoding="utf-8")))
                if slugify(anchor) not in anchors:
                    problems.append(LinkProblem(rel, number, target, f"no heading anchor #{slugify(anchor)}"))
    return LinkReport(problems=problems, checked_links=checked, external_links=external)