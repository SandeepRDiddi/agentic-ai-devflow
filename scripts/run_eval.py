"""
devflow-lab — Skill trigger eval runner.

Measures how reliably each SKILL.md fires for the right prompts.
Run with: hatch run eval
"""
import os, json
from pathlib import Path
import anthropic
from rich.console import Console
from rich.table import Table

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
console = Console()
SKILLS_DIR = Path("skills")
EVALS_DIR  = Path("evals")


def build_available_skills_summary() -> str:
    """Build the same available_skills context Claude sees in production."""
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            continue
        content = skill_md_path.read_text()
        # Extract description from YAML frontmatter
        lines = content.splitlines()
        in_desc = False
        desc_lines = []
        for line in lines:
            if line.strip().startswith("description:"):
                in_desc = True
                rest = line.split("description:", 1)[1].strip().lstrip(">").strip()
                if rest:
                    desc_lines.append(rest)
            elif in_desc:
                if line.startswith("  ") or line.startswith("\t"):
                    desc_lines.append(line.strip())
                else:
                    break
        desc = " ".join(desc_lines)[:300]
        skills.append(f"- name: {skill_dir.name}\n  description: {desc}")
    return "\n".join(skills)


def check_trigger(skill_name: str, prompt: str, skills_summary: str) -> bool:
    """Ask Claude whether it would use the named skill for this prompt."""
    check = (
        f"You have access to these Claude Skills:\n\n{skills_summary}\n\n"
        f"A user sends this message: \"{prompt}\"\n\n"
        f"Would you consult the '{skill_name}' skill to help with this request?\n"
        "Answer with only YES or NO."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=5,
        messages=[{"role": "user", "content": check}],
    )
    return "YES" in response.content[0].text.upper()


def run_evals_for_file(eval_file: Path, skills_summary: str) -> tuple[int, int]:
    data = json.loads(eval_file.read_text())
    skill = data["skill"]
    cases = data["test_cases"]

    table = Table(title=f"Skill: {skill}", show_header=True, header_style="bold")
    table.add_column("Prompt",   max_width=52, style="dim")
    table.add_column("Expected", justify="center")
    table.add_column("Got",      justify="center")
    table.add_column("Pass",     justify="center")

    passed = 0
    for case in cases:
        triggered = check_trigger(skill, case["prompt"], skills_summary)
        expected  = case["should_trigger"]
        ok = triggered == expected
        if ok:
            passed += 1
        table.add_row(
            case["prompt"][:52],
            "✓ trigger" if expected  else "✗ skip",
            "✓ trigger" if triggered else "✗ skip",
            "[green]PASS[/green]" if ok else "[red]FAIL[/red]",
        )

    console.print(table)
    rate = round(passed / len(cases) * 100)
    color = "green" if rate >= 80 else "yellow" if rate >= 60 else "red"
    console.print(f"  Trigger accuracy: [{color}]{rate}%[/{color}] ({passed}/{len(cases)})\n")
    return passed, len(cases)


def main():
    console.print("\n[bold cyan]devflow-lab — Skill Trigger Evals[/bold cyan]\n")

    if not any(SKILLS_DIR.iterdir()):
        console.print("[red]No skills found in skills/ directory.[/red]")
        return

    skills_summary = build_available_skills_summary()
    overall_pass = overall_total = 0

    for eval_file in sorted(EVALS_DIR.glob("*.json")):
        p, t = run_evals_for_file(eval_file, skills_summary)
        overall_pass  += p
        overall_total += t

    if overall_total > 0:
        overall_rate = round(overall_pass / overall_total * 100)
        color = "green" if overall_rate >= 80 else "yellow" if overall_rate >= 60 else "red"
        console.print(f"[bold]Overall accuracy: [{color}]{overall_rate}%[/{color}] ({overall_pass}/{overall_total})[/bold]\n")


if __name__ == "__main__":
    main()
