import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
import os


class BusFactorVisualizer:
    """
    Generates data visualizations (bar charts) using Matplotlib.
    """

    def __init__(self):
        self.output_dir = "charts"
        os.makedirs(self.output_dir, exist_ok=True)
        self.console = Console()

    def generate_top_n_bar_chart(
        self,
        results_df: pd.DataFrame,
        n_top: int = 10,
        filename: str = "top_risky_files.png",
    ):
        """
        Creates a bar chart showing the main author's share for the Top N risky files.
        """
        risky_files = (
            results_df.sort_values(by="main_author_share", ascending=False)
            .head(n_top)
            .reset_index(drop=True)
        )

        if risky_files.empty:
            self.console.print("[yellow]Insufficient data to plot trend.[/yellow]")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.barh(
            risky_files["file"], risky_files["main_author_share"] * 100, color="skyblue"
        )

        ax.set_xlabel("Share do Principal Autor (%)")
        ax.set_title(f"Top {n_top} Arquivos por Dominância do Autor")
        ax.set_xlim(0, 100)
        plt.gca().invert_yaxis()  # Inverte para ter o 'Top 1' no topo

        ax.axvline(
            80, color="red", linestyle="--", linewidth=1, label="Risco Alto (>80%)"
        )
        ax.legend()
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close(fig)

        self.console.print(f"[bold green]Bar chart saved to:[/bold green] {filepath}")

    def plot_trend(self, trend_df: pd.DataFrame, filename="bus_factor_trend.png"):
        if trend_df.empty:
            self.console.print("[yellow]Insufficient data to plot trend.[/yellow]")
            return

        plt.figure(figsize=(12, 6))

        ax = plt.gca()
        ax.plot(
            trend_df["date"],
            trend_df["risky_percentage"],
            color="tab:red",
            marker="o",
            label="% Risky Files",
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("% Risky Files", color="tab:red")
        ax.tick_params(axis="y", labelcolor="tab:red")
        ax.set_ylim(0, 105)

        plt.title("Bus Factor Evolution Over Time")
        plt.grid(True, alpha=0.3)

        ax.legend(loc="upper left")
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)

        self.console.print(f"[bold green]Trend chart saved to:[/bold green] {filepath}")
