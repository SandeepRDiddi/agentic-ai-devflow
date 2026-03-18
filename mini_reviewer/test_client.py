"""
mini_reviewer/test_client.py
─────────────────────────────
End-to-end test that:
  1. Starts the FastAPI server in a background thread
  2. Calls /health, /skills, /review, /benchmark
  3. Prints results live in the terminal (with colour)
  4. Saves a full Markdown report → mini_reviewer/results.md

Run from devflow-lab/:
    python mini_reviewer/test_client.py
"""

import sys, time, json, threading, textwrap
from pathlib import Path
from datetime import datetime

# ── Rich for coloured terminal output ────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel   import Panel
    from rich.rule    import Rule
    from rich.table   import Table
    from rich.syntax  import Syntax
    console = Console()
except ImportError:
    import subprocess; subprocess.run([sys.executable, "-m", "pip", "install", "rich", "-q"])
    from rich.console import Console
    from rich.panel   import Panel
    from rich.rule    import Rule
    from rich.table   import Table
    from rich.syntax  import Syntax
    console = Console()

# ── Install deps silently if missing ─────────────────────────────────────────
import subprocess
for pkg in ["fastapi", "uvicorn", "httpx", "anthropic", "python-dotenv", "pydantic"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "-q"])

import os, re
from pathlib import Path

# ── Inject API key before anything else imports ──────────────────────────────
_env = Path(__file__).parents[1] / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        m = re.match(r'^([A-Z_]+)\s*=\s*"?([^"#\n]+)"?', _line.strip())
        if m and m.group(1) not in os.environ:
            os.environ[m.group(1)] = m.group(2).strip()

import httpx
import uvicorn

BASE_URL = "http://127.0.0.1:8080"

# ══════════════════════════════════════════════════════════════════════════════
# Test payloads — real-world code samples with intentional issues
# ══════════════════════════════════════════════════════════════════════════════

BUGGY_CODE = """\
import psycopg2, os

DB_URL = "postgresql://admin:password123@prod-db:5432/users"   # hardcoded creds

def get_user(user_id):
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")   # SQL injection
    row  = cur.fetchone()
    return row                                                  # no close(), no error handling

def reset_password(email, new_pass):
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    cur.execute(f"UPDATE users SET password='{new_pass}' WHERE email='{email}'")
    conn.commit()
    # Missing: no hashing, no auth check, no input validation
"""

BENCHMARK_TASK = (
    "Write a complete README section and CHANGELOG entry for a new feature: "
    "async background job processing using Redis and Celery, with automatic "
    "retries (max 3), exponential back-off, dead-letter queue, and Prometheus metrics."
)


# ══════════════════════════════════════════════════════════════════════════════
# Server management
# ══════════════════════════════════════════════════════════════════════════════

_server_thread = None

def start_server():
    """Boot the FastAPI app in a daemon thread."""
    sys.path.insert(0, str(Path(__file__).parents[1]))   # devflow-lab/ on path
    from mini_reviewer.api import app
    config = uvicorn.Config(app, host="127.0.0.1", port=8080,
                            log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    # Wait until server is ready
    for _ in range(30):
        try:
            httpx.get(f"{BASE_URL}/health", timeout=1, verify=False)
            return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError("Server did not start in time")


# ══════════════════════════════════════════════════════════════════════════════
# Individual test calls
# ══════════════════════════════════════════════════════════════════════════════

def test_health(client: httpx.Client) -> dict:
    r = client.get("/health")
    r.raise_for_status()
    return r.json()


def test_skills(client: httpx.Client) -> dict:
    r = client.get("/skills")
    r.raise_for_status()
    return r.json()


def test_review(client: httpx.Client) -> dict:
    r = client.post("/review", json={
        "code": BUGGY_CODE,
        "context": "Auth service — submitted for PR review",
        "skill": "pr-reviewer",
    }, timeout=90)
    r.raise_for_status()
    return r.json()


def test_benchmark(client: httpx.Client) -> dict:
    r = client.post("/benchmark", json={
        "task": BENCHMARK_TASK,
        "manual_minutes": 25,
    }, timeout=90)
    r.raise_for_status()
    return r.json()


# ══════════════════════════════════════════════════════════════════════════════
# Report builder
# ══════════════════════════════════════════════════════════════════════════════

def build_report(health, skills, review, bench) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# devflow-lab · Mini Reviewer — Test Report",
        f"_Generated: {ts}_\n",
        "---\n",

        "## 1 · Health Check\n",
        f"- Status : `{health['status']}`",
        f"- Model  : `{health['model']}`",
        f"- Skills : `{health['skills_dir']}`\n",

        "## 2 · Available Skills\n",
        f"Found **{skills['count']} skills**:\n",
    ]
    for s in skills["skills"]:
        lines.append(f"- **{s['name']}** — {s['description']}")

    lines += [
        "\n## 3 · Code Review (pr-reviewer skill)\n",
        f"> Elapsed: **{review['elapsed_sec']}s** · Model: `{review['model']}`\n",
        "### Code submitted\n",
        "```python",
        BUGGY_CODE.strip(),
        "```\n",
        "### Claude's review\n",
        review["review"],
    ]

    saved_pct = round((1 - (bench["agent_seconds"] / 60) / bench["manual_minutes"]) * 100, 1)
    lines += [
        "\n---\n",
        "## 4 · Benchmark — Agent vs Manual\n",
        f"| | |",
        f"|---|---|",
        f"| Task | {bench['task'][:80]}... |",
        f"| Your estimate | **{bench['manual_minutes']} minutes** |",
        f"| Agent took | **{bench['agent_seconds']} seconds** |",
        f"| Speedup | **{bench['speedup']}** |",
        f"| Time saved | **{saved_pct}%** |",
        "\n### Agent output preview\n",
        bench["output_preview"],
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Main runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]devflow-lab · Mini Reviewer[/bold cyan]\n"
        "[dim]Full-stack agentic AI demo — FastAPI + Claude Skills[/dim]",
        border_style="cyan"
    ))

    # 1 · Start server
    console.print("\n[dim]Starting FastAPI server on :8080…[/dim]")
    start_server()
    console.print("[green]✓ Server ready[/green]\n")

    client = httpx.Client(base_url=BASE_URL, verify=False)

    # 2 · Health
    console.rule("[bold]1 · Health Check[/bold]")
    health = test_health(client)
    console.print(f"  Status : [green]{health['status']}[/green]")
    console.print(f"  Model  : [cyan]{health['model']}[/cyan]")
    console.print(f"  Skills : {health['skills_dir']}\n")

    # 3 · Skills
    console.rule("[bold]2 · Available Skills[/bold]")
    skills = test_skills(client)
    t = Table(show_header=True, header_style="bold cyan", box=None)
    t.add_column("Skill", style="cyan", min_width=25)
    t.add_column("Description")
    for s in skills["skills"]:
        t.add_row(s["name"], s["description"])
    console.print(t)
    console.print()

    # 4 · Code Review
    console.rule("[bold]3 · Code Review  (pr-reviewer skill)[/bold]")
    console.print("[dim]Sending buggy Python auth code to Claude…[/dim]")
    console.print(Syntax(BUGGY_CODE, "python", theme="monokai", line_numbers=True))
    console.print()

    t0 = time.time()
    review = test_review(client)
    console.print(f"[green]✓ Review received in {review['elapsed_sec']}s[/green]\n")
    console.print(Panel(review["review"], title="[bold]Claude's Review[/bold]",
                        border_style="green", padding=(1, 2)))

    # 5 · Benchmark
    console.rule("[bold]4 · Benchmark — Agentic AI vs Manual[/bold]")
    console.print(f"[dim]Task:[/dim] {BENCHMARK_TASK[:80]}…")
    console.print(f"[dim]Your estimate: 25 minutes. Let's see how fast Claude is…[/dim]\n")

    bench = test_benchmark(client)
    saved_pct = round((1 - (bench["agent_seconds"] / 60) / bench["manual_minutes"]) * 100, 1)

    bt = Table(show_header=False, box=None)
    bt.add_column("Label",  style="dim",        min_width=20)
    bt.add_column("Value",  style="bold green",  min_width=20)
    bt.add_row("Manual estimate",  f"{bench['manual_minutes']} minutes")
    bt.add_row("Agent took",       f"{bench['agent_seconds']} seconds")
    bt.add_row("Speedup",          bench["speedup"])
    bt.add_row("Time saved",       f"{saved_pct}%")
    console.print(bt)
    console.print()

    # 6 · Save report
    report_md = build_report(health, skills, review, bench)
    out_path  = Path(__file__).parent / "results.md"
    out_path.write_text(report_md)

    console.print(Rule(style="dim"))
    console.print(f"\n[bold green]✅ All tests passed![/bold green]")
    console.print(f"   Report saved → [bold]{out_path}[/bold]\n")

    return out_path


if __name__ == "__main__":
    main()
