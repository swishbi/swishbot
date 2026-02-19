"""MkDocs hook to auto-generate the skills and agents catalog from frontmatter.

Only exposes names and descriptions — not the actual content.
"""

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2] / "src" / "swishbot" / ".claude" / "skills"
AGENTS_DIR = Path(__file__).resolve().parents[2] / "src" / "swishbot" / ".claude" / "agents"
PLACEHOLDER = "<!-- SKILLS_CATALOG -->"
AGENTS_PLACEHOLDER = "<!-- AGENTS_CATALOG -->"

CATEGORIES = {
    "Discovery & Planning": ["business-logic-mapping", "requirements-discovery"],
    "Infrastructure": ["dba-security", "iac-terraform"],
    "Ingestion": ["dlt-pipelines"],
    "Orchestration": ["dagster"],
    "Transformation (dbt)": [
        "dbt",
        "dimensional-modeling",
    ],
    "Analytics & Presentation": ["powerbi", "semantic-layer"],
}


def _read_skills() -> dict[str, str]:
    """Read skill names and descriptions from SKILL.md frontmatter."""
    skills = {}
    for d in sorted(SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if d.is_dir() and skill_md.exists():
            content = skill_md.read_text()
            match = re.search(r'description:\s*"?([^"\n]+)"?', content)
            desc = match.group(1).strip().rstrip('"') if match else "(no description)"
            skills[d.name] = desc
    return skills


def _build_catalog(skills: dict[str, str]) -> str:
    """Build markdown table grouped by category."""
    lines = []
    for category, members in CATEGORIES.items():
        lines.append(f"### {category}\n")
        lines.append("| Skill | Description |")
        lines.append("|-------|-------------|")
        for name in members:
            desc = skills.get(name, "(not found)")
            lines.append(f"| `{name}` | {desc} |")
        lines.append("")

    # Any skills not in a category
    categorized = {s for members in CATEGORIES.values() for s in members}
    uncategorized = {k: v for k, v in skills.items() if k not in categorized}
    if uncategorized:
        lines.append("### Other\n")
        lines.append("| Skill | Description |")
        lines.append("|-------|-------------|")
        for name, desc in sorted(uncategorized.items()):
            lines.append(f"| `{name}` | {desc} |")
        lines.append("")

    return "\n".join(lines)


def _read_agents() -> dict[str, str]:
    """Read agent names and descriptions from AGENT.md frontmatter."""
    agents = {}
    for d in sorted(AGENTS_DIR.iterdir()):
        agent_md = d / "AGENT.md"
        if d.is_dir() and agent_md.exists():
            content = agent_md.read_text()
            match = re.search(r'description:\s*"?([^"\n]+)"?', content)
            desc = match.group(1).strip().rstrip('"') if match else "(no description)"
            agents[d.name] = desc
    return agents


def _build_agents_catalog(agents: dict[str, str]) -> str:
    """Build markdown table for agents."""
    lines = ["| Agent | Description |", "|-------|-------------|"]
    for name, desc in sorted(agents.items()):
        lines.append(f"| `{name}` | {desc} |")
    lines.append("")
    return "\n".join(lines)


def on_page_markdown(markdown: str, **kwargs) -> str:
    """Replace catalog placeholders with generated tables."""
    if PLACEHOLDER in markdown:
        skills = _read_skills()
        catalog = _build_catalog(skills)
        markdown = markdown.replace(PLACEHOLDER, catalog)

    if AGENTS_PLACEHOLDER in markdown:
        agents = _read_agents()
        agents_catalog = _build_agents_catalog(agents)
        markdown = markdown.replace(AGENTS_PLACEHOLDER, agents_catalog)

    return markdown
