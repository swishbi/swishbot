# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""Tests for swishbot CLI."""

import argparse
import re
from pathlib import Path

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


# ─── get_available_agents ─────────────────────────────────────────────


def test_get_available_agents_returns_nonempty():
    agents = cli.get_available_agents()
    assert len(agents) > 0


def test_get_available_agents_has_required_keys():
    agents = cli.get_available_agents()
    for a in agents:
        assert "name" in a
        assert "description" in a


def test_get_available_agents_names_match_files():
    agents = cli.get_available_agents()
    for a in agents:
        agent_file = cli.AGENTS_DIR / f"{a['name']}.md"
        assert agent_file.is_file(), f"Agent file missing: {agent_file}"


def test_get_available_agents_empty_dir(monkeypatch, tmp_path):
    empty_dir = tmp_path / "empty_agents"
    empty_dir.mkdir()
    monkeypatch.setattr(cli, "AGENTS_DIR", empty_dir)
    assert cli.get_available_agents() == []


def test_agent_skills_documented_in_body():
    available_skills = {s["name"] for s in cli.get_available_skills()}
    for f in sorted(cli.AGENTS_DIR.iterdir()):
        if not (f.is_file() and f.suffix == ".md"):
            continue
        content = f.read_text()
        assert "## Skills" in content, f"Agent {f.stem} missing '## Skills' section in body"
        # Validate any skill links in the body point to existing skill dirs
        skill_refs = re.findall(r"\(\.\./skills/([^/]+)/SKILL\.md\)", content)
        for skill in skill_refs:
            assert skill in available_skills, f"Agent {f.stem} references unknown skill '{skill}'"


def test_agent_frontmatter_has_skills_list():
    available_skills = {s["name"] for s in cli.get_available_skills()}
    for f in sorted(cli.AGENTS_DIR.iterdir()):
        if not (f.is_file() and f.suffix == ".md"):
            continue
        content = f.read_text()
        # Extract frontmatter block (between opening and closing ---)
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, f"Agent {f.stem} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        # Must declare skills in frontmatter (block sequence) so Claude Code injects them at startup
        skills_match = re.search(r"^skills:\n((?:[ \t]+-[ \t]+\S+\n?)+)", frontmatter, re.MULTILINE)
        assert skills_match, f"Agent {f.stem} missing 'skills:' block list in frontmatter"
        for skill in re.findall(r"[ \t]+-[ \t]+(\S+)", skills_match.group(1)):
            assert skill in available_skills, f"Agent {f.stem} frontmatter references unknown skill '{skill}'"


def test_agent_descriptions_are_single_line():
    for f in sorted(cli.AGENTS_DIR.iterdir()):
        if not (f.is_file() and f.suffix == ".md"):
            continue
        content = f.read_text()
        match = re.search(r'description:\s*"?([^"\n]+)"?', content)
        assert match, f"Agent {f.stem} missing description"
        desc = match.group(1).strip()
        assert "\n" not in desc, f"Agent {f.stem} description contains newline"


def test_all_agents_have_copyright_footer():
    for f in sorted(cli.AGENTS_DIR.iterdir()):
        if not (f.is_file() and f.suffix == ".md"):
            continue
        content = f.read_text().rstrip()
        assert content.endswith("*Copyright (c) 2026 Swish BI Limited. All rights reserved.*"), (
            f"Agent {f.stem} missing copyright footer"
        )


# ─── skill frontmatter validation ────────────────────────────────────


def test_all_skills_have_copyright_footer():
    for d in sorted(cli.SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if not (d.is_dir() and skill_md.exists()):
            continue
        content = skill_md.read_text().rstrip()
        assert content.endswith("*Copyright (c) 2026 Swish BI Limited. All rights reserved.*"), (
            f"Skill {d.name} missing copyright footer"
        )


def test_skill_descriptions_are_single_line():
    for d in sorted(cli.SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if not (d.is_dir() and skill_md.exists()):
            continue
        content = skill_md.read_text()
        match = re.search(r'description:\s*"?([^"\n]+)"?', content)
        assert match, f"Skill {d.name} missing description"
        desc = match.group(1).strip()
        assert "\n" not in desc, f"Skill {d.name} description contains newline"


def test_skill_frontmatter_has_required_fields():
    for d in sorted(cli.SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if not (d.is_dir() and skill_md.exists()):
            continue
        content = skill_md.read_text()
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        assert fm_match, f"Skill {d.name} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert re.search(r"^name:", frontmatter, re.MULTILINE), f"Skill {d.name} missing 'name' in frontmatter"
        assert re.search(r"^description:", frontmatter, re.MULTILINE), (
            f"Skill {d.name} missing 'description' in frontmatter"
        )


# ─── cmd_list ─────────────────────────────────────────────────────────


def test_cmd_list_prints_skills(capsys):
    args = argparse.Namespace()
    cli.cmd_list(args)
    out = capsys.readouterr().out
    # Should contain at least one known skill name
    skills = cli.get_available_skills()
    assert skills[0]["name"] in out


def test_cmd_list_prints_agents(capsys):
    args = argparse.Namespace()
    cli.cmd_list(args)
    out = capsys.readouterr().out
    assert "Available agents:" in out
    agents = cli.get_available_agents()
    assert agents[0]["name"] in out


def test_cmd_list_empty_skills_and_agents(capsys, monkeypatch, tmp_path):
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()
    empty_agents = tmp_path / "empty_agents"
    empty_agents.mkdir()
    monkeypatch.setattr(cli, "SKILLS_DIR", empty_skills)
    monkeypatch.setattr(cli, "AGENTS_DIR", empty_agents)

    args = argparse.Namespace()
    cli.cmd_list(args)
    out = capsys.readouterr().out
    assert "No skills or agents found." in out


# ─── cmd_install ──────────────────────────────────────────────────────


def test_cmd_install_single_skill(tmp_path):
    skill_name = cli.get_available_skills()[0]["name"]
    args = argparse.Namespace(skills=[skill_name], all=False, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / skill_name
    assert installed.is_dir()
    assert (installed / "SKILL.md").exists()


def test_cmd_install_all(tmp_path):
    args = argparse.Namespace(skills=[], all=True, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    available = cli.get_available_skills()
    for s in available:
        assert (tmp_path / s["name"]).is_dir()


def test_cmd_install_overwrites_existing(tmp_path):
    skill_name = cli.get_available_skills()[0]["name"]
    args = argparse.Namespace(skills=[skill_name], all=False, agent=False, path=str(tmp_path))

    # Install twice — should not raise
    cli.cmd_install(args)
    cli.cmd_install(args)
    assert (tmp_path / skill_name / "SKILL.md").exists()


def test_cmd_install_nonexistent_skill(tmp_path):
    args = argparse.Namespace(skills=["nonexistent-skill"], all=False, agent=False, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


def test_cmd_install_no_skill_no_all(tmp_path):
    args = argparse.Namespace(skills=[], all=False, agent=False, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


def test_cmd_install_copies_workflows(tmp_path):
    args = argparse.Namespace(skills=["dbt"], all=False, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / "dbt"
    assert installed.is_dir()
    assert (installed / "SKILL.md").exists()
    assert (installed / "workflows").is_dir()
    # Verify at least one workflow file was copied (may be in subdirectories)
    workflow_files = list((installed / "workflows").rglob("*.md"))
    assert len(workflow_files) > 0


# ─── cmd_install --agent ──────────────────────────────────────────────


def test_cmd_install_agent_single(tmp_path):
    agent_name = cli.get_available_agents()[0]["name"]
    args = argparse.Namespace(skills=[agent_name], all=False, agent=True, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / f"{agent_name}.md"
    assert installed.is_file()


def test_cmd_install_agent_all(tmp_path):
    args = argparse.Namespace(skills=[], all=True, agent=True, path=str(tmp_path))
    cli.cmd_install(args)

    available = cli.get_available_agents()
    for a in available:
        assert (tmp_path / f"{a['name']}.md").is_file()


def test_cmd_install_agent_overwrites_existing(tmp_path):
    agent_name = cli.get_available_agents()[0]["name"]
    args = argparse.Namespace(skills=[agent_name], all=False, agent=True, path=str(tmp_path))

    cli.cmd_install(args)
    cli.cmd_install(args)
    assert (tmp_path / f"{agent_name}.md").is_file()


def test_cmd_install_agent_nonexistent(tmp_path):
    args = argparse.Namespace(skills=["nonexistent-agent"], all=False, agent=True, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


def test_cmd_install_agent_no_name_no_all(tmp_path):
    args = argparse.Namespace(skills=[], all=False, agent=True, path=str(tmp_path))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_install(args)


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


# ─── cmd_init_project (SECURITY.md) ──────────────────────────────────


def test_cmd_init_project_copies_security_md(tmp_path):
    args = argparse.Namespace(path=str(tmp_path), force=False)
    cli.cmd_init_project(args)

    security_target = tmp_path / "SECURITY.md"
    assert security_target.exists()
    assert security_target.read_text() == cli.SECURITY_MD.read_text()


# ─── cmd_hooks ───────────────────────────────────────────────────────


def test_cmd_hooks_lists_installed_hooks(capsys, tmp_path):
    # Install skills with hooks to tmp_path
    args = argparse.Namespace(skills=["dbt"], all=False, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    hook_args = argparse.Namespace(path=str(tmp_path))
    cli.cmd_hooks(hook_args)
    out = capsys.readouterr().out
    assert "dbt" in out
    assert "PreToolUse" in out


def test_cmd_hooks_no_skills_installed(tmp_path):
    nonexistent = tmp_path / "nonexistent"
    hook_args = argparse.Namespace(path=str(nonexistent))
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_hooks(hook_args)


def test_cmd_hooks_no_hooks_found(capsys, tmp_path):
    # Install a skill without hooks
    skill_dir = tmp_path / "no-hook-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text('---\nname: no-hook-skill\ndescription: "No hooks"\n---\n')

    hook_args = argparse.Namespace(path=str(tmp_path))
    cli.cmd_hooks(hook_args)
    out = capsys.readouterr().out
    assert "No hooks found" in out


def test_cmd_hooks_multiple_skills(capsys, tmp_path):
    # Install multiple skills with hooks
    skills = ["dbt", "dba-security"]
    args = argparse.Namespace(skills=skills, all=False, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    hook_args = argparse.Namespace(path=str(tmp_path))
    cli.cmd_hooks(hook_args)
    out = capsys.readouterr().out
    assert "dbt" in out
    assert "dba-security" in out


# ─── cmd_init_memory ─────────────────────────────────────────────────


def test_cmd_init_memory_scaffolds_directory(tmp_path):
    args = argparse.Namespace(path=str(tmp_path), force=False)
    cli.cmd_init_memory(args)

    memory_dir = tmp_path / ".claude" / "memory"
    assert memory_dir.is_dir()
    assert (memory_dir / "MEMORY.md").exists()
    assert (memory_dir / "modeling-decisions.md").exists()
    assert (memory_dir / "source-catalog.md").exists()
    assert (memory_dir / "conventions.md").exists()


def test_cmd_init_memory_creates_settings_json(tmp_path):
    args = argparse.Namespace(path=str(tmp_path), force=False)
    cli.cmd_init_memory(args)

    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()
    import json

    settings = json.loads(settings_path.read_text())
    assert "hooks" in settings
    assert "Stop" in settings["hooks"]


def test_cmd_init_memory_errors_if_exists(tmp_path):
    memory_dir = tmp_path / ".claude" / "memory"
    memory_dir.mkdir(parents=True)

    args = argparse.Namespace(path=str(tmp_path), force=False)
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_init_memory(args)


def test_cmd_init_memory_force_overwrites(tmp_path):
    memory_dir = tmp_path / ".claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("old content")

    args = argparse.Namespace(path=str(tmp_path), force=True)
    cli.cmd_init_memory(args)

    assert (memory_dir / "MEMORY.md").read_text() != "old content"


def test_cmd_init_memory_preserves_existing_settings(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text('{"existing": true}')

    args = argparse.Namespace(path=str(tmp_path), force=False)
    # Should not overwrite settings.json
    cli.cmd_init_memory(args)

    import json

    settings = json.loads((claude_dir / "settings.json").read_text())
    assert settings == {"existing": True}


# ─── cmd_install copies scripts ──────────────────────────────────────


def test_cmd_install_copies_scripts(tmp_path):
    args = argparse.Namespace(skills=["dba-security"], all=False, agent=False, path=str(tmp_path))
    cli.cmd_install(args)

    installed = tmp_path / "dba-security"
    assert (installed / "scripts").is_dir()
    assert (installed / "scripts" / "validate-sql.sh").exists()


# ─── main (argparse integration) ────────────────────────────────────


# ─── cmd_scaffold ───────────────────────────────────────────────────


def test_cmd_scaffold_creates_structure(tmp_path):
    args = argparse.Namespace(name="test-project", path=str(tmp_path), force=False)
    cli.cmd_scaffold(args)

    project = tmp_path / "test-project"
    assert project.is_dir()
    assert (project / "pyproject.toml").exists()
    assert (project / "dagster_cloud.yaml").exists()
    assert (project / ".devcontainer" / "Dockerfile").exists()
    assert (project / ".devcontainer" / "devcontainer.json").exists()
    assert (project / ".gitignore").exists()
    assert (project / ".env.example").exists()
    assert (project / "ingestion").is_dir()
    assert (project / "transformation").is_dir()
    assert (project / "orchestration").is_dir()
    assert (project / "orchestration" / "definitions.py").exists()
    assert (project / "orchestration" / "defs" / "ingestion" / "dlt" / "component.py").exists()
    assert (project / "orchestration" / "defs" / "transformation" / "dbt" / "defs.yaml").exists()
    assert (project / "orchestration" / "utils" / "environment_helpers.py").exists()
    assert (project / "transformation" / "dbt_project.yml").exists()
    assert (project / "transformation" / "profiles.yml").exists()
    assert (project / "transformation" / "packages.yml").exists()
    assert (project / ".github" / "workflows" / "deploy.yml").exists()
    assert (project / ".github" / "workflows" / "branch_deployments.yml").exists()
    assert (project / ".mcp.json").exists()
    assert (project / ".claude" / "memory" / "MEMORY.md").exists()
    assert (project / ".claude" / "settings.json").exists()


def test_cmd_scaffold_replaces_project_name(tmp_path):
    args = argparse.Namespace(name="my-client", path=str(tmp_path), force=False)
    cli.cmd_scaffold(args)

    project = tmp_path / "my-client"
    pyproject = (project / "pyproject.toml").read_text()
    assert 'name = "my-client"' in pyproject

    dbt_project = (project / "transformation" / "dbt_project.yml").read_text()
    assert "name: my_client" in dbt_project

    dagster_cloud = (project / "dagster_cloud.yaml").read_text()
    assert "location_name: my-client" in dagster_cloud

    devcontainer = (project / ".devcontainer" / "devcontainer.json").read_text()
    assert '"name": "my-client"' in devcontainer

    deploy = (project / ".github" / "workflows" / "deploy.yml").read_text()
    assert "my-client.dagster.plus" in deploy

    branch_deploy = (project / ".github" / "workflows" / "branch_deployments.yml").read_text()
    assert "my-client.dagster.plus" in branch_deploy


def test_cmd_scaffold_creates_init_files(tmp_path):
    args = argparse.Namespace(name="test-project", path=str(tmp_path), force=False)
    cli.cmd_scaffold(args)

    project = tmp_path / "test-project"
    expected_inits = [
        "ingestion/__init__.py",
        "orchestration/__init__.py",
        "orchestration/defs/__init__.py",
        "orchestration/defs/ingestion/__init__.py",
        "orchestration/defs/ingestion/dlt/__init__.py",
        "orchestration/defs/transformation/__init__.py",
        "orchestration/defs/transformation/dbt/__init__.py",
        "orchestration/utils/__init__.py",
        "tests/__init__.py",
    ]
    for init_path in expected_inits:
        assert (project / init_path).exists(), f"Missing __init__.py at {init_path}"


def test_cmd_scaffold_installs_skills_and_agents(tmp_path):
    args = argparse.Namespace(name="test-project", path=str(tmp_path), force=False)
    cli.cmd_scaffold(args)

    project = tmp_path / "test-project"
    skills_dir = project / ".claude" / "skills"
    agents_dir = project / ".claude" / "agents"
    assert skills_dir.is_dir()
    assert agents_dir.is_dir()
    # At least some skills and agents were copied
    assert len(list(skills_dir.iterdir())) > 0
    assert len(list(agents_dir.iterdir())) > 0
    # CLAUDE.md was copied
    assert (project / ".claude" / "CLAUDE.md").exists()


def test_cmd_scaffold_existing_errors(tmp_path):
    target = tmp_path / "test-project"
    target.mkdir()
    args = argparse.Namespace(name="test-project", path=str(tmp_path), force=False)
    with pytest.raises(SystemExit, match="1"):
        cli.cmd_scaffold(args)


def test_cmd_scaffold_force_overwrites(tmp_path):
    target = tmp_path / "test-project"
    target.mkdir()
    (target / "old-file.txt").write_text("old")

    args = argparse.Namespace(name="test-project", path=str(tmp_path), force=True)
    cli.cmd_scaffold(args)

    project = tmp_path / "test-project"
    assert (project / "pyproject.toml").exists()
    assert not (project / "old-file.txt").exists()


# ─── _prompt_scope ───────────────────────────────────────────────────


def test_prompt_scope_returns_project(monkeypatch):
    inputs = iter(["P"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    p = Path("/project/skills")
    g = Path("/global/skills")
    result = cli._prompt_scope(p, g)
    assert result == p


def test_prompt_scope_retries_on_invalid(monkeypatch):
    inputs = iter(["X", "Q", "G"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    p = Path("/project/skills")
    g = Path("/global/skills")
    result = cli._prompt_scope(p, g)
    assert result == g


def test_prompt_scope_eof_exits(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError()))
    with pytest.raises(SystemExit, match="1"):
        cli._prompt_scope(Path("/p"), Path("/g"))


# ─── scope prompt integration (no --path) ───────────────────────────


def test_cmd_install_scope_project(tmp_path, monkeypatch):
    dest = tmp_path / ".claude" / "skills"
    monkeypatch.setattr(cli, "_prompt_scope", lambda *_: dest)
    args = argparse.Namespace(skills=[], all=True, agent=False, path=None)
    cli.cmd_install(args)
    assert (dest / cli.get_available_skills()[0]["name"]).is_dir()


def test_cmd_install_agent_scope_project(tmp_path, monkeypatch):
    dest = tmp_path / ".claude" / "agents"
    monkeypatch.setattr(cli, "_prompt_scope", lambda *_: dest)
    args = argparse.Namespace(skills=[], all=True, agent=True, path=None)
    cli.cmd_install(args)
    assert (dest / f"{cli.get_available_agents()[0]['name']}.md").is_file()


def test_cmd_init_project_scope_project(tmp_path, monkeypatch):
    dest = tmp_path / ".claude"
    monkeypatch.setattr(cli, "_prompt_scope", lambda *_: dest)
    args = argparse.Namespace(path=None, force=False)
    cli.cmd_init_project(args)
    assert (dest / "CLAUDE.md").exists()


def test_cmd_init_memory_scope_project(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "_prompt_scope", lambda *_: tmp_path)
    args = argparse.Namespace(path=None, force=False)
    cli.cmd_init_memory(args)
    assert (tmp_path / ".claude" / "memory" / "MEMORY.md").exists()


# ─── main (argparse integration) ────────────────────────────────────


def test_main_no_args_prints_help(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["swishbot"])
    cli.main()
    out = capsys.readouterr().out
    assert "usage" in out.lower() or "swishbot" in out.lower()
