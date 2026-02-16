# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""Tests for swishbot CLI."""

import argparse

import pytest

from swishbot import cli

# ─── get_available_skills ─────────────────────────────────────────────


def test_get_available_skills_returns_nonempty():
    skills = cli.get_available_skills()
    assert len(skills) > 0


def test_get_available_skills_has_required_keys():
    skills = cli.get_available_skills()
    for s in skills:
        assert "name" in s
        assert "description" in s


def test_get_available_skills_names_match_dirs():
    skills = cli.get_available_skills()
    for s in skills:
        skill_dir = cli.SKILLS_DIR / s["name"]
        assert skill_dir.is_dir(), f"Skill dir missing: {skill_dir}"


# ─── cmd_list ─────────────────────────────────────────────────────────


def test_cmd_list_prints_skills(capsys):
    args = argparse.Namespace()
    cli.cmd_list(args)
    out = capsys.readouterr().out
    # Should contain at least one known skill name
    skills = cli.get_available_skills()
    assert skills[0]["name"] in out


def test_cmd_list_empty_skills(capsys, monkeypatch, tmp_path):
    empty_dir = tmp_path / "empty_skills"
    empty_dir.mkdir()
    monkeypatch.setattr(cli, "SKILLS_DIR", empty_dir)

    args = argparse.Namespace()
    cli.cmd_list(args)
    out = capsys.readouterr().out
    assert "No skills found." in out


# ─── cmd_install ──────────────────────────────────────────────────────


def test_cmd_install_single_skill(tmp_path):
    skill_name = cli.get_available_skills()[0]["name"]
    args = argparse.Namespace(skills=[skill_name], all=False, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / skill_name
    assert installed.is_dir()
    assert (installed / "SKILL.md").exists()


def test_cmd_install_all(tmp_path):
    args = argparse.Namespace(skills=[], all=True, path=str(tmp_path))
    cli.cmd_install(args)

    available = cli.get_available_skills()
    for s in available:
        assert (tmp_path / s["name"]).is_dir()


def test_cmd_install_overwrites_existing(tmp_path):
    skill_name = cli.get_available_skills()[0]["name"]
    args = argparse.Namespace(skills=[skill_name], all=False, path=str(tmp_path))

    # Install twice — should not raise
    cli.cmd_install(args)
    cli.cmd_install(args)
    assert (tmp_path / skill_name / "SKILL.md").exists()


def test_cmd_install_nonexistent_skill(tmp_path):
    args = argparse.Namespace(skills=["nonexistent-skill"], all=False, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


def test_cmd_install_no_skill_no_all(tmp_path):
    args = argparse.Namespace(skills=[], all=False, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


def test_cmd_install_copies_workflows(tmp_path):
    args = argparse.Namespace(skills=["dbt-staging"], all=False, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / "dbt-staging"
    assert installed.is_dir()
    assert (installed / "SKILL.md").exists()
    assert (installed / "workflows").is_dir()
    # Verify at least one workflow file was copied
    workflow_files = list((installed / "workflows").glob("*.md"))
    assert len(workflow_files) > 0


# ─── cmd_init ─────────────────────────────────────────────────────────


def test_cmd_init_scaffolds_skill(monkeypatch, tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)

    args = argparse.Namespace(name="my-new-skill")
    cli.cmd_init(args)

    skill_md = skills_dir / "my-new-skill" / "SKILL.md"
    assert skill_md.exists()
    content = skill_md.read_text()
    assert "my-new-skill" in content
    assert "My New Skill" in content


def test_cmd_init_creates_workflows_dir(monkeypatch, tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)

    args = argparse.Namespace(name="test-skill")
    cli.cmd_init(args)

    workflows_dir = skills_dir / "test-skill" / "workflows"
    assert workflows_dir.is_dir()


def test_cmd_init_existing_skill_errors(monkeypatch, tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "existing").mkdir()
    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)

    args = argparse.Namespace(name="existing")
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_init(args)


# ─── cmd_init_project ────────────────────────────────────────────────


def test_cmd_init_project_copies_claude_md(tmp_path):
    args = argparse.Namespace(path=str(tmp_path), force=False)
    cli.cmd_init_project(args)

    target = tmp_path / "CLAUDE.md"
    assert target.exists()
    assert target.read_text() == cli.CLAUDE_MD.read_text()


def test_cmd_init_project_errors_if_exists(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("existing")
    args = argparse.Namespace(path=str(tmp_path), force=False)
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_init_project(args)


def test_cmd_init_project_force_overwrites(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("old content")
    args = argparse.Namespace(path=str(tmp_path), force=True)
    cli.cmd_init_project(args)

    target = tmp_path / "CLAUDE.md"
    assert target.read_text() == cli.CLAUDE_MD.read_text()


# ─── main (argparse integration) ────────────────────────────────────


def test_main_no_args_prints_help(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["swishbot"])
    cli.main()
    out = capsys.readouterr().out
    assert "usage" in out.lower() or "swishbot" in out.lower()
