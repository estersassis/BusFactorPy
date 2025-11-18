import typer
from typing import Optional
from rich.console import Console
from busfactorpy.core.miner import GitMiner
from busfactorpy.core.calculator import BusFactorCalculator
from busfactorpy.core.ignore import BusFactorIgnore
from busfactorpy.output.reporter import ConsoleReporter
from busfactorpy.output.visualizer import BusFactorVisualizer
from busfactorpy import __version__

app = typer.Typer(
    name="busfactorpy",
    help="A command-line tool to measure the Bus Factor of a Git repository."
)
console = Console()

@app.command()
def version():
    """
    Exibe a versão instalada do BusFactorPy.
    """
    console.print(f"BusFactorPy Versão: [bold green]{__version__}[/bold green]")
    typer.Exit()

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
        help="Path to the exclusion file (default: .busfactorignore)."
    ),
    metric: str = typer.Option(
        "churn",
        "--metric",
        "-m",
        help="Metric: commit-number, churn, entropy, hhi, ownership.",
        case_sensitive=False
    ),
    threshold: float = typer.Option(
        0.8,
        "--threshold",
        "-t",
        help="Threshold for High Risk classification (0.0 to 1.0). Default is 0.8."
    ),
    group_by: str = typer.Option(
        "file",
        "--group-by",
        "-g",
        help="Group results by 'file' or 'directory'.",
        case_sensitive=False
    ),
    depth: int = typer.Option(
        1,
        "--depth",
        "-d",
        help="Directory depth when grouping by directory (only valid with --group-by directory)."
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Limit analysis to a subdirectory (path relative to repo root). Example: src/ or src/utils"
    )
):
    """
    Executes the Bus Factor analysis on a given Git repository.
    """
    console.print(f"[bold cyan]Analysing repository:[/bold cyan] {repository}")
    
    try:
        ignorer = BusFactorIgnore(ignore_file)
        console.print(f"[bold yellow]Excluding files based on:[/bold yellow] {ignore_file}")
    except Exception as e:
        console.print(f"[bold red]ERROR loading ignore file:[/bold red] {e}")
        raise typer.Exit(code=1)

    valid_metrics = {"churn", "entropy", "hhi", "ownership", "commit-number"}
    if metric.lower() not in valid_metrics:
        console.print(
            f"[bold red]Invalid metric:[/bold red] {metric}. "
            f"Valid options: {', '.join(valid_metrics)}"
        )
        raise typer.Exit(code=1)
    
    if not (0.0 < threshold <= 1.0):
         console.print(f"[bold red]Invalid threshold:[/bold red] {threshold}. Must be between 0.0 and 1.0")
         raise typer.Exit(code=1)

    valid_group_by = {"file", "directory"}
    group_by = group_by.lower()
    if group_by not in valid_group_by:
        console.print(
            f"[bold red]Invalid group-by:[/bold red] {group_by}. "
            f"Valid options: file, directory"
        )
        raise typer.Exit(code=1)

    if group_by == "directory" and depth < 1:
        console.print(
            f"[bold red]Invalid depth:[/bold red] {depth}. Must be an integer >= 1 when grouping by directory."
        )
        raise typer.Exit(code=1)

    normalized_scope = None
    if scope:
        # Normaliza separadores e remove barras finais/iniciais redundantes
        normalized_scope = scope.strip().replace("\\", "/").strip("/")
        if normalized_scope == "":
            normalized_scope = None

    # Mensagens informativas (ainda sem alterar lógica de cálculo)
    if group_by == "directory":
        console.print(f"[bold cyan]Grouping by:[/bold cyan] directory (depth={depth})")
    else:
        console.print(f"[bold cyan]Grouping by:[/bold cyan] file")

    if normalized_scope:
        console.print(f"[bold cyan]Scope:[/bold cyan] {normalized_scope}/")
    else:
        console.print(f"[bold cyan]Scope:[/bold cyan] repository root")

    # Mineração de Dados (Extraction)
    try:
        miner = GitMiner(repository, ignorer, normalized_scope)
        commit_data = miner.mine_commit_history()
    except Exception as e:
        console.print(f"[bold red]ERROR during mining:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Verifica se escopo esvaziou totalmente os dados
    if normalized_scope and commit_data.empty:
        console.print(
            f"[bold yellow]No files found under scope:[/bold yellow] {normalized_scope}/. "
            "Analysis aborted."
        )
        raise typer.Exit(code=0)
    
    # Cálculo do Bus Factor
    if not commit_data.empty:
        # Passamos o threshold para o calculator
        calculator = BusFactorCalculator(
            commit_data, 
            metric=metric.lower(), 
            threshold=threshold
        )
        bus_factor_results = calculator.calculate()
        
        reporter = ConsoleReporter(bus_factor_results)
        
        if output_format == "summary":
            reporter.generate_cli_summary(n_top=n_top)
        elif output_format in ["csv", "json"]:
            reporter.export_report(format=output_format)
        
        visualizer = BusFactorVisualizer()
        visualizer.generate_top_n_bar_chart(results_df=bus_factor_results, n_top=n_top)
    else:
        console.print("[yellow]No relevant commit data found. Analysis aborted.[/yellow]")

if __name__ == "__main__":
    app()