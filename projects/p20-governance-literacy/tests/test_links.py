"""In-site link and anchor checker: fixtures first, then the real site."""

from __future__ import annotations

from pathlib import Path

import checks
import links


def test_slugify_matches_markdown_toc() -> None:
    assert links.slugify("How to read our dashboards") == "how-to-read-our-dashboards"
    assert links.slugify("Data quality scorecard") == "data-quality-scorecard"
    assert links.slugify("Rule (2): escalation") == "rule-2-escalation"


def test_anchors_ignores_fenced_code() -> None:
    text = "# Real heading\n\n```\n# not a heading\n```\n\n## Second one {.focus}\n"
    assert links.anchors_in(text) == {"real-heading", "second-one"}


def test_clean_site_has_no_problems(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "index.md").write_text("# Home\n\nSee [the other page](sub/page.md#its-heading).\n", encoding="utf-8")
    (tmp_path / "sub" / "page.md").write_text(
        "# Page\n\n## Its heading\n\nBack [home](../index.md).\n", encoding="utf-8"
    )
    report = links.check_site(tmp_path)
    assert report.ok
    assert report.checked_links == 2
    assert report.external_links == 0


def test_missing_file_is_reported(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("[gone](missing.md)\n", encoding="utf-8")
    report = links.check_site(tmp_path)
    assert not report.ok
    assert "no such file" in report.problems[0].reason
    assert report.problems[0].line == 1


def test_missing_anchor_is_reported(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("[x](a.md#nope)\n", encoding="utf-8")
    report = links.check_site(tmp_path)
    assert not report.ok
    assert "no heading anchor" in report.problems[0].reason


def test_link_outside_docs_dir_is_reported(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "outside.md").write_text("x\n", encoding="utf-8")
    (docs / "a.md").write_text("[out](../outside.md)\n", encoding="utf-8")
    report = links.check_site(docs)
    assert not report.ok
    assert "outside the site docs_dir" in report.problems[0].reason


def test_external_links_are_counted_not_checked(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("[site](https://example.invalid/x) and [mail](mailto:a@b.c)\n", encoding="utf-8")
    report = links.check_site(tmp_path)
    assert report.ok
    assert report.external_links == 2
    assert report.checked_links == 0


def test_links_inside_code_fences_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("```text\n[not a link](missing.md)\n```\n", encoding="utf-8")
    assert links.check_site(tmp_path).ok


def test_image_links_are_checked(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("![shot](img/shot.png)\n", encoding="utf-8")
    assert not links.check_site(tmp_path).ok


def test_real_site_links_resolve() -> None:
    report = links.check_site(checks.PROJECT_DIR / "docs")
    assert report.problems == []
    assert report.checked_links > 50
