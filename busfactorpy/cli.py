import typer
from rich.console import Console
from core.miner import GitMiner
from core.calculator import BusFactorCalculator
from output.reporter import ConsoleReporter

app = typer.Typer(
    name="busfactorpy",
    help="A command-line tool to measure the Bus Factor of a Git repository."
)
console = Console()

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
):
    """
    Executes the Bus Factor analysis on a given Git repository.
    """
    console.print(f"[bold cyan]Analysing repository:[/bold cyan] {repository}")

    # Mineração de Dados (Extraction)
    try:
        miner = GitMiner(repository)
        commit_data = miner.mine_commit_history()
    except Exception as e:
        console.print(f"[bold red]ERROR during mining:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Cálculo do Bus Factor
    if not commit_data.empty:
        calculator = BusFactorCalculator(commit_data)
        bus_factor_results = calculator.calculate()
        
        reporter = ConsoleReporter(bus_factor_results)
        
        if output_format == "summary":
            reporter.generate_cli_summary(n_top=n_top)
        elif output_format in ["csv", "json"]:
            reporter.export_report(format=output_format)
        
        # visualizer.generate_chart(bus_factor_results)
    else:
        console.print("[yellow]No relevant commit data found. Analysis aborted.[/yellow]")

if __name__ == "__main__":
    app()