# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""swishbot CLI — Install data stack skills into your Claude environment."""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

CLAUDE_DIR = Path(__file__).parent / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
AGENTS_DIR = CLAUDE_DIR / "agents"
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
SECURITY_MD = CLAUDE_DIR / "SECURITY.md"
MEMORY_TEMPLATES_DIR = Path(__file__).parent / "memory_templates"
SCAFFOLD_TEMPLATES_DIR = Path(__file__).parent / "scaffold_templates"
DEFAULT_INSTALL_PATH = Path.home() / ".claude" / "skills"
DEFAULT_AGENT_INSTALL_PATH = Path.home() / ".claude" / "agents"

SKILL_TEMPLATE = """\
---
name: {name}
description: "[TODO: Describe when to use this skill. Include trigger phrases users would say.]"
---

# {title}

## Overview

[TODO: What this skill does and the methodology behind it.]

## Methodology

[TODO: Your opinionated approach — the reasoning and patterns that
make Claude work the way you would. Focus on the *what* and *why*,
not platform-specific *how*. Claude already knows the platforms;
it needs to know how you think.]

## Patterns

[TODO: Concrete patterns with examples. Show what good output
looks like. Include both the pattern and the reasoning behind it.]

## Anti-Patterns

[TODO: What to avoid. This is often where the most valuable
signal lives — the mistakes you've seen clients make that
Claude should steer away from.]

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
"""


def get_available_skills() -> list[dict]:
    """Return list of available skills with name and description."""
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if d.is_dir() and skill_md.exists():
            content = skill_md.read_text()
            match = re.search(r'description:\s*"?([^"\n]+)"?', content)
            description = match.group(1).strip() if match else "(no description)"
            skills.append({"name": d.name, "description": description})

    return skills


def get_available_agents() -> list[dict]:
    """Return list of available agents with name and description."""
    if not AGENTS_DIR.exists():
        return []

    agents = []
    for d in sorted(AGENTS_DIR.iterdir()):
        agent_md = d / "AGENT.md"
        if d.is_dir() and agent_md.exists():
            content = agent_md.read_text()
            match = re.search(r'description:\s*"?([^"\n]+)"?', content)
            description = match.group(1).strip() if match else "(no description)"
            agents.append({"name": d.name, "description": description})

    return agents


# ─── Commands ────────────────────────────────────────────────────────


def cmd_list(args: argparse.Namespace) -> None:
    """List available skills and agents."""
    skills = get_available_skills()
    agents = get_available_agents()

    if not skills and not agents:
        print("No skills or agents found.")
        return

    if skills:
        max_name = max(len(s["name"]) for s in skills)
        print("\nAvailable skills:\n")
        for s in skills:
            print(f"  {s['name']:<{max_name + 2}} {s['description']}")
        print("\nInstall with: swishbot install <skill-name>")

    if agents:
        max_name = max(len(a["name"]) for a in agents)
        print("\nAvailable agents:\n")
        for a in agents:
            print(f"  {a['name']:<{max_name + 2}} {a['description']}")
        print("\nInstall agent: swishbot install --agent <agent-name>")

    print()


def cmd_install(args: argparse.Namespace) -> None:
    """Install one or more skills or agents."""
    if args.agent:
        _install_agents(args)
    else:
        _install_skills(args)


def _install_skills(args: argparse.Namespace) -> None:
    """Install one or more skills."""
    dest = Path(args.path) if args.path else DEFAULT_INSTALL_PATH
    available = {s["name"] for s in get_available_skills()}

    if args.all:
        names = sorted(available)
    elif args.skills:
        names = args.skills
    else:
        print("Error: specify a skill name or use --all", file=sys.stderr)
        sys.exit(1)

    for name in names:
        if name not in available:
            print(f"Error: skill '{name}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(sorted(available))}", file=sys.stderr)
            sys.exit(1)

        src = SKILLS_DIR / name
        skill_dest = dest / name

        if skill_dest.exists():
            print(f"  ⟳ {name} — already installed, overwriting")
            shutil.rmtree(skill_dest)

        shutil.copytree(src, skill_dest)
        print(f"  ✓ {name} → {skill_dest}")

    print(f"\nDone. Skills installed to {dest}")
    print("Make sure your Claude project references this path.\n")


def _install_agents(args: argparse.Namespace) -> None:
    """Install one or more agents."""
    dest = Path(args.path) if args.path else DEFAULT_AGENT_INSTALL_PATH
    available = {a["name"] for a in get_available_agents()}

    if args.all:
        names = sorted(available)
    elif args.skills:
        names = args.skills
    else:
        print("Error: specify an agent name or use --all", file=sys.stderr)
        sys.exit(1)

    for name in names:
        if name not in available:
            print(f"Error: agent '{name}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(sorted(available))}", file=sys.stderr)
            sys.exit(1)

        src = AGENTS_DIR / name
        agent_dest = dest / name

        if agent_dest.exists():
            print(f"  ⟳ {name} — already installed, overwriting")
            shutil.rmtree(agent_dest)

        shutil.copytree(src, agent_dest)
        print(f"  ✓ {name} → {agent_dest}")

    print(f"\nDone. Agents installed to {dest}")
    print("Make sure your Claude project references this path.\n")


def cmd_init_project(args: argparse.Namespace) -> None:
    """Install a starter CLAUDE.md and SECURITY.md into a project."""
    dest = Path(args.path) if args.path else Path.cwd()
    target = dest / "CLAUDE.md"

    if target.exists() and not args.force:
        print(f"Error: {target} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(CLAUDE_MD, target)
    print(f"\n  ✓ CLAUDE.md → {target}")

    # Copy SECURITY.md if available
    if SECURITY_MD.exists():
        security_target = dest / "SECURITY.md"
        shutil.copy2(SECURITY_MD, security_target)
        print(f"  ✓ SECURITY.md → {security_target}")

    print("\nEdit the file to uncomment your installed skills and fill in project details.\n")


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold a new skill."""
    name = args.name
    dest = SKILLS_DIR / name

    if dest.exists():
        print(f"Error: skill '{name}' already exists at {dest}", file=sys.stderr)
        sys.exit(1)

    dest.mkdir(parents=True)
    (dest / "workflows").mkdir()
    title = " ".join(w.capitalize() for w in name.split("-"))
    (dest / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=name, title=title))

    print(f"\nScaffolded new skill: {dest}/SKILL.md")
    print("Edit the SKILL.md to encode your methodology.\n")


def cmd_hooks(args: argparse.Namespace) -> None:
    """List hooks provided by installed skills."""
    install_path = Path(args.path) if args.path else DEFAULT_INSTALL_PATH
    if not install_path.exists():
        print("No skills installed yet.", file=sys.stderr)
        print("Install skills first: swishbot install --all", file=sys.stderr)
        sys.exit(1)

    hooks_found = []
    for skill_dir in sorted(install_path.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not (skill_dir.is_dir() and skill_md.exists()):
            continue

        content = skill_md.read_text()
        # Extract YAML frontmatter
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        frontmatter = fm_match.group(1)
        if "hooks:" not in frontmatter:
            continue

        # Parse hooks from frontmatter using simple YAML-like extraction
        _parse_hooks_from_frontmatter(skill_dir.name, frontmatter, hooks_found)

    if not hooks_found:
        print("No hooks found in installed skills.")
        return

    max_skill = max(len(h["skill"]) for h in hooks_found)
    max_event = max(len(h["event"]) for h in hooks_found)

    print("\nInstalled hooks:\n")
    for h in hooks_found:
        print(f"  {h['skill']:<{max_skill + 2}} {h['event']:<{max_event + 2}} ({h['matcher']})  {h['description']}")
    print()


def _parse_hooks_from_frontmatter(skill_name: str, frontmatter: str, hooks_found: list) -> None:
    """Extract hook entries from YAML frontmatter text.

    Assumes a single hook per event type per skill. If a skill defines multiple
    hooks under the same event (e.g., two PreToolUse hooks), only the last one
    is captured. This is sufficient for current skills but should be revisited
    if multi-hook-per-event support is needed.
    """
    current_event = None
    current_matcher = None

    for line in frontmatter.split("\n"):
        stripped = line.strip()

        # Detect event type (PreToolUse, PostToolUse, Stop, etc.)
        if re.match(r"^(Pre|Post)ToolUse:", stripped) or re.match(r"^Stop:", stripped):
            current_event = stripped.rstrip(":")

        # Detect matcher
        matcher_match = re.search(r'matcher:\s*"([^"]+)"', stripped)
        if matcher_match:
            current_matcher = matcher_match.group(1)

        # Detect hook type and extract description
        if "type:" in stripped and current_event:
            hook_type = stripped.split("type:")[-1].strip()
            # Look for prompt or command on subsequent lines — use matcher as description base
            desc = f"{hook_type} hook"
            # Try to find a prompt or command line nearby
            prompt_match = re.search(r'prompt:\s*"([^"]{1,60})', frontmatter)
            command_match = re.search(r'command:\s*"([^"]+)"', frontmatter)
            if hook_type == "prompt" and prompt_match:
                desc = prompt_match.group(1).rstrip(".")
                if len(desc) > 55:
                    desc = desc[:55] + "..."
            elif hook_type == "command" and command_match:
                desc = Path(command_match.group(1)).name

            hooks_found.append(
                {
                    "skill": skill_name,
                    "event": current_event,
                    "matcher": current_matcher or "*",
                    "description": desc,
                }
            )


def _scaffold_memory(dest: Path) -> None:
    """Create .claude/memory/ templates and settings.json Stop hook. Idempotent — skips settings.json if it already exists."""
    memory_dir = dest / ".claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    for template in sorted(MEMORY_TEMPLATES_DIR.iterdir()):
        if template.is_file():
            shutil.copy2(template, memory_dir / template.name)
    settings_path = dest / ".claude" / "settings.json"
    if not settings_path.exists():
        settings = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "prompt",
                                "prompt": (
                                    "Review this session. If any data modeling decisions, "
                                    "source configurations, or convention choices were made, "
                                    "update the relevant files in .claude/memory/. Only update "
                                    "if substantive decisions were made — skip routine coding sessions."
                                ),
                                "timeout": 30,
                            }
                        ]
                    }
                ]
            }
        }
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")


def cmd_init_memory(args: argparse.Namespace) -> None:
    """Scaffold project memory directory with templates."""
    dest = Path(args.path) if args.path else Path.cwd()
    memory_dir = dest / ".claude" / "memory"

    if memory_dir.exists() and not args.force:
        print(f"Error: {memory_dir} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    settings_path = dest / ".claude" / "settings.json"
    settings_existed = settings_path.exists()

    _scaffold_memory(dest)

    if settings_existed:
        print(f"  ⟳ {settings_path} already exists — add the Stop hook manually if desired")
    else:
        print(f"  ✓ {settings_path} (session capture hook)")

    print(f"\n  ✓ Memory templates → {memory_dir}")
    files = sorted(f.name for f in memory_dir.iterdir() if f.is_file())
    for f in files:
        print(f"    - {f}")
    print("\nClaude will update these files as decisions are made during sessions.\n")


def _to_snake_case(name: str) -> str:
    """Convert a kebab-case name to snake_case."""
    return name.replace("-", "_").replace(" ", "_").lower()


# File renames: template filename -> target filename
_SCAFFOLD_RENAMES = {
    "gitignore": ".gitignore",
    "env.example": ".env.example",
    "mcp.json": ".mcp.json",
}

# Directory renames: template dir name -> target dir name
_SCAFFOLD_DIR_RENAMES = {
    "devcontainer": ".devcontainer",
    "github": ".github",
}

# Directories that get an __init__.py
_INIT_PY_DIRS = [
    "ingestion",
    "orchestration",
    "orchestration/defs",
    "orchestration/defs/ingestion",
    "orchestration/defs/ingestion/dlt",
    "orchestration/defs/reporting",
    "orchestration/defs/reporting/powerbi",
    "orchestration/defs/transformation",
    "orchestration/defs/transformation/dbt",
    "orchestration/utils",
    "tests",
]

# Empty directories to create
_EMPTY_DIRS = [
    "transformation/models/staging",
    "transformation/models/intermediate",
    "transformation/models/marts",
    "transformation/seeds",
    "transformation/macros",
    "transformation/tests",
]


def cmd_scaffold(args: argparse.Namespace) -> None:
    """Scaffold a new analytics project."""
    project_name = args.name
    project_name_snake = _to_snake_case(project_name)
    target = Path(args.path or ".") / project_name

    if target.exists():
        if not args.force:
            print(f"Error: {target} already exists. Use --force to overwrite.", file=sys.stderr)
            sys.exit(1)
        shutil.rmtree(target)

    # Walk templates and copy with placeholder replacement
    for src_path in sorted(SCAFFOLD_TEMPLATES_DIR.rglob("*")):
        if src_path.is_dir():
            continue

        # Skip __pycache__, .pyc, and hidden directories (e.g. .ruff_cache)
        if any(p.startswith(".") or p == "__pycache__" for p in src_path.relative_to(SCAFFOLD_TEMPLATES_DIR).parts):
            continue

        rel = src_path.relative_to(SCAFFOLD_TEMPLATES_DIR)
        # Apply directory and file renames
        rel_parts = [_SCAFFOLD_DIR_RENAMES.get(p, p) for p in rel.parent.parts]
        dest_name = _SCAFFOLD_RENAMES.get(rel.name, rel.name)
        dest_path = target / Path(*rel_parts) / dest_name if rel_parts else target / dest_name

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        content = src_path.read_text()
        content = content.replace("{project_name}", project_name)
        content = content.replace("{project_name_snake}", project_name_snake)
        dest_path.write_text(content)

    # Create __init__.py files
    for d in _INIT_PY_DIRS:
        init_dir = target / d
        init_dir.mkdir(parents=True, exist_ok=True)
        (init_dir / "__init__.py").write_text("")

    # Create empty directories with .gitkeep so git tracks them
    for d in _EMPTY_DIRS:
        (target / d).mkdir(parents=True, exist_ok=True)
        (target / d / ".gitkeep").write_text("")

    # Copy skills
    claude_dir = target / ".claude"
    skills_dest = claude_dir / "skills"
    for skill in sorted(SKILLS_DIR.iterdir()):
        if skill.is_dir() and (skill / "SKILL.md").exists():
            shutil.copytree(skill, skills_dest / skill.name)

    # Copy agents
    agents_dest = claude_dir / "agents"
    for agent in sorted(AGENTS_DIR.iterdir()):
        if agent.is_dir() and (agent / "AGENT.md").exists():
            shutil.copytree(agent, agents_dest / agent.name)

    # Copy CLAUDE.md and SECURITY.md
    shutil.copy2(CLAUDE_MD, claude_dir / "CLAUDE.md")
    if SECURITY_MD.exists():
        shutil.copy2(SECURITY_MD, claude_dir / "SECURITY.md")

    # Scaffold shared memory directory and session capture hook
    _scaffold_memory(target)

    print(f"\n  ✓ Scaffolded project: {target}")
    print("    - ingestion/           dlt pipelines")
    print("    - transformation/      dbt project")
    print("    - orchestration/       Dagster orchestration")
    print("    - .claude/             Skills, agents, memory, project config")
    print("\n  Next steps:")
    print(f"    cd {project_name}")
    print("    uv sync")
    print("    dagster dev\n")


# ─── Entry ───────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="swishbot",
        description="Install data stack skills into your Claude environment",
    )
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List available skills")

    # install
    install_parser = subparsers.add_parser("install", help="Install skills or agents")
    install_parser.add_argument("skills", nargs="*", help="Skill or agent names to install")
    install_parser.add_argument("--all", action="store_true", help="Install all skills (or all agents with --agent)")
    install_parser.add_argument("--agent", action="store_true", help="Install agents instead of skills")
    install_parser.add_argument("--path", type=str, help=f"Install target (default: {DEFAULT_INSTALL_PATH})")

    # init
    init_parser = subparsers.add_parser("init", help="Scaffold a new skill")
    init_parser.add_argument("name", help="Name for the new skill")

    # init-project
    init_project_parser = subparsers.add_parser("init-project", help="Install a starter CLAUDE.md into your project")
    init_project_parser.add_argument("--path", type=str, help="Target directory (default: current directory)")
    init_project_parser.add_argument("--force", action="store_true", help="Overwrite existing CLAUDE.md")

    # hooks
    hooks_parser = subparsers.add_parser("hooks", help="List hooks provided by installed skills")
    hooks_parser.add_argument("--path", type=str, help=f"Skills install path (default: {DEFAULT_INSTALL_PATH})")

    # init-memory
    init_memory_parser = subparsers.add_parser("init-memory", help="Scaffold project memory directory with templates")
    init_memory_parser.add_argument("--path", type=str, help="Target directory (default: current directory)")
    init_memory_parser.add_argument("--force", action="store_true", help="Overwrite existing memory directory")

    # scaffold
    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold a new analytics project")
    scaffold_parser.add_argument("name", help="Project name (kebab-case)")
    scaffold_parser.add_argument("--path", type=str, help="Parent directory (default: current directory)")
    scaffold_parser.add_argument("--force", action="store_true", help="Overwrite existing directory")

    args = parser.parse_args()

    match args.command:
        case "list":
            cmd_list(args)
        case "install":
            cmd_install(args)
        case "init":
            cmd_init(args)
        case "init-project":
            cmd_init_project(args)
        case "hooks":
            cmd_hooks(args)
        case "init-memory":
            cmd_init_memory(args)
        case "scaffold":
            cmd_scaffold(args)
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
