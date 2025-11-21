import typer
from typing import Optional
from datetime import datetime
from rich.console import Console
from busfactorpy.core.miner import GitMiner
from busfactorpy.core.calculator import BusFactorCalculator
from busfactorpy.core.trend import TrendAnalyzer
from busfactorpy.core.ignore import BusFactorIgnore
from busfactorpy.output.reporter import ConsoleReporter
from busfactorpy.output.visualizer import BusFactorVisualizer
from busfactorpy import __version__
import pandas as pd

app = typer.Typer(
    name="busfactorpy",
    help="A command-line tool to measure the Bus Factor of a Git repository.",
)
console = Console()


@app.command()
def version():
    """
    Exibe a versão instalada do BusFactorPy.
    """
    console.print(f"BusFactorPy Versão: [bold green]{__version__}[/bold green]")
    raise typer.Exit()


@app.command()
def analyze(
    repository: str = typer.Argument(
        ..., help="Local path or GitHub URL of the repository to analyze."
    ),
    output_format: str = typer.Option(
        "summary", "--format", "-f", help="Output format: summary, csv, or json."
    ),
    n_top: int = typer.Option(
        10, "--top-n", "-n", help="Number of top risky files to report."
    ),
    ignore_file: str = typer.Option(
        ".busfactorignore",
        "--ignore-file",
        help="Path to the exclusion file (default: .busfactorignore).",
    ),
    metric: str = typer.Option(
        "churn",
        "--metric",
        "-m",
        help="Metric: commit-number, churn, entropy, hhi, ownership.",
        case_sensitive=False,
    ),
    threshold: float = typer.Option(
        0.8,
        "--threshold",
        "-t",
        help="Threshold for High Risk classification (0.0 to 1.0). Default is 0.8.",
    ),
    group_by: str = typer.Option(
        "file",
        "--group-by",
        "-g",
        help="Group results by 'file' or 'directory'.",
        case_sensitive=False,
    ),
    depth: int = typer.Option(
        1,
        "--depth",
        "-d",
        help="Directory depth when grouping by directory (only valid with --group-by directory).",
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Limit analysis to a subdirectory (path relative to repo root). Example: src/ or src/utils",
    ),
    trend: bool = typer.Option(
        False, "--trend", help="Enable trend analysis mode (evolution over time)."
    ),
    since: Optional[str] = typer.Option(
        None,
        help="Start date for analysis (YYYY-MM-DD). Defaults to beginning of repo or window calc.",
    ),
    until: Optional[str] = typer.Option(
        None, help="End date for analysis (YYYY-MM-DD). Defaults to today."
    ),
    window: int = typer.Option(
        180, "--window", help="Sliding window size in days for trend analysis."
    ),
    step: int = typer.Option(
        30, "--step", help="Step size in days for trend analysis iteration."
    ),
):
    """
    Executes the Bus Factor analysis on a given Git repository.
    """
    console.print(f"[bold cyan]Analysing repository:[/bold cyan] {repository}")

    start_dt = None
    end_dt = datetime.now()

    if since:
        try:
            start_dt = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            console.print(
                "[bold red]Invalid date format for --since. Use YYYY-MM-DD.[/bold red]"
            )
            raise typer.Exit(code=1)

    if until:
        try:
            end_dt = datetime.strptime(until, "%Y-%m-%d")
        except ValueError:
            console.print(
                "[bold red]Invalid date format for --until. Use YYYY-MM-DD.[/bold red]"
            )
            raise typer.Exit(code=1)

    if not (0.0 < threshold <= 1.0):
        console.print(
            f"[bold red]Invalid threshold:[/bold red] {threshold}. Must be between 0.0 and 1.0"
        )
        raise typer.Exit(code=1)

    valid_metrics = {"churn", "entropy", "hhi", "ownership", "commit-number"}
    if metric.lower() not in valid_metrics:
        console.print(
            f"[bold red]Invalid metric:[/bold red] {metric}. "
            f"Valid options: {', '.join(valid_metrics)}"
        )
        raise typer.Exit(code=1)

    valid_group_by = {"file", "directory"}
    group_by_lower = group_by.lower()
    if group_by_lower not in valid_group_by:
        console.print(
            f"[bold red]Invalid group-by:[/bold red] {group_by}. "
            "Valid options: file, directory"
        )
        raise typer.Exit(code=1)

    if group_by_lower == "directory" and depth < 1:
        console.print(
            f"[bold red]Invalid depth:[/bold red] {depth}. Must be an integer >= 1 when grouping by directory."
        )
        raise typer.Exit(code=1)

    try:
        ignorer = BusFactorIgnore(ignore_file)
        console.print(
            f"[bold yellow]Excluding files based on:[/bold yellow] {ignore_file}"
        )
    except Exception as e:
        console.print(f"[bold red]ERROR loading ignore file:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        miner = GitMiner(repository, ignorer, scope)
        commit_data = miner.mine_commit_history()

        if "date" not in commit_data.columns:
            if trend:
                console.print("\n[bold red]ERROR: Commit dates are missing![/bold red]")
                console.print(
                    "[yellow]The current GitMiner implementation does not extract commit dates.[/yellow]"
                )
                raise typer.Exit(code=1)
        else:
            commit_data["date"] = pd.to_datetime(commit_data["date"], utc=True)
            commit_data["date"] = commit_data["date"].dt.tz_localize(None)

    except Exception as e:
        console.print(f"[bold red]ERROR during mining:[/bold red] {e}")
        raise typer.Exit(code=1)

    if commit_data.empty:
        console.print("[yellow]No commit data found. Analysis aborted.[/yellow]")
        raise typer.Exit(code=0)

    if trend:
        console.print("[bold magenta]Running Trend Analysis...[/bold magenta]")
        console.print(f"Window: {window} days | Step: {step} days")

        if not start_dt:
            start_dt = commit_data["date"].min()
            console.print(f"Auto-detected start date: {start_dt.date()}")

        calc_params = {
            "metric": metric.lower(),
            "threshold": threshold,
            "group_by": group_by_lower,
            "depth": depth,
        }

        trend_analyzer = TrendAnalyzer(commit_data, calc_params)
        trend_df = trend_analyzer.analyze(
            start_date=start_dt, end_date=end_dt, window_days=window, step_days=step
        )

        if trend_df.empty:
            console.print(
                "[red]Trend analysis produced no data points. Check date ranges.[/red]"
            )
        else:
            console.print("\n[bold]Trend Summary:[/bold]")
            console.print(trend_df.to_string(index=False))

            visualizer = BusFactorVisualizer()
            visualizer.plot_trend(trend_df)

    else:
        filtered_data = commit_data
        if "date" in filtered_data.columns:
            if start_dt:
                filtered_data = filtered_data[filtered_data["date"] >= start_dt]
            if until:
                filtered_data = filtered_data[filtered_data["date"] <= end_dt]

        if filtered_data.empty:
            console.print(
                "[red]No commits found (possibly due to date filtering).[/red]"
            )
            raise typer.Exit(code=0)

        calculator = BusFactorCalculator(
            filtered_data,
            metric=metric.lower(),
            threshold=threshold,
            group_by=group_by_lower,
            depth=depth,
        )
        bus_factor_results = calculator.calculate()

        reporter = ConsoleReporter(bus_factor_results)

        if output_format == "summary":
            reporter.generate_cli_summary(n_top=n_top)
        elif output_format in ["csv", "json"]:
            reporter.export_report(format=output_format)

        visualizer = BusFactorVisualizer()
        visualizer.generate_top_n_bar_chart(results_df=bus_factor_results, n_top=n_top)


if __name__ == "__main__":
    app()
