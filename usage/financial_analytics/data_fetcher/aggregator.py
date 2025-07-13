import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import time


class DataAggregator:
    def __init__(self):
        self.aggregation_history = []
        self.temp_storage = defaultdict(list)

    def aggregate_by_time_period(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        df['date'] = pd.to_datetime(df['date'])

        aggregated_data = []

        if period == 'weekly':
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year

            for (year, week), group in df.groupby(['year', 'week']):
                agg_record = {
                    'period': f"{year}-W{week}",
                    'open': group.iloc[0]['open'],
                    'close': group.iloc[-1]['close'],
                    'high': group['high'].max(),
                    'low': group['low'].min(),
                    'volume': group['volume'].sum(),
                    'count': len(group)
                }
                aggregated_data.append(agg_record)

        elif period == 'monthly':
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year

            for (year, month), group in df.groupby(['year', 'month']):
                agg_record = {
                    'period': f"{year}-{month:02d}",
                    'open': group.iloc[0]['open'],
                    'close': group.iloc[-1]['close'],
                    'high': group['high'].max(),
                    'low': group['low'].min(),
                    'volume': group['volume'].sum(),
                    'count': len(group)
                }
                aggregated_data.append(agg_record)

        result_df = pd.DataFrame(aggregated_data)
        self.aggregation_history.append({
            'timestamp': time.time(),
            'period': period,
            'records': len(result_df)
        })

        return result_df

    def create_hierarchical_aggregation(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        hierarchy = {}

        for symbol, df in data.items():
            symbol_data = {
                'daily': df.to_dict('records'),
                'weekly': self.aggregate_by_time_period(df, 'weekly').to_dict('records'),
                'monthly': self.aggregate_by_time_period(df, 'monthly').to_dict('records'),
                'statistics': {
                    'mean_price': df['close'].mean(),
                    'std_price': df['close'].std(),
                    'total_volume': df['volume'].sum()
                }
            }
            hierarchy[symbol] = symbol_data

        return hierarchy

    def calculate_cross_correlations(self, data: Dict[str, pd.DataFrame]) -> Dict[Tuple[str, str], float]:
        correlations = {}
        symbols = list(data.keys())

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]

                df1 = data[symbol1].set_index('date')['close']
                df2 = data[symbol2].set_index('date')['close']

                merged = pd.concat([df1, df2], axis=1, join='inner')

                if len(merged) > 1:
                    corr = merged.iloc[:, 0].corr(merged.iloc[:, 1])
                    correlations[(symbol1, symbol2)] = corr

        return correlations

    def generate_summary_statistics(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}

        for key, value in aggregated_data.items():
            if isinstance(value, dict):
                nested_summary = self.generate_summary_statistics(value)
                summary[key] = nested_summary
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                df = pd.DataFrame(value)
                numeric_cols = df.select_dtypes(include=[np.number]).columns

                stats = {}
                for col in numeric_cols:
                    stats[col] = {
                        'mean': df[col].mean(),
                        'median': df[col].median(),
                        'std': df[col].std(),
                        'min': df[col].min(),
                        'max': df[col].max()
                    }
                summary[key] = stats
            else:
                summary[key] = value

        return summary

    def merge_temporal_data(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        merged = defaultdict(lambda: defaultdict(list))

        for dataset in datasets:
            for symbol, data in dataset.items():
                for period, records in data.items():
                    if isinstance(records, list):
                        merged[symbol][period].extend(records)
                    else:
                        self.temp_storage[f"{symbol}_{period}"].append(records)

        final_merged = {}
        for symbol, periods in merged.items():
            final_merged[symbol] = {}
            for period, records in periods.items():
                final_merged[symbol][period] = sorted(records,
                                                      key=lambda x: x.get('period', ''))

        return final_merged