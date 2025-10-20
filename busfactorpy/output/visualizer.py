import pandas as pd
import matplotlib.pyplot as plt
import os

class BusFactorVisualizer:
    """
    Generates data visualizations (bar charts) using Matplotlib.
    """
    def __init__(self):
        self.output_dir = "busfactorpy_output"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_top_n_bar_chart(self, results_df: pd.DataFrame, n_top: int = 10, filename: str = "top_risky_files.png"):
        """
        Creates a bar chart showing the main author's share for the Top N risky files.
        """
        risky_files = results_df.sort_values(
            by='main_author_share', 
            ascending=False
        ).head(n_top).reset_index(drop=True)

        if risky_files.empty:
            print("Nenhum dado para visualização.")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.barh(
            risky_files['file'], 
            risky_files['main_author_share'] * 100, 
            color='skyblue'
        )

        ax.set_xlabel('Share do Principal Autor (%)')
        ax.set_title(f'Top {n_top} Arquivos por Dominância do Autor')
        ax.set_xlim(0, 100)
        plt.gca().invert_yaxis() # Inverte para ter o 'Top 1' no topo

        ax.axvline(80, color='red', linestyle='--', linewidth=1, label='Risco Alto (>80%)')
        ax.legend()
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close(fig)
        
        print(f"Gráfico de barras salvo em: {filepath}")