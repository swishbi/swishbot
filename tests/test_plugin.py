# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""Tests for swishbot Claude Code plugin structure."""

import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "swishbot"
SKILLS_DIR = PLUGIN_ROOT / "skills"
AGENTS_DIR = PLUGIN_ROOT / "agents"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
HOOKS_DIR = PLUGIN_ROOT / "hooks"
TEMPLATES_DIR = PLUGIN_ROOT / "templates"
MARKETPLACE_ROOT = Path(__file__).resolve().parents[1] / ".claude-plugin"


# ─── plugin manifest ────────────────────────────────────────────────


def test_plugin_json_exists():
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists(), "plugin.json not found"


def test_plugin_json_has_required_fields():
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    for field in ("name", "version", "description"):
        assert field in data, f"plugin.json missing '{field}'"


def test_plugin_json_version_is_semver():
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert re.match(r"^\d+\.\d+\.\d+$", data["version"]), f"Version '{data['version']}' is not semver"


# ─── marketplace ─────────────────────────────────────────────────────


def test_marketplace_json_exists():
    marketplace_json = MARKETPLACE_ROOT / "marketplace.json"
    assert marketplace_json.exists(), "marketplace.json not found"


def test_marketplace_json_references_plugin():
    marketplace_json = MARKETPLACE_ROOT / "marketplace.json"
    data = json.loads(marketplace_json.read_text())
    assert "plugins" in data
    assert len(data["plugins"]) > 0
    plugin_entry = data["plugins"][0]
    assert plugin_entry["name"] == "swishbot"
    # Verify the source resolves to the actual plugin directory
    plugin_path = (MARKETPLACE_ROOT.parent / plugin_entry["source"]).resolve()
    assert plugin_path.exists(), f"Plugin source {plugin_entry['source']} does not resolve"


# ─── skills ──────────────────────────────────────────────────────────


def _get_skills() -> list[Path]:
    return sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists())


def test_skills_exist():
    skills = _get_skills()
    assert len(skills) >= 8, f"Expected at least 8 skills, found {len(skills)}"


def test_skill_frontmatter_has_required_fields():
    for skill_dir in _get_skills():
        content = (skill_dir / "SKILL.md").read_text()
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        assert fm_match, f"Skill {skill_dir.name} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert re.search(r"^name:", frontmatter, re.MULTILINE), f"Skill {skill_dir.name} missing 'name'"
        assert re.search(r"^description:", frontmatter, re.MULTILINE), f"Skill {skill_dir.name} missing 'description'"


def test_skill_descriptions_are_single_line():
    for skill_dir in _get_skills():
        content = (skill_dir / "SKILL.md").read_text()
        match = re.search(r'description:\s*"?([^"\n]+)"?', content)
        assert match, f"Skill {skill_dir.name} missing description"
        desc = match.group(1).strip()
        assert "\n" not in desc, f"Skill {skill_dir.name} description contains newline"


def test_all_skills_have_copyright_footer():
    for skill_dir in _get_skills():
        content = (skill_dir / "SKILL.md").read_text().rstrip()
        assert content.endswith("*Copyright (c) 2026 Swish BI Limited. All rights reserved.*"), (
            f"Skill {skill_dir.name} missing copyright footer"
        )


def test_skill_hook_scripts_use_plugin_root():
    """Command hooks in plugin skills must use ${CLAUDE_PLUGIN_ROOT}, not ~/.claude/."""
    for skill_dir in _get_skills():
        content = (skill_dir / "SKILL.md").read_text()
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        frontmatter = fm_match.group(1)
        if "command:" in frontmatter:
            assert "~/.claude/" not in frontmatter, (
                f"Skill {skill_dir.name} uses ~/.claude/ path in hooks — should use ${{CLAUDE_PLUGIN_ROOT}}"
            )


# ─── agents ──────────────────────────────────────────────────────────


def _get_agents() -> list[Path]:
    return sorted(f for f in AGENTS_DIR.iterdir() if f.is_file() and f.suffix == ".md")


def test_agents_exist():
    agents = _get_agents()
    assert len(agents) >= 4, f"Expected at least 4 agents, found {len(agents)}"


def test_agent_frontmatter_has_required_fields():
    for agent_file in _get_agents():
        content = agent_file.read_text()
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, f"Agent {agent_file.stem} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert re.search(r"^name:", frontmatter, re.MULTILINE), f"Agent {agent_file.stem} missing 'name'"
        assert re.search(r"^description:", frontmatter, re.MULTILINE), f"Agent {agent_file.stem} missing 'description'"


def test_agent_descriptions_are_single_line():
    for agent_file in _get_agents():
        content = agent_file.read_text()
        match = re.search(r'description:\s*"?([^"\n]+)"?', content)
        assert match, f"Agent {agent_file.stem} missing description"
        desc = match.group(1).strip()
        assert "\n" not in desc, f"Agent {agent_file.stem} description contains newline"


def test_agent_frontmatter_has_skills_list():
    skill_names = {d.name for d in _get_skills()}
    for agent_file in _get_agents():
        content = agent_file.read_text()
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, f"Agent {agent_file.stem} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        skills_match = re.search(r"^skills:\n((?:[ \t]+-[ \t]+\S+\n?)+)", frontmatter, re.MULTILINE)
        assert skills_match, f"Agent {agent_file.stem} missing 'skills:' block list in frontmatter"
        for skill in re.findall(r"[ \t]+-[ \t]+(\S+)", skills_match.group(1)):
            assert skill in skill_names, f"Agent {agent_file.stem} references unknown skill '{skill}'"


def test_agent_skills_documented_in_body():
    skill_names = {d.name for d in _get_skills()}
    for agent_file in _get_agents():
        content = agent_file.read_text()
        assert "## Skills" in content, f"Agent {agent_file.stem} missing '## Skills' section"
        skill_refs = re.findall(r"\(\.\./skills/([^/]+)/SKILL\.md\)", content)
        for skill in skill_refs:
            assert skill in skill_names, f"Agent {agent_file.stem} references unknown skill '{skill}'"


def test_all_agents_have_copyright_footer():
    for agent_file in _get_agents():
        content = agent_file.read_text().rstrip()
        assert content.endswith("*Copyright (c) 2026 Swish BI Limited. All rights reserved.*"), (
            f"Agent {agent_file.stem} missing copyright footer"
        )


# ─── commands ────────────────────────────────────────────────────────


def _get_commands() -> list[Path]:
    return sorted(f for f in COMMANDS_DIR.iterdir() if f.is_file() and f.suffix == ".md")


def test_commands_exist():
    commands = _get_commands()
    assert len(commands) >= 3, f"Expected at least 3 commands, found {len(commands)}"


def test_command_names():
    command_names = {f.stem for f in _get_commands()}
    expected = {"scaffold", "init-project", "init-memory", "migrate"}
    assert expected.issubset(command_names), f"Missing commands: {expected - command_names}"


def test_commands_have_frontmatter():
    for cmd_file in _get_commands():
        content = cmd_file.read_text()
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        assert fm_match, f"Command {cmd_file.stem} missing YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert re.search(r"^name:", frontmatter, re.MULTILINE), f"Command {cmd_file.stem} missing 'name'"
        assert re.search(r"^description:", frontmatter, re.MULTILINE), f"Command {cmd_file.stem} missing 'description'"


def test_commands_have_copyright_footer():
    for cmd_file in _get_commands():
        content = cmd_file.read_text().rstrip()
        assert content.endswith("*Copyright (c) 2026 Swish BI Limited. All rights reserved.*"), (
            f"Command {cmd_file.stem} missing copyright footer"
        )


# ─── hooks ───────────────────────────────────────────────────────────


def test_hooks_json_exists():
    hooks_json = HOOKS_DIR / "hooks.json"
    assert hooks_json.exists(), "hooks.json not found"


def test_hooks_json_is_valid():
    hooks_json = HOOKS_DIR / "hooks.json"
    data = json.loads(hooks_json.read_text())
    assert "hooks" in data
    # Must have at least PreToolUse and PostToolUse
    assert "PreToolUse" in data["hooks"]
    assert "PostToolUse" in data["hooks"]
    assert "Stop" in data["hooks"]


def test_hooks_scripts_use_plugin_root():
    """All command hooks must use ${CLAUDE_PLUGIN_ROOT} paths."""
    hooks_json = HOOKS_DIR / "hooks.json"
    data = json.loads(hooks_json.read_text())
    for event, entries in data["hooks"].items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook.get("command", "")
                    assert "${CLAUDE_PLUGIN_ROOT}" in cmd, f"Hook command '{cmd}' doesn't use ${{CLAUDE_PLUGIN_ROOT}}"
                    assert "~/.claude/" not in cmd, f"Hook command '{cmd}' uses ~/.claude/ — should use plugin root"


def test_hooks_reference_existing_scripts():
    """All script paths in hooks.json must point to files that exist."""
    hooks_json = HOOKS_DIR / "hooks.json"
    data = json.loads(hooks_json.read_text())
    for event, entries in data["hooks"].items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook["command"]
                    # Replace ${CLAUDE_PLUGIN_ROOT} with actual plugin root for validation
                    resolved = cmd.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))
                    assert Path(resolved).exists(), f"Hook script not found: {cmd} (resolved: {resolved})"


# ─── mcp ─────────────────────────────────────────────────────────────


def test_mcp_json_exists():
    mcp_json = PLUGIN_ROOT / ".mcp.json"
    assert mcp_json.exists(), ".mcp.json not found"


def test_mcp_json_has_servers():
    mcp_json = PLUGIN_ROOT / ".mcp.json"
    data = json.loads(mcp_json.read_text())
    assert "mcpServers" in data
    expected_servers = {"dbt", "dagster-dg-cli", "dlt", "powerbi-modeling", "powerbi-remote"}
    actual_servers = set(data["mcpServers"].keys())
    assert expected_servers.issubset(actual_servers), f"Missing MCP servers: {expected_servers - actual_servers}"


# ─── templates ───────────────────────────────────────────────────────


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), "templates/ directory not found"


def test_scaffold_templates_present():
    """Key scaffold template files must exist."""
    expected = [
        "pyproject.toml",
        "dagster_cloud.yaml",
        "gitignore",
        "env.example",
        "mcp.json",
    ]
    for name in expected:
        assert (TEMPLATES_DIR / name).exists(), f"Template file missing: {name}"


def test_memory_templates_present():
    memory_dir = TEMPLATES_DIR / "memory"
    assert memory_dir.is_dir(), "templates/memory/ directory not found"
    expected = ["MEMORY.md", "conventions.md", "modeling-decisions.md", "source-catalog.md"]
    for name in expected:
        assert (memory_dir / name).exists(), f"Memory template missing: {name}"


# ─── project-level files ────────────────────────────────────────────


def test_plugin_claude_md_exists():
    assert (PLUGIN_ROOT / "CLAUDE.md").exists(), "Plugin CLAUDE.md not found"


def test_plugin_security_md_exists():
    assert (PLUGIN_ROOT / "SECURITY.md").exists(), "Plugin SECURITY.md not found"
