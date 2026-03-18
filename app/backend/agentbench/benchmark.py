"""AgentBench — times 6 dev tasks: manual estimate vs actual agent run time."""
import os, time, csv
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv(Path(__file__).parents[3] / ".env")
from rich.console import Console
from rich.table import Table

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
console = Console()

TASKS = [
    {
        "name": "Write PR description",
        "manual_min": 25,
        "skill": "pr-reviewer",
        "input": (
            "Generate a professional PR description for a commit that adds JWT "
            "authentication to a FastAPI endpoint, including middleware, token "
            "validation, and unit tests."
        ),
    },
    {
        "name": "Validate data contract",
        "manual_min": 40,
        "skill": "data-contract-bot",
        "input": (
            "Validate this data contract: name=user_events, version=1.0.0, "
            "owner=platform-team, columns=[user_id:string, event_type:string, timestamp:datetime]"
        ),
    },
    {
        "name": "Code review + comments",
        "manual_min": 55,
        "skill": "pr-reviewer",
        "input": (
            "Review this Python function for issues:\n"
            "def get_user(id):\n"
            "  conn = db.connect()\n"
            "  return conn.execute(f'SELECT * FROM users WHERE id={id}').fetchone()"
        ),
    },
    {
        "name": "Generate OpenSpec YAML",
        "manual_min": 30,
        "skill": "openspec-validator",
        "input": (
            "Generate an OpenSpec YAML schema for a REST API endpoint that accepts "
            "a user registration payload: email, password, name, optional phone number."
        ),
    },
    {
        "name": "Write unit tests",
        "manual_min": 60,
        "skill": "pr-reviewer",
        "input": (
            "Write pytest unit tests for a function that validates an email address "
            "using regex. Cover valid emails, invalid formats, empty strings, and edge cases."
        ),
    },
    {
        "name": "README + changelog",
        "manual_min": 20,
        "skill": "pr-reviewer",
        "input": (
            "Write a README section and CHANGELOG entry for a new feature: async job "
            "queue using Redis and Celery, with retry logic and dead letter queue."
        ),
    },
]


def load_skill(skill_name: str) -> str:
    path = Path("skills") / skill_name / "SKILL.md"
    if path.exists():
        return path.read_text()
    return f"You are a senior software engineer helping with: {skill_name}"


def run_task(task: dict) -> dict:
    skill_content = load_skill(task["skill"])
    start = time.time()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=skill_content,
        messages=[{"role": "user", "content": task["input"]}],
    )
    elapsed_sec = round(time.time() - start, 1)
    elapsed_min = round(elapsed_sec / 60, 2)
    saved_pct = round((1 - elapsed_min / task["manual_min"]) * 100, 1)
    return {
        "name": task["name"],
        "manual_min": task["manual_min"],
        "agent_sec": elapsed_sec,
        "agent_min": elapsed_min,
        "saved_pct": saved_pct,
        "output_preview": response.content[0].text[:150].replace("\n", " ") + "...",
    }


def main():
    console.print("\n[bold cyan]AgentBench — devflow-lab[/bold cyan]")
    console.print("[dim]Running 6 tasks: recording manual estimate vs agent time...[/dim]\n")

    results = []
    for task in TASKS:
        console.print(f"  ⏱  [cyan]{task['name']}[/cyan]", end=" ")
        result = run_task(task)
        results.append(result)
        console.print(
            f"→ agent: [green]{result['agent_sec']}s[/green]  "
            f"manual: {task['manual_min']}min  "
            f"saved: [bold green]{result['saved_pct']}%[/bold green]"
        )

    # Write CSV
    out_path = Path("agentbench/results.csv")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "manual_min", "agent_sec", "agent_min", "saved_pct", "output_preview"]
        )
        writer.writeheader()
        writer.writerows(results)

    # Summary table
    table = Table(title="\n  AgentBench Results", show_header=True, header_style="bold")
    table.add_column("Task",        style="cyan",  min_width=28)
    table.add_column("Manual",      justify="right")
    table.add_column("Agent",       justify="right", style="green")
    table.add_column("Time saved",  justify="right", style="bold green")
    table.add_column("Speedup",     justify="right", style="bold")

    for r in results:
        speedup = round(r["manual_min"] / max(r["agent_min"], 0.01))
        table.add_row(
            r["name"],
            f"{r['manual_min']} min",
            f"{r['agent_sec']} s",
            f"{r['saved_pct']}%",
            f"~{speedup}x",
        )

    total_manual = sum(r["manual_min"] for r in results)
    total_agent_min = round(sum(r["agent_min"] for r in results), 1)
    total_saved = round((1 - total_agent_min / total_manual) * 100, 1)
    total_speedup = round(total_manual / max(total_agent_min, 0.01))
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_manual} min[/bold]",
        f"[bold]{total_agent_min} min[/bold]",
        f"[bold]{total_saved}%[/bold]",
        f"[bold]~{total_speedup}x[/bold]",
    )

    console.print(table)
    console.print(f"\n  Results saved → [bold]{out_path}[/bold]\n")


if __name__ == "__main__":
    main()
