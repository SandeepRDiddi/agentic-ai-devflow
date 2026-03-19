#!/usr/bin/env python3
"""
benchmark_report.py — Agentic AI vs Manual: Business Performance Report

Usage:
    python benchmark_report.py <path-to-your-project>

Example:
    python benchmark_report.py ../SOLO_NODE

What it does:
    1. Reviews every Python file using the pr-reviewer Claude skill
    2. Records real wall-clock agent time vs industry manual estimates
    3. Prints a rich terminal dashboard with bar charts
    4. Saves an interactive HTML report → benchmark_report.html
       (open in any browser — ready to show in a business meeting)

Requirements:
    pip install anthropic rich httpx python-dotenv plotly
"""

import os, sys, time
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
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

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("\n❌  ANTHROPIC_API_KEY not found. Add it to your .env file.\n")
    sys.exit(1)

# ── Install deps if missing ───────────────────────────────────────────────────
import subprocess
for pkg in ["anthropic", "rich", "httpx", "plotly"]:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg,
                        "--break-system-packages", "-q"])

import httpx
import anthropic
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rich.console   import Console
from rich.panel     import Panel
from rich.table     import Table
from rich.rule      import Rule
from rich.progress  import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text      import Text
from rich           import box

console = Console()

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL            = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SKILLS_DIR       = Path(__file__).parent / "skills"
DEVELOPER_RATE   = 150        # USD per hour (industry average senior dev)
MANUAL_MIN_FILE  = 45         # minutes a human takes to review one file
MAX_CHARS        = 8000
SKIP_DIRS        = {"__pycache__", ".git", ".venv", "venv", "env",
                    "node_modules", ".tox", "dist", "build", ".eggs"}
SKIP_FILES       = {"__init__.py", "setup.py", "conftest.py", "manage.py"}

# ── Anthropic client ──────────────────────────────────────────────────────────
_client = None
def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            http_client=httpx.Client(verify=False),
        )
    return _client

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_skill(name):
    p = SKILLS_DIR / name / "SKILL.md"
    if not p.exists():
        console.print(f"[red]Skill not found: {p}[/red]"); sys.exit(1)
    return p.read_text()

def find_python_files(root: Path):
    files = []
    for f in sorted(root.rglob("*.py")):
        if any(p in SKIP_DIRS for p in f.parts): continue
        if f.name in SKIP_FILES: continue
        files.append(f)
    return files

def review_file(filepath: Path, skill_text: str) -> dict:
    code = filepath.read_text(errors="replace")
    if len(code) > MAX_CHARS:
        code = code[:MAX_CHARS] + "\n\n...[truncated]"
    lines = len(filepath.read_text(errors="replace").splitlines())

    prompt = (f"Review this Python file: `{filepath.name}`\n\n"
              f"```python\n{code}\n```\n\n"
              "Reference actual function/variable names you see.")

    start = time.time()
    resp  = get_client().messages.create(
        model=MODEL, max_tokens=1500, system=skill_text,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = round(time.time() - start, 1)

    # Count issues mentioned (rough proxy for review depth)
    review_text = resp.content[0].text
    blockers     = review_text.count("🚫")
    suggestions  = review_text.count("💡")

    return {
        "file":        filepath.name,
        "lines":       lines,
        "elapsed_sec": elapsed,
        "manual_min":  MANUAL_MIN_FILE,
        "agent_min":   round(elapsed / 60, 3),
        "saved_min":   round(MANUAL_MIN_FILE - elapsed / 60, 1),
        "saved_pct":   round((1 - elapsed / 60 / MANUAL_MIN_FILE) * 100, 1),
        "speedup":     round(MANUAL_MIN_FILE / max(elapsed / 60, 0.001)),
        "cost_manual": round(MANUAL_MIN_FILE / 60 * DEVELOPER_RATE, 2),
        "cost_agent":  round(elapsed / 3600 * DEVELOPER_RATE, 4),
        "blockers":    blockers,
        "suggestions": suggestions,
        "review":      review_text,
    }


# ── Terminal dashboard ────────────────────────────────────────────────────────
def print_terminal_dashboard(project_name: str, results: list):
    total_manual_min  = sum(r["manual_min"]  for r in results)
    total_agent_min   = round(sum(r["agent_min"]  for r in results), 2)
    total_saved_min   = round(total_manual_min - total_agent_min, 1)
    total_saved_pct   = round((1 - total_agent_min / total_manual_min) * 100, 1)
    total_speedup     = round(total_manual_min / max(total_agent_min, 0.001))
    total_cost_manual = sum(r["cost_manual"] for r in results)
    total_cost_agent  = round(sum(r["cost_agent"]  for r in results), 2)
    money_saved       = round(total_cost_manual - total_cost_agent, 2)

    # ── Header ────────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Agentic AI Performance Report[/bold cyan]\n"
        f"[dim]Project: {project_name}  ·  {len(results)} files  ·  "
        f"Model: {MODEL}[/dim]",
        border_style="cyan",
    ))

    # ── KPI boxes ─────────────────────────────────────────────────────────────
    console.print()
    kpi = Table(box=box.SIMPLE, show_header=False, padding=(0, 3))
    kpi.add_column(justify="center", min_width=18)
    kpi.add_column(justify="center", min_width=18)
    kpi.add_column(justify="center", min_width=18)
    kpi.add_column(justify="center", min_width=18)
    kpi.add_row(
        Panel(f"[bold green]{total_saved_pct}%[/bold green]\nTime Saved",       border_style="green"),
        Panel(f"[bold cyan]~{total_speedup}x[/bold cyan]\nFaster",              border_style="cyan"),
        Panel(f"[bold yellow]${money_saved:,.0f}[/bold yellow]\nCost Saved",    border_style="yellow"),
        Panel(f"[bold magenta]{total_manual_min} min[/bold magenta]\nReclaimed", border_style="magenta"),
    )
    console.print(kpi)

    # ── Per-file bar chart (terminal) ─────────────────────────────────────────
    console.rule("[bold]Manual vs Agent — Per File[/bold]")
    max_manual = max(r["manual_min"] for r in results)

    for r in results:
        bar_manual = int(r["manual_min"] / max_manual * 40)
        bar_agent  = max(int(r["agent_min"] / max_manual * 40), 1)
        console.print(f"  [cyan]{r['file']:<20}[/cyan]")
        console.print(f"    [red]Manual [/red] {'█' * bar_manual} {r['manual_min']} min")
        console.print(f"    [green]Agent  [/green] {'█' * bar_agent} {r['elapsed_sec']}s")
        console.print()

    # ── Summary table ─────────────────────────────────────────────────────────
    console.rule("[bold]Summary[/bold]")
    t = Table(show_header=True, header_style="bold cyan",
              box=box.ROUNDED, padding=(0, 1))
    t.add_column("File",        style="cyan",  min_width=20)
    t.add_column("Lines",       justify="right")
    t.add_column("Manual",      justify="right", style="red")
    t.add_column("Agent",       justify="right", style="green")
    t.add_column("Saved",       justify="right", style="bold green")
    t.add_column("Speedup",     justify="right", style="bold")
    t.add_column("$ Saved",     justify="right", style="yellow")
    t.add_column("Issues",      justify="right")

    for r in results:
        t.add_row(
            r["file"],
            str(r["lines"]),
            f"{r['manual_min']} min",
            f"{r['elapsed_sec']}s",
            f"{r['saved_pct']}%",
            f"~{r['speedup']}x",
            f"${r['cost_manual'] - r['cost_agent']:.0f}",
            f"🚫{r['blockers']} 💡{r['suggestions']}",
        )

    t.add_section()
    t.add_row(
        f"[bold]TOTAL ({len(results)} files)[/bold]", "",
        f"[bold]{total_manual_min} min[/bold]",
        f"[bold]{round(total_agent_min * 60)}s[/bold]",
        f"[bold]{total_saved_pct}%[/bold]",
        f"[bold]~{total_speedup}x[/bold]",
        f"[bold yellow]${money_saved:,.0f}[/bold yellow]", "",
    )
    console.print(t)
    console.print()


# ── HTML report with Plotly charts ────────────────────────────────────────────
def build_html_report(project_name: str, results: list) -> str:
    from datetime import datetime

    total_manual_min  = sum(r["manual_min"]  for r in results)
    total_agent_sec   = round(sum(r["elapsed_sec"] for r in results), 1)
    total_agent_min   = round(total_agent_sec / 60, 2)
    total_saved_pct   = round((1 - total_agent_min / total_manual_min) * 100, 1)
    total_speedup     = round(total_manual_min / max(total_agent_min, 0.001))
    total_cost_manual = sum(r["cost_manual"] for r in results)
    total_cost_agent  = round(sum(r["cost_agent"]  for r in results), 2)
    money_saved       = round(total_cost_manual - total_cost_agent, 2)
    ts                = datetime.now().strftime("%B %d, %Y  %H:%M")
    files             = [r["file"] for r in results]

    # Chart 1: Manual vs Agent time per file
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name="Manual Review",
        x=files,
        y=[r["manual_min"] for r in results],
        marker_color="#ef4444",
        text=[f"{r['manual_min']} min" for r in results],
        textposition="outside",
    ))
    fig1.add_trace(go.Bar(
        name="AI Agent",
        x=files,
        y=[round(r["agent_min"], 2) for r in results],
        marker_color="#22c55e",
        text=[f"{r['elapsed_sec']}s" for r in results],
        textposition="outside",
    ))
    fig1.update_layout(
        title="Manual Review vs AI Agent — Time Per File",
        barmode="group",
        yaxis_title="Minutes",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font_color="#e2e8f0",
        legend=dict(bgcolor="#1e293b"),
        title_font_size=18,
    )

    # Chart 2: Time saved % per file
    fig2 = go.Figure(go.Bar(
        x=files,
        y=[r["saved_pct"] for r in results],
        marker=dict(
            color=[r["saved_pct"] for r in results],
            colorscale="Greens",
            showscale=False,
        ),
        text=[f"{r['saved_pct']}%" for r in results],
        textposition="outside",
    ))
    fig2.update_layout(
        title="Time Saved Per File (%)",
        yaxis_title="% Time Saved",
        yaxis_range=[0, 105],
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font_color="#e2e8f0",
        title_font_size=18,
    )

    # Chart 3: Cost manual vs agent
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Manual Cost",
        x=files,
        y=[r["cost_manual"] for r in results],
        marker_color="#f97316",
        text=[f"${r['cost_manual']:.0f}" for r in results],
        textposition="outside",
    ))
    fig3.add_trace(go.Bar(
        name="Agent Cost",
        x=files,
        y=[r["cost_agent"] for r in results],
        marker_color="#3b82f6",
        text=[f"${r['cost_agent']:.2f}" for r in results],
        textposition="outside",
    ))
    fig3.update_layout(
        title=f"Cost Comparison (@ ${DEVELOPER_RATE}/hr developer rate)",
        barmode="group",
        yaxis_title="USD ($)",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font_color="#e2e8f0",
        legend=dict(bgcolor="#1e293b"),
        title_font_size=18,
    )

    # Chart 4: Speedup multiplier
    fig4 = go.Figure(go.Bar(
        x=files,
        y=[r["speedup"] for r in results],
        marker=dict(
            color=[r["speedup"] for r in results],
            colorscale="Blues",
            showscale=False,
        ),
        text=[f"~{r['speedup']}x" for r in results],
        textposition="outside",
    ))
    fig4.update_layout(
        title="Speedup Multiplier Per File (Agent vs Manual)",
        yaxis_title="× Faster",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font_color="#e2e8f0",
        title_font_size=18,
    )

    # Rows table HTML
    rows_html = ""
    for r in results:
        rows_html += f"""
        <tr>
          <td>{r['file']}</td>
          <td>{r['lines']}</td>
          <td class="red">{r['manual_min']} min</td>
          <td class="green">{r['elapsed_sec']}s</td>
          <td class="green bold">{r['saved_pct']}%</td>
          <td class="cyan bold">~{r['speedup']}x</td>
          <td class="yellow">${r['cost_manual']:.0f}</td>
          <td class="blue">${r['cost_agent']:.4f}</td>
          <td class="yellow bold">${r['cost_manual'] - r['cost_agent']:.2f}</td>
        </tr>"""

    chart1_html = fig1.to_html(full_html=False, include_plotlyjs=False)
    chart2_html = fig2.to_html(full_html=False, include_plotlyjs=False)
    chart3_html = fig3.to_html(full_html=False, include_plotlyjs=False)
    chart4_html = fig4.to_html(full_html=False, include_plotlyjs=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agentic AI Performance Report — {project_name}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #020617; color: #e2e8f0; padding: 2rem; }}
  h1   {{ font-size: 2rem; color: #38bdf8; margin-bottom: 0.25rem; }}
  h2   {{ font-size: 1.25rem; color: #94a3b8; margin: 2rem 0 1rem; }}
  .sub {{ color: #64748b; font-size: 0.95rem; margin-bottom: 2rem; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0 2.5rem; }}
  .kpi {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 12px;
           padding: 1.5rem; text-align: center; }}
  .kpi .value {{ font-size: 2.5rem; font-weight: 800; line-height: 1; }}
  .kpi .label {{ font-size: 0.85rem; color: #64748b; margin-top: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .green  {{ color: #22c55e; }}
  .cyan   {{ color: #38bdf8; }}
  .yellow {{ color: #eab308; }}
  .purple {{ color: #a855f7; }}
  .red    {{ color: #ef4444; }}
  .blue   {{ color: #3b82f6; }}
  .bold   {{ font-weight: 700; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 1.5rem 0; }}
  .chart-box {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0;
           background: #0f172a; border-radius: 12px; overflow: hidden; }}
  th {{ background: #1e293b; color: #94a3b8; padding: 0.75rem 1rem;
        text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #1e293b; font-size: 0.9rem; }}
  tr:last-child td {{ border-bottom: none; font-weight: 700; background: #1e293b; }}
  .footer {{ text-align: center; color: #334155; font-size: 0.8rem; margin-top: 3rem; }}
  @media (max-width: 900px) {{
    .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
    .charts   {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<h1>⚡ Agentic AI Performance Report</h1>
<p class="sub">Project: <strong>{project_name}</strong> &nbsp;·&nbsp; Generated: {ts} &nbsp;·&nbsp; Model: {MODEL}</p>

<!-- KPIs -->
<div class="kpi-grid">
  <div class="kpi">
    <div class="value green">{total_saved_pct}%</div>
    <div class="label">Time Saved</div>
  </div>
  <div class="kpi">
    <div class="value cyan">~{total_speedup}x</div>
    <div class="label">Faster than Manual</div>
  </div>
  <div class="kpi">
    <div class="value yellow">${money_saved:,.0f}</div>
    <div class="label">Developer Cost Saved</div>
  </div>
  <div class="kpi">
    <div class="value purple">{total_manual_min} min</div>
    <div class="label">Productive Time Reclaimed</div>
  </div>
</div>

<!-- Charts row 1 -->
<h2>Performance Comparison</h2>
<div class="charts">
  <div class="chart-box">{chart1_html}</div>
  <div class="chart-box">{chart2_html}</div>
</div>

<!-- Charts row 2 -->
<div class="charts">
  <div class="chart-box">{chart3_html}</div>
  <div class="chart-box">{chart4_html}</div>
</div>

<!-- Detail table -->
<h2>File-by-File Breakdown</h2>
<table>
  <thead>
    <tr>
      <th>File</th><th>Lines</th><th>Manual</th><th>Agent</th>
      <th>Saved %</th><th>Speedup</th><th>Manual Cost</th><th>Agent Cost</th><th>$ Saved</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
    <tr>
      <td>TOTAL ({len(results)} files)</td><td></td>
      <td class="red">{total_manual_min} min</td>
      <td class="green">{total_agent_sec}s</td>
      <td class="green bold">{total_saved_pct}%</td>
      <td class="cyan bold">~{total_speedup}x</td>
      <td class="yellow">${total_cost_manual:,.0f}</td>
      <td class="blue">${total_cost_agent:.2f}</td>
      <td class="yellow bold">${money_saved:,.0f}</td>
    </tr>
  </tbody>
</table>

<div class="footer">
  Developer rate assumed: ${DEVELOPER_RATE}/hr &nbsp;·&nbsp;
  Manual estimate: {MANUAL_MIN_FILE} min/file &nbsp;·&nbsp;
  Powered by devflow-lab + Claude {MODEL}
</div>

</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        console.print("\n[bold red]Usage:[/bold red]  python benchmark_report.py <path-to-project>\n")
        console.print("  Example:  python benchmark_report.py ../SOLO_NODE\n")
        sys.exit(1)

    project_path = Path(sys.argv[1]).resolve()
    if not project_path.exists():
        console.print(f"\n[red]❌  Not found: {project_path}[/red]\n"); sys.exit(1)

    py_files = find_python_files(project_path)
    if not py_files:
        console.print(f"\n[yellow]No Python files found in {project_path}[/yellow]\n"); sys.exit(0)

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Agentic AI Benchmark[/bold cyan]\n"
        f"[dim]Project: {project_path.name}  ·  {len(py_files)} files  ·  "
        f"Developer rate: ${DEVELOPER_RATE}/hr[/dim]",
        border_style="cyan",
    ))

    skill_text = load_skill("pr-reviewer")
    results    = []

    for i, filepath in enumerate(py_files, 1):
        with Progress(SpinnerColumn(), TextColumn(
            f"  [cyan]{i}/{len(py_files)}[/cyan] Reviewing [bold]{filepath.name}[/bold]..."
        ), transient=True, console=console) as p:
            p.add_task("")
            result = review_file(filepath, skill_text)
        results.append(result)
        console.print(
            f"  ✓ [cyan]{filepath.name}[/cyan]  "
            f"[green]{result['elapsed_sec']}s[/green]  vs  "
            f"[red]{result['manual_min']} min manual[/red]  "
            f"→  saved [bold green]{result['saved_pct']}%[/bold green]"
        )

    console.print()

    # Terminal dashboard
    print_terminal_dashboard(project_path.name, results)

    # HTML report
    html    = build_html_report(project_path.name, results)
    outpath = Path(__file__).parent / "benchmark_report.html"
    outpath.write_text(html)

    console.print(Rule(style="dim"))
    console.print(f"\n[bold green]✅  HTML report saved → benchmark_report.html[/bold green]")
    console.print(f"[dim]Open in your browser to see interactive charts[/dim]\n")


if __name__ == "__main__":
    main()
