"""
mini_reviewer/demo.py
──────────────────────
Live agentic AI demo — runs 3 real tasks through Claude Skills,
prints results to the terminal, and saves a Markdown report.

Run from devflow-lab/:
    python mini_reviewer/demo.py
"""

import os, re, sys, time
from pathlib import Path
from datetime import datetime

# ── Load .env — overwrite empty env vars (handles corp proxy zeroing them) ────
_env = Path(__file__).parents[1] / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _k = _k.strip()
        _v = _v.strip().strip('"').strip("'")
        if _k and _v:
            # Always overwrite if current value is empty
            if not os.environ.get(_k):
                os.environ[_k] = _v

# ── Deps ─────────────────────────────────────────────────────────────────────
import subprocess
for _pkg in ["anthropic", "rich", "httpx"]:
    try: __import__(_pkg)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", _pkg,
                        "--break-system-packages", "-q"])

import httpx
import anthropic
from rich.console  import Console
from rich.panel    import Panel
from rich.rule     import Rule
from rich.table    import Table
from rich.syntax   import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ── Anthropic client ──────────────────────────────────────────────────────────
_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_model   = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_client  = anthropic.Anthropic(
    api_key=_api_key,
    http_client=httpx.Client(verify=False),   # bypass self-signed proxy certs
)

SKILLS_DIR = Path(__file__).parents[1] / "skills"


# ── Core helpers ──────────────────────────────────────────────────────────────
def load_skill(name: str) -> str:
    p = SKILLS_DIR / name / "SKILL.md"
    return p.read_text() if p.exists() else f"You are a senior software engineer."


def run_agent(skill_name: str, task: str, max_tokens: int = 1500) -> tuple[str, float]:
    """Core agent loop: skill → system prompt, task → user message."""
    system = load_skill(skill_name)
    start  = time.time()
    resp   = _client.messages.create(
        model=_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": task}],
    )
    return resp.content[0].text, round(time.time() - start, 2)


# ══════════════════════════════════════════════════════════════════════════════
# Demo tasks
# ══════════════════════════════════════════════════════════════════════════════

TASKS = [
    {
        "id": 1,
        "title": "Code Review  ·  pr-reviewer skill",
        "skill": "pr-reviewer",
        "manual_min": 55,
        "input": (
            "Review this Python authentication code for issues:\n\n"
            "```python\n"
            "import psycopg2, os\n\n"
            'DB_URL = "postgresql://admin:password123@prod-db:5432/users"  # hardcoded creds\n\n'
            "def get_user(user_id):\n"
            "    conn = psycopg2.connect(DB_URL)\n"
            "    cur  = conn.cursor()\n"
            "    cur.execute(f'SELECT * FROM users WHERE id = {user_id}')  # SQL injection\n"
            "    return cur.fetchone()  # no conn.close(), no error handling\n\n"
            "def reset_password(email, new_pass):\n"
            "    conn = psycopg2.connect(DB_URL)\n"
            "    cur  = conn.cursor()\n"
            "    cur.execute(f\"UPDATE users SET password='{new_pass}' WHERE email='{email}'\")\n"
            "    conn.commit()\n"
            "    # no password hashing, no auth check, no input validation\n"
            "```"
        ),
        "show_syntax": (
            "import psycopg2\n"
            'DB_URL = "postgresql://admin:password123@prod-db:5432/users"\n\n'
            "def get_user(user_id):\n"
            "    conn = psycopg2.connect(DB_URL)\n"
            "    cur  = conn.cursor()\n"
            "    cur.execute(f'SELECT * FROM users WHERE id = {user_id}')\n"
            "    return cur.fetchone()\n\n"
            "def reset_password(email, new_pass):\n"
            "    conn = psycopg2.connect(DB_URL)\n"
            "    cur.execute(f\"UPDATE users SET password='{new_pass}'...\")\n"
            "    conn.commit()"
        ),
    },
    {
        "id": 2,
        "title": "Data Contract  ·  data-contract-bot skill",
        "skill": "data-contract-bot",
        "manual_min": 40,
        "input": (
            "Generate and validate a data contract for:\n"
            "name: user_events\n"
            "version: 2.0.0\n"
            "owner: platform-team\n"
            "columns:\n"
            "  - user_id: uuid, required, primary key\n"
            "  - event_type: string enum [login, logout, purchase, view], required\n"
            "  - session_id: uuid, required\n"
            "  - timestamp: datetime with timezone, required\n"
            "  - properties: json blob, optional\n"
            "  - revenue_usd: decimal(10,2), nullable, only set for purchase events\n"
            "SLA: data available within 60s of event, 99.9% uptime"
        ),
        "show_syntax": (
            "name: user_events\nversion: 2.0.0\nowner: platform-team\n"
            "columns:\n"
            "  - user_id: uuid (PK)\n"
            "  - event_type: enum[login, logout, purchase, view]\n"
            "  - timestamp: datetime+tz\n"
            "  - revenue_usd: decimal(10,2) nullable\n"
            "SLA: <60s delivery, 99.9% uptime"
        ),
    },
    {
        "id": 3,
        "title": "README + Tests  ·  pr-reviewer skill",
        "skill": "pr-reviewer",
        "manual_min": 45,
        "input": (
            "Two tasks in one:\n"
            "1. Write pytest unit tests for this email validator:\n"
            "   def validate_email(email: str) -> bool:\n"
            "       import re\n"
            "       return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', email))\n"
            "   Cover: valid emails, missing @, multiple dots, empty string, unicode, long addresses.\n\n"
            "2. Then write a short README section describing this validator's purpose and usage."
        ),
        "show_syntax": (
            "def validate_email(email: str) -> bool:\n"
            "    import re\n"
            "    return bool(re.match(\n"
            "        r'^[a-zA-Z0-9._%+-]+@'\n"
            "        r'[a-zA-Z0-9.-]+\\.'\n"
            "        r'[a-zA-Z]{2,}$', email))"
        ),
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Report
# ══════════════════════════════════════════════════════════════════════════════

def build_report(results: list[dict]) -> str:
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_manual = sum(r["manual_min"] for r in results)
    total_agent  = round(sum(r["elapsed"] for r in results), 1)
    total_saved  = round((1 - (total_agent / 60) / total_manual) * 100, 1)
    overall_speedup = round(total_manual / max(total_agent / 60, 0.001))

    md = [
        "# devflow-lab · Agentic AI Demo — Results",
        f"_Generated: {ts}  |  Model: `{_model}`_\n",
        "---\n",
        "## Executive Summary\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Tasks completed | {len(results)} |",
        f"| Total manual estimate | **{total_manual} minutes** |",
        f"| Total agent time | **{total_agent} seconds** |",
        f"| Overall time saved | **{total_saved}%** |",
        f"| Overall speedup | **~{overall_speedup}x faster** |\n",
        "---\n",
    ]

    for r in results:
        saved = round((1 - (r["elapsed"] / 60) / r["manual_min"]) * 100, 1)
        spdup = round(r["manual_min"] / max(r["elapsed"] / 60, 0.001))
        md += [
            f"## Task {r['id']}: {r['title']}\n",
            f"- **Skill used**: `{r['skill']}`",
            f"- **Manual estimate**: {r['manual_min']} minutes",
            f"- **Agent completed in**: {r['elapsed']} seconds",
            f"- **Time saved**: {saved}%  |  **Speedup**: ~{spdup}x\n",
            "### Output\n",
            r["output"],
            "\n---\n",
        ]

    return "\n".join(md)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]devflow-lab · Agentic AI Demo[/bold cyan]\n"
        f"[dim]Model: {_model}  |  Skills: {len(list(SKILLS_DIR.iterdir()))} loaded[/dim]",
        border_style="cyan",
    ))

    # List skills
    console.print("\n[bold]Available Skills:[/bold]")
    for d in sorted(SKILLS_DIR.iterdir()):
        if (d / "SKILL.md").exists():
            console.print(f"  [cyan]▸[/cyan] {d.name}")

    console.print()
    results = []

    for task in TASKS:
        console.rule(f"[bold]Task {task['id']} · {task['title']}[/bold]")

        # Show the input
        console.print("\n[dim]Input:[/dim]")
        console.print(Syntax(task["show_syntax"], "python", theme="monokai",
                              line_numbers=False, padding=(0, 1)))
        console.print()

        # Run agent with spinner
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                      transient=True, console=console) as progress:
            progress.add_task(f"Agent thinking... (skill: {task['skill']})")
            output, elapsed = run_agent(task["skill"], task["input"])

        saved_pct = round((1 - (elapsed / 60) / task["manual_min"]) * 100, 1)
        speedup   = round(task["manual_min"] / max(elapsed / 60, 0.001))

        console.print(Panel(
            output,
            title=f"[bold green]Claude's Output[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))

        console.print(
            f"\n  ⏱  Agent: [green bold]{elapsed}s[/green bold]  "
            f"vs manual: {task['manual_min']} min  "
            f"→  saved [bold green]{saved_pct}%[/bold green]  "
            f"([bold]~{speedup}x faster[/bold])\n"
        )

        results.append({**task, "elapsed": elapsed, "output": output})

    # Summary table
    console.rule("[bold cyan]FINAL BENCHMARK[/bold cyan]")
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Task",         style="cyan",       min_width=35)
    table.add_column("Manual",       justify="right")
    table.add_column("Agent",        justify="right", style="green")
    table.add_column("Saved",        justify="right", style="bold green")
    table.add_column("Speedup",      justify="right", style="bold")

    total_manual = sum(r["manual_min"] for r in results)
    total_agent  = round(sum(r["elapsed"] for r in results), 1)

    for r in results:
        saved = round((1 - (r["elapsed"] / 60) / r["manual_min"]) * 100, 1)
        spdup = round(r["manual_min"] / max(r["elapsed"] / 60, 0.001))
        table.add_row(r["title"], f"{r['manual_min']} min",
                      f"{r['elapsed']} s", f"{saved}%", f"~{spdup}x")

    total_saved  = round((1 - (total_agent / 60) / total_manual) * 100, 1)
    total_speedup = round(total_manual / max(total_agent / 60, 0.001))
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_manual} min[/bold]",
        f"[bold]{total_agent} s[/bold]",
        f"[bold]{total_saved}%[/bold]",
        f"[bold]~{total_speedup}x[/bold]",
    )
    console.print(table)

    # Save report
    report    = build_report(results)
    out_path  = Path(__file__).parent / "results.md"
    out_path.write_text(report)

    console.print()
    console.print(f"[bold green]✅  Demo complete![/bold green]")
    console.print(f"    Markdown report → [bold]{out_path}[/bold]\n")
    return out_path


if __name__ == "__main__":
    main()
