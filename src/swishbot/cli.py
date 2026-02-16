# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""swishbot CLI — Install data stack skills into your Claude environment."""

import argparse
import re
import shutil
import sys
from pathlib import Path

CLAUDE_DIR = Path(__file__).parent / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
AGENTS_DIR = CLAUDE_DIR / "agents"
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
DEFAULT_INSTALL_PATH = Path.home() / ".claude" / "skills"
DEFAULT_AGENT_INSTALL_PATH = Path.home() / ".claude" / "agents"

SKILL_TEMPLATE = """\
---
name: {name}
description: "[TODO: Describe when to use this skill and what it does.]"
workflows: []
---

# {title}

## Overview

[TODO: What this skill does and the methodology behind it.]

## Workflows

[TODO: Add workflow files in the `workflows/` subdirectory and
reference them here. Each workflow is a focused, step-by-step
procedure for a specific task within this skill.]

| Workflow | When to Use |
|----------|-------------|

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
    """Install a starter CLAUDE.md into a project."""
    dest = Path(args.path) if args.path else Path.cwd()
    target = dest / "CLAUDE.md"

    if target.exists() and not args.force:
        print(f"Error: {target} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(CLAUDE_MD, target)
    print(f"\n  ✓ CLAUDE.md → {target}")
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
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
