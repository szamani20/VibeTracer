import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import time


class DataProcessor:
    def __init__(self):
        self.processed_count = 0
        self.error_log = []

    def process_raw_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        all_records = []

        for symbol, data in raw_data.items():
            if data is None:
                continue

            for record in data.get('records', []):
                processed_record = record.copy()
                processed_record['symbol'] = symbol
                processed_record['processed_at'] = time.time()
                all_records.append(processed_record)

        df = pd.DataFrame(all_records)
        self.processed_count += len(df)

        return df

    def normalize_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_df = df.copy()

        for column in ['open', 'close', 'high', 'low']:
            if column in normalized_df.columns:
                mean_val = normalized_df[column].mean()
                std_val = normalized_df[column].std()
                normalized_df[f'{column}_normalized'] = (normalized_df[column] - mean_val) / std_val

        return normalized_df

    def calculate_moving_averages(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        result_df = df.copy()

        for window in windows:
            for i in range(len(df)):
                if i >= window - 1:
                    window_data = []
                    for j in range(i - window + 1, i + 1):
                        window_data.append(df.iloc[j]['close'])
                    result_df.loc[i, f'ma_{window}'] = sum(window_data) / len(window_data)
                else:
                    result_df.loc[i, f'ma_{window}'] = np.nan

        return result_df

    def detect_outliers(self, df: pd.DataFrame, column: str) -> List[int]:
        outliers = []

        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for idx, value in df[column].items():
            if value < lower_bound or value > upper_bound:
                outliers.append(idx)

        return outliers

    def merge_datasets(self, datasets: List[pd.DataFrame]) -> pd.DataFrame:
        if not datasets:
            return pd.DataFrame()

        merged = datasets[0]

        for i in range(1, len(datasets)):
            merged = pd.concat([merged, datasets[i]], ignore_index=True)

        return merged

    def calculate_correlations(self, df: pd.DataFrame) -> np.ndarray:
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        correlation_matrix = np.zeros((len(numeric_columns), len(numeric_columns)))

        for i, col1 in enumerate(numeric_columns):
            for j, col2 in enumerate(numeric_columns):
                if df[col1].std() != 0 and df[col2].std() != 0:
                    correlation_matrix[i][j] = df[col1].corr(df[col2])

        return correlation_matrix