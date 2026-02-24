# Copyright (c) 2026 Swish BI Limited. All rights reserved.
# Licensed under proprietary license. See LICENSE for details.

"""swishbot CLI — Install data stack skills into your Claude environment."""

import argparse
import json
import os
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

# ─── Terminal styling ─────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def _tty() -> bool:
    """True only when stdout is a color-capable interactive terminal."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Apply ANSI code; pass through unchanged when not a TTY."""
    return f"{code}{text}{_RESET}" if _tty() else text


def _bold(t: str) -> str:
    return _c(_BOLD, t)


def _dim(t: str) -> str:
    return _c(_DIM, t)


def _red(t: str) -> str:
    return _c(_RED, t)


def _green(t: str) -> str:
    return _c(_GREEN, t)


def _yellow(t: str) -> str:
    return _c(_YELLOW, t)


def _cyan(t: str) -> str:
    return _c(_CYAN, t)


def _header(title: str) -> str:
    """Bold cyan section title with a dim horizontal rule below."""
    if not _tty():
        return f"\n{title}"
    rule = _DIM + "─" * min(len(title) + 2, 72) + _RESET
    return f"\n{_BOLD}{_CYAN}{title}{_RESET}\n{rule}"


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
    for f in sorted(AGENTS_DIR.iterdir()):
        if f.is_file() and f.suffix == ".md":
            content = f.read_text()
            match = re.search(r'description:\s*"?([^"\n]+)"?', content)
            description = match.group(1).strip() if match else "(no description)"
            agents.append({"name": f.stem, "description": description})

    return agents


# ─── Commands ────────────────────────────────────────────────────────


def _prompt_scope(project_path: Path, global_path: Path) -> Path:
    """Prompt user to choose project-local or global install."""
    print(f"\n{_bold('Install to:')}")
    print(f"  {_cyan('[P]')} Project  {_dim(f'— {project_path}')}")
    print(f"  {_cyan('[G]')} Global   {_dim(f'— {global_path}')}")
    while True:
        try:
            choice = input("Choice [P/G]: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)
        if choice in ("P", "PROJECT"):
            return project_path
        if choice in ("G", "GLOBAL"):
            return global_path
        print("  Please enter P or G.", file=sys.stderr)


def cmd_list(args: argparse.Namespace) -> None:
    """List available skills and agents."""
    skills = get_available_skills()
    agents = get_available_agents()

    if not skills and not agents:
        print("No skills or agents found.")
        return

    if skills:
        max_name = max(len(s["name"]) for s in skills)
        print(_header("Available skills:"))
        print()
        for s in skills:
            name_padded = f"{s['name']:<{max_name + 2}}"
            print(f"  {_bold(name_padded)} {_dim(s['description'])}")
        print(f"\n{_dim('Install with: swishbot install <skill-name>')}")

    if agents:
        max_name = max(len(a["name"]) for a in agents)
        print(_header("Available agents:"))
        print()
        for a in agents:
            name_padded = f"{a['name']:<{max_name + 2}}"
            print(f"  {_bold(name_padded)} {_dim(a['description'])}")
        print(f"\n{_dim('Install agent: swishbot install --agent <agent-name>')}")

    print()


def cmd_install(args: argparse.Namespace) -> None:
    """Install one or more skills or agents."""
    if args.agent:
        _install_agents(args)
    else:
        _install_skills(args)


def _install_skills(args: argparse.Namespace) -> None:
    """Install one or more skills."""
    if args.path:
        dest = Path(args.path)
    else:
        dest = _prompt_scope(Path.cwd() / ".claude" / "skills", DEFAULT_INSTALL_PATH)
    dest.mkdir(parents=True, exist_ok=True)
    available = {s["name"] for s in get_available_skills()}

    if args.all:
        names = sorted(available)
    elif args.skills:
        names = args.skills
    else:
        print(f"{_red('Error:')} specify a skill name or use --all", file=sys.stderr)
        sys.exit(1)

    for name in names:
        if name not in available:
            print(f"{_red('Error:')} skill '{name}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(sorted(available))}", file=sys.stderr)
            sys.exit(1)

        src = SKILLS_DIR / name
        skill_dest = dest / name

        if skill_dest.exists():
            print(f"  {_yellow('⟳')} {_bold(name)} {_dim('— already installed, overwriting')}")
            shutil.rmtree(skill_dest)

        shutil.copytree(src, skill_dest)
        print(f"  {_green('✓')} {_bold(name)} {_dim(f'→ {skill_dest}')}")

    print(f"\n{_bold('Done.')} {_dim(f'Skills installed to {dest}')}")
    print("Make sure your Claude project references this path.\n")


def _install_agents(args: argparse.Namespace) -> None:
    """Install one or more agents."""
    if args.path:
        dest = Path(args.path)
    else:
        dest = _prompt_scope(Path.cwd() / ".claude" / "agents", DEFAULT_AGENT_INSTALL_PATH)
    dest.mkdir(parents=True, exist_ok=True)
    available = {a["name"] for a in get_available_agents()}

    if args.all:
        names = sorted(available)
    elif args.skills:
        names = args.skills
    else:
        print(f"{_red('Error:')} specify an agent name or use --all", file=sys.stderr)
        sys.exit(1)

    for name in names:
        if name not in available:
            print(f"{_red('Error:')} agent '{name}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(sorted(available))}", file=sys.stderr)
            sys.exit(1)

        src = AGENTS_DIR / f"{name}.md"
        agent_dest = dest / f"{name}.md"

        if agent_dest.exists():
            print(f"  {_yellow('⟳')} {_bold(name)} {_dim('— already installed, overwriting')}")
            agent_dest.unlink()

        shutil.copy2(src, agent_dest)
        print(f"  {_green('✓')} {_bold(name)} {_dim(f'→ {agent_dest}')}")

    print(f"\n{_bold('Done.')} {_dim(f'Agents installed to {dest}')}")
    print("Make sure your Claude project references this path.\n")


def cmd_init_project(args: argparse.Namespace) -> None:
    """Install a starter CLAUDE.md and SECURITY.md into a project."""
    if args.path:
        dest = Path(args.path)
    else:
        dest = _prompt_scope(Path.cwd() / ".claude", Path.home() / ".claude")
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "CLAUDE.md"

    if target.exists() and not args.force:
        print(f"{_red('Error:')} {target} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(CLAUDE_MD, target)
    print(f"\n  {_green('✓')} CLAUDE.md {_dim(f'→ {target}')}")

    # Copy SECURITY.md if available
    if SECURITY_MD.exists():
        security_target = dest / "SECURITY.md"
        shutil.copy2(SECURITY_MD, security_target)
        print(f"  {_green('✓')} SECURITY.md {_dim(f'→ {security_target}')}")

    print(f"\n{_dim('Edit the file to uncomment your installed skills and fill in project details.')}\n")


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold a new skill."""
    name = args.name
    dest = SKILLS_DIR / name

    if dest.exists():
        print(f"{_red('Error:')} skill '{name}' already exists at {dest}", file=sys.stderr)
        sys.exit(1)

    dest.mkdir(parents=True)
    (dest / "workflows").mkdir()
    title = " ".join(w.capitalize() for w in name.split("-"))
    (dest / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=name, title=title))

    print(f"\n  {_green('✓')} Scaffolded new skill: {_bold(str(dest / 'SKILL.md'))}")
    print(f"{_dim('Edit the SKILL.md to encode your methodology.')}\n")


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

    print(_header("Installed hooks:"))
    print()
    for h in hooks_found:
        name_padded = f"{h['skill']:<{max_skill + 2}}"
        event_padded = f"{h['event']:<{max_event + 2}}"
        matcher_str = f"({h['matcher']})"
        print(f"  {_bold(name_padded)} {_cyan(event_padded)} {_dim(matcher_str)}  {h['description']}")
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
    """Create .claude/memory/ templates and settings.json Stop hook.

    Idempotent — skips settings.json if it already exists.
    """
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
                                    "Review this session. If cross-agent project decisions were made — "
                                    "naming conventions, modeling choices, source configurations — "
                                    "update the relevant files in .claude/memory/. "
                                    "Do NOT update .claude/agent-memory/ here; agents manage that automatically. "
                                    "Only update if substantive shared decisions were made."
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
    if args.path:
        dest = Path(args.path)
    else:
        dest = _prompt_scope(Path.cwd(), Path.home())
    memory_dir = dest / ".claude" / "memory"

    if memory_dir.exists() and not args.force:
        print(f"{_red('Error:')} {memory_dir} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    settings_path = dest / ".claude" / "settings.json"
    settings_existed = settings_path.exists()

    _scaffold_memory(dest)

    if settings_existed:
        print(f"  {_yellow('⟳')} {_dim(str(settings_path))} already exists — add the Stop hook manually if desired")
    else:
        print(f"  {_green('✓')} {_dim(str(settings_path))} (session capture hook)")

    print(f"\n  {_green('✓')} Memory templates {_dim(f'→ {memory_dir}')}")
    files = sorted(f.name for f in memory_dir.iterdir() if f.is_file())
    for f in files:
        print(f"    {_dim('-')} {f}")
    print(f"\n{_dim('Claude will update these files as decisions are made during sessions.')}\n")


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
            print(f"{_red('Error:')} {target} already exists. Use --force to overwrite.", file=sys.stderr)
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
    agents_dest.mkdir(parents=True, exist_ok=True)
    for agent in sorted(AGENTS_DIR.iterdir()):
        if agent.is_file() and agent.suffix == ".md":
            shutil.copy2(agent, agents_dest / agent.name)

    # Copy CLAUDE.md and SECURITY.md
    shutil.copy2(CLAUDE_MD, claude_dir / "CLAUDE.md")
    if SECURITY_MD.exists():
        shutil.copy2(SECURITY_MD, claude_dir / "SECURITY.md")

    # Scaffold shared memory directory and session capture hook
    _scaffold_memory(target)

    print(f"\n  {_green('✓')} Scaffolded project: {_bold(str(target))}")
    print(f"    {_dim('- ingestion/           dlt pipelines')}")
    print(f"    {_dim('- transformation/      dbt project')}")
    print(f"    {_dim('- orchestration/       Dagster orchestration')}")
    print(f"    {_dim('- .claude/             Skills, agents, memory, project config')}")
    print(f"\n  {_bold('Next steps:')}")
    print(f"    {_cyan(f'cd {project_name}')}")
    print(f"    {_cyan('uv sync')}")
    print(f"    {_cyan('dagster dev')}\n")


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
