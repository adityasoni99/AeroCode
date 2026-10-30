"""Aero-Code ProofLoop Interactive CLI."""
import os
from pathlib import Path
import sys
import threading
import time
import webbrowser

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aero_code.config import get_settings
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.report import VerificationVerdict
from aero_code.state import ProofLoopEvent, ProofLoopEventBus
from benchmarks.evaluate import BenchmarkSuite

console = Console()


@click.group()
def cli():
    """Aero-Code: Deterministic Autonomous Software Engineering Agent."""
    pass


@cli.command()
def cases():
    """List all available curated benchmark cases."""
    suite = BenchmarkSuite()
    case_list = suite.load_cases()

    table = Table(title="Aero-Code Seeded Benchmark Cases", border_style="cyan")
    table.add_column("Case ID", style="bold cyan", no_wrap=True)
    table.add_column("Target Package", style="magenta")
    table.add_column("Category", style="yellow")
    table.add_column("Title", style="white")

    for c in case_list:
        table.add_row(
            c.case_id,
            f"{c.issue.target_package} {c.issue.package_version}",
            c.metadata.get("category", "bug"),
            c.issue.title,
        )

    console.print(table)


@cli.command()
@click.option("--case", default="pydantic_v2_migration", help="Benchmark case ID to run")
@click.option("--mode", type=click.Choice(["demo", "live"]), default="demo", help="Execution mode")
@click.option("--web", is_flag=True, help="Launch web dashboard alongside run")
@click.option("--repo", default=None, help="Custom repository path")
def run(case: str, mode: str, web: bool, repo: str | None):
    """Execute the ProofLoop deterministic pipeline on an issue."""
    suite = BenchmarkSuite()
    case_obj = next((c for c in suite.load_cases() if c.case_id == case), None)

    if not case_obj:
        console.print(f"[bold red]Error:[/] Benchmark case '{case}' not found.")
        sys.exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]Aero-Code ProofLoop Engine[/]\n"
            f"[white]Target Case:[/] [bold yellow]{case}[/]\n"
            f"[white]Mode:[/] [bold green]{mode.upper()}[/]\n"
            f"[white]Issue:[/] {case_obj.issue.title}",
            border_style="cyan",
        )
    )

    bus = ProofLoopEventBus()

    def on_event(event: ProofLoopEvent):
        if event.event_type == "PHASE_CHANGE":
            phase = event.payload.get("phase", "")
            escalated = event.payload.get("escalated", False)
            tag = " [bold magenta](Escalated: Nemotron 550b Ultra)[/]" if escalated else ""
            console.print(f"  [bold blue]→ Phase:[/] [bold cyan]{phase}[/]{tag}")
        elif event.event_type == "GIT_GUARD_VERIFIED":
            console.print("  [bold green]✓ Git Guard:[/] Test suite & config immutability verified.")
        elif event.event_type == "RESEARCH_COMPLETE":
            citations = event.payload.get("citations", [])
            console.print(f"  [bold yellow]🔍 Tavily:[/] {len(citations)} citations retrieved.")
        elif event.event_type == "PATCH_GENERATED":
            console.print("  [bold green]⚡ Patch Engineer:[/] Synthesized unified diff and isolated regression test.")

    bus.subscribe(on_event)

    if web:
        from aero_code.web.server import create_app
        import uvicorn

        def run_server():
            app = create_app(event_bus=bus)
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(1.0)
        webbrowser.open("http://127.0.0.1:8000")
        console.print("[dim]Web dashboard launched at http://127.0.0.1:8000[/]")

    orchestrator = ProofLoopOrchestrator(mode=mode, event_bus=bus)
    result = suite.run_case(case_obj, orchestrator=orchestrator)
    report = result["report"]

    # Display Double-Verification Matrix
    matrix_table = Table(title="Double-Verification Matrix Results", border_style="green")
    matrix_table.add_column("Rule", style="bold white")
    matrix_table.add_column("Result", style="bold")

    matrix_table.add_row(
        "1. Bug Reproduction (Regression test failed on baseline)",
        "[green]PASSED[/]" if result["reproduced"] else "[red]FAILED[/]",
    )
    matrix_table.add_row(
        "2. Bug Resolution (Regression test passed on patch)",
        "[green]PASSED[/]" if result["repaired"] else "[red]FAILED[/]",
    )
    matrix_table.add_row(
        "3. Zero Regressions (Existing test suite passing)",
        "[green]PASSED[/]" if report.baseline_suite_passed else "[red]FAILED[/]",
    )
    matrix_table.add_row(
        "4. Git Guard Immutability (Baseline tests & build config)",
        "[green]PASSED[/]" if report.git_guard_passed else "[red]FAILED[/]",
    )

    console.print(matrix_table)

    verdict_color = "bold green" if report.verdict == VerificationVerdict.VERIFIED else "bold red"
    console.print(
        Panel(
            f"ProofLoop Execution Finished\n"
            f"Verdict: [{verdict_color}]{report.verdict.value}[/]\n"
            f"Run ID: {report.run_id}",
            border_style="green" if report.verdict == VerificationVerdict.VERIFIED else "red",
        )
    )


@cli.command()
@click.option("--mode", type=click.Choice(["demo", "live"]), default="demo")
def evaluate(mode: str):
    """Run full evaluation suite across all benchmark cases."""
    suite = BenchmarkSuite()
    console.print("[bold cyan]Evaluating Aero-Code on all benchmark cases...[/]")

    bus = ProofLoopEventBus()
    orchestrator = ProofLoopOrchestrator(mode=mode, event_bus=bus)
    metrics = suite.run_all(orchestrator=orchestrator)

    table = Table(title="Aero-Code Benchmark Suite Evaluation Metrics", border_style="cyan")
    table.add_column("Metric", style="bold white")
    table.add_column("Count / Rate", style="bold cyan")

    table.add_row("Total Cases", str(metrics.total_cases))
    table.add_row("Reproduction Rate", f"{metrics.reproduction_rate * 100:.1f}% ({metrics.reproduced_count}/{metrics.total_cases})")
    table.add_row("Repair Rate", f"{metrics.repair_rate * 100:.1f}% ({metrics.repaired_count}/{metrics.total_cases})")
    table.add_row("Verification Rate (Double-Verified)", f"{metrics.verification_rate * 100:.1f}% ({metrics.verified_count}/{metrics.total_cases})")

    console.print(table)


@cli.command()
@click.option("--port", default=8000, help="Port to bind server to")
@click.option("--host", default="127.0.0.1", help="Host interface")
def web(port: int, host: str):
    """Launch the Aero-Code real-time SSE Web Dashboard."""
    import uvicorn
    from aero_code.web.server import create_app

    app = create_app()
    console.print(f"[bold green]Starting Aero-Code Web Dashboard on http://{host}:{port}[/]")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
