import pandas as pd
import os
from rich.console import Console
from rich.table import Table


class ConsoleReporter:
    """
    Generates CSV/JSON reports and CLI summaries using Pandas and Rich.
    """

    def __init__(self, results_df: pd.DataFrame):
        self.results = results_df
        self.console = Console()
        self.output_dir = "reports"

    def _get_risk_style(self, risk_class: str) -> str:
        """Maps risk classes to Rich console styles."""
        styles = {
            "Critical": "bold white on red",
            "High": "bold red",
            "Medium": "bold yellow",
            "Low": "green",
        }
        return styles.get(risk_class, "default")

    def generate_cli_summary(self, n_top: int = 10):
        risky_files = (
            self.results[
                self.results["risk_class"].isin(["Critical", "High", "Medium"])
            ]
            .sort_values(
                by=["main_author_share", "total_file_churn"], ascending=[False, False]
            )
            .head(n_top)
        )

        if risky_files.empty:
            self.console.print(
                "[green]Análise concluída. Nenhum arquivo de alto risco ou crítico encontrado.[/green]"
            )
            return

        table = Table(title=f"Top {n_top} Arquivos com Risco de Bus Factor")
        table.add_column("Arquivo", style="dim", overflow="fold")
        table.add_column("Risco", justify="center")
        table.add_column("Autores", justify="right")
        table.add_column("Share do Main Autor", justify="right")
        table.add_column("Autor Principal", justify="left", style="bold white")

        for _, row in risky_files.iterrows():
            share_percent = f"{row['main_author_share']:.2%}"
            risk_style = self._get_risk_style(row["risk_class"])

            table.add_row(
                row["file"],
                f"[{risk_style}]{row['risk_class']}[/{risk_style}]",
                str(row["n_authors"]),
                share_percent,
                row["main_author"],
            )

        self.console.print(table)

    def export_report(self, format: str):
        """Exports the full report to CSV or JSON format."""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = f"{self.output_dir}/busfactorpy_report.{format}"

        if format == "csv":
            self.results.to_csv(filename, index=False)
        elif format == "json":
            self.results.to_json(filename, orient="records", indent=4)

        self.console.print(
            f"[bold green]Relatório exportado com sucesso para:[/bold green] {filename}"
        )
