"""MkDocs hook to auto-generate the skills catalog from SKILL.md frontmatter.

Only exposes skill names and descriptions — not the actual skill content.
"""

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2] / "src" / "swishbot" / ".claude" / "skills"
PLACEHOLDER = "<!-- SKILLS_CATALOG -->"

CATEGORIES = {
    "Discovery & Planning": ["business-logic-mapping", "requirements-discovery"],
    "Infrastructure": ["analytics-architecture", "dba-security", "iac-terraform"],
    "Ingestion": ["dlt-pipelines"],
    "Transformation (dbt)": [
        "dbt-intermediate",
        "dbt-marts",
        "dbt-mcp",
        "dbt-staging",
        "dbt-staging-model",
        "dbt-style",
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


def on_page_markdown(markdown: str, **kwargs) -> str:
    """Replace the SKILLS_CATALOG placeholder with the generated table."""
    if PLACEHOLDER not in markdown:
        return markdown

    skills = _read_skills()
    catalog = _build_catalog(skills)
    return markdown.replace(PLACEHOLDER, catalog)
