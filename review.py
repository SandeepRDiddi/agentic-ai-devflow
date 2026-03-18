#!/usr/bin/env python3
"""
review.py — Agentic AI code reviewer powered by devflow-lab

Usage:
    python review.py <path-to-your-project>

Examples:
    python review.py ../SOLO_NODE
    python review.py ~/projects/my-app
    python review.py .

What it does:
    - Scans your project for Python files
    - Reviews each one using the pr-reviewer skill (Claude)
    - Saves a full Markdown report → review_report.md

Requirements:
    pip install anthropic rich httpx python-dotenv
    Add your ANTHROPIC_API_KEY to .env
"""

import os, sys, time
from pathlib import Path

# ── Load .env (overwrites empty env vars set by corp proxies) ────────────────
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
        if _k and _v and not os.environ.get(_k):
            os.environ[_k] = _v

# ── Check API key before importing anything else ─────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("\n❌  ANTHROPIC_API_KEY not found.")
    print("    1. Copy .env.example to .env")
    print("    2. Add your key: ANTHROPIC_API_KEY=sk-ant-...\n")
    sys.exit(1)

import httpx
import anthropic
from rich.console  import Console
from rich.panel    import Panel
from rich.rule     import Rule
from rich.table    import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ── Config ────────────────────────────────────────────────────────────────────
MODEL      = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SKILLS_DIR = Path(__file__).parent / "skills"
MAX_TOKENS = 1500
# Files to skip — not useful to review
SKIP_FILES = {"__init__.py", "setup.py", "conftest.py", "manage.py"}
# Max file size to send (characters) — avoids huge files timing out
MAX_CHARS  = 8000


# ── Load skill ────────────────────────────────────────────────────────────────
def load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.exists():
        console.print(f"[red]Skill '{name}' not found at {path}[/red]")
        sys.exit(1)
    return path.read_text()


# ── Claude call ───────────────────────────────────────────────────────────────
_client = None

def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            http_client=httpx.Client(verify=False),
        )
    return _client


def review_file(filepath: Path, skill: str) -> dict:
    code = filepath.read_text(errors="replace")
    if len(code) > MAX_CHARS:
        code = code[:MAX_CHARS] + f"\n\n... [truncated — file too large, showing first {MAX_CHARS} chars]"

    system = load_skill(skill)
    prompt = (
        f"Review this Python file: `{filepath.name}`\n\n"
        f"```python\n{code}\n```\n\n"
        "Be specific — reference actual function and variable names you see."
    )

    start = time.time()
    resp  = get_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = round(time.time() - start, 1)

    return {
        "file":    filepath.name,
        "path":    str(filepath),
        "elapsed": elapsed,
        "lines":   len(filepath.read_text(errors="replace").splitlines()),
        "review":  resp.content[0].text,
    }


# ── Find Python files in project ──────────────────────────────────────────────
def find_python_files(project_path: Path) -> list[Path]:
    files = []
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", "env",
                 "node_modules", ".tox", "dist", "build", ".eggs"}

    for py_file in sorted(project_path.rglob("*.py")):
        # Skip hidden/cache dirs
        if any(part in skip_dirs for part in py_file.parts):
            continue
        # Skip uninteresting files
        if py_file.name in SKIP_FILES:
            continue
        files.append(py_file)

    return files


# ── Build Markdown report ─────────────────────────────────────────────────────
def build_report(project_path: Path, results: list[dict]) -> str:
    from datetime import datetime
    ts            = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_manual  = len(results) * 45   # ~45 min per file for a human
    total_agent   = round(sum(r["elapsed"] for r in results), 1)
    total_saved   = round((1 - (total_agent / 60) / total_manual) * 100, 1)
    speedup       = round(total_manual / max(total_agent / 60, 0.001))

    lines = [
        f"# Agentic AI Code Review",
        f"**Project:** `{project_path.resolve().name}`  ",
        f"**Generated:** {ts}  ",
        f"**Model:** `{MODEL}`  ",
        f"**Files reviewed:** {len(results)}\n",
        "---\n",
        "## Summary\n",
        f"| | |",
        f"|---|---|",
        f"| Files reviewed | {len(results)} |",
        f"| Manual estimate | ~{total_manual} minutes |",
        f"| Agent completed in | {total_agent} seconds |",
        f"| Time saved | **{total_saved}%** |",
        f"| Speedup | **~{speedup}x faster** |\n",
        "---\n",
    ]

    for r in results:
        lines += [
            f"## `{r['file']}`",
            f"_{r['lines']} lines · reviewed in {r['elapsed']}s_\n",
            r["review"],
            "\n---\n",
        ]

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Parse argument ────────────────────────────────────────────────────────
    if len(sys.argv) < 2:
        console.print("\n[bold red]Usage:[/bold red]  python review.py <path-to-project>\n")
        console.print("  Example:  python review.py ../SOLO_NODE")
        console.print("  Example:  python review.py ~/projects/my-app\n")
        sys.exit(1)

    project_path = Path(sys.argv[1]).resolve()

    if not project_path.exists():
        console.print(f"\n[red]❌  Project folder not found: {project_path}[/red]\n")
        sys.exit(1)

    # ── Find files ────────────────────────────────────────────────────────────
    py_files = find_python_files(project_path)

    if not py_files:
        console.print(f"\n[yellow]No Python files found in {project_path}[/yellow]\n")
        sys.exit(0)

    # ── Header ────────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Agentic AI Code Review[/bold cyan]\n"
        f"[dim]Project: {project_path.name}  ·  {len(py_files)} Python files found[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Show files that will be reviewed
    console.print("[bold]Files to review:[/bold]")
    for f in py_files:
        console.print(f"  [cyan]▸[/cyan] {f.relative_to(project_path)}")
    console.print()

    # ── Review each file ──────────────────────────────────────────────────────
    results = []
    for i, filepath in enumerate(py_files, 1):
        console.rule(f"[bold]{i}/{len(py_files)} · {filepath.name}[/bold]")

        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                      transient=True, console=console) as progress:
            progress.add_task("Claude is reviewing via pr-reviewer skill...")
            result = review_file(filepath, "pr-reviewer")

        results.append(result)
        console.print(Panel(
            result["review"],
            title=f"[green]{filepath.name}[/green]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print(f"  ⏱  [green]{result['elapsed']}s[/green]  vs ~45 min manual\n")

    # ── Summary table ─────────────────────────────────────────────────────────
    console.rule("[bold cyan]Review Complete[/bold cyan]")
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("File",        style="cyan", min_width=25)
    table.add_column("Lines",       justify="right")
    table.add_column("Agent time",  justify="right", style="green")
    table.add_column("Manual est.", justify="right")

    total_time = 0
    for r in results:
        table.add_row(r["file"], str(r["lines"]), f"{r['elapsed']}s", "~45 min")
        total_time += r["elapsed"]

    table.add_row(
        f"[bold]TOTAL ({len(results)} files)[/bold]",
        "",
        f"[bold green]{round(total_time, 1)}s[/bold green]",
        f"[bold]~{len(results) * 45} min[/bold]",
    )
    console.print(table)

    # ── Save report ───────────────────────────────────────────────────────────
    report     = build_report(project_path, results)
    out_path   = Path(__file__).parent / "review_report.md"
    out_path.write_text(report)

    console.print()
    console.print(f"[bold green]✅  Report saved → review_report.md[/bold green]\n")


if __name__ == "__main__":
    main()
