from datetime import datetime, timedelta
import pandas as pd
from busfactorpy.core.calculator import BusFactorCalculator


class TrendAnalyzer:
    def __init__(self, commit_data, calculator_params):
        """
        :param commit_data: DataFrame com todo o histórico minerado.
        :param calculator_params: Dicionário com parâmetros para o BusFactorCalculator (metric, threshold, etc).
        """
        self.commit_data = commit_data

        if not pd.api.types.is_datetime64_any_dtype(self.commit_data["date"]):
            self.commit_data["date"] = pd.to_datetime(
                self.commit_data["date"], utc=True
            )

        self.params = calculator_params

    def analyze(
        self, start_date: datetime, end_date: datetime, window_days: int, step_days: int
    ):
        results = []
        current_date = start_date

        if current_date.tzinfo is None:
            current_date = current_date.replace(tzinfo=None)

        while current_date <= end_date:
            window_start = current_date - timedelta(days=window_days)

            mask = (self.commit_data["date"] >= window_start) & (
                self.commit_data["date"] <= current_date
            )
            window_data = self.commit_data.loc[mask].copy()

            if not window_data.empty:
                calculator = BusFactorCalculator(window_data, **self.params)
                bf_results = calculator.calculate()

                total_files = len(bf_results)
                risky_count = 0

                if total_files > 0:
                    if "Bus Factor" in bf_results.columns:
                        risky_count = len(bf_results[bf_results["Bus Factor"] == 1])

                    elif "risk_class" in bf_results.columns:
                        risky_count = len(
                            bf_results[bf_results["risk_class"] == "Critical"]
                        )

                    else:
                        risky_count = 0

                results.append(
                    {
                        "date": current_date,
                        "total_files": total_files,
                        "risky_files": risky_count,
                        "risky_percentage": (risky_count / total_files * 100)
                        if total_files > 0
                        else 0,
                    }
                )

            current_date += timedelta(days=step_days)

        return pd.DataFrame(results)
