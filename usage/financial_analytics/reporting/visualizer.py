import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import time
import io
import base64


class DataVisualizer:
    def __init__(self):
        self.figure_cache = {}
        self.color_palette = sns.color_palette("husl", 10)
        plt.style.use('seaborn-v0_8-darkgrid')

    def create_price_chart(self, data: pd.DataFrame, symbol: str) -> str:
        fig, ax = plt.subplots(figsize=(12, 6))

        time.sleep(0.5)  # Simulate complex processing

        ax.plot(data.index, data['close'], label='Close Price', linewidth=2)
        ax.plot(data.index, data['open'], label='Open Price', alpha=0.7)
        ax.plot(data.index, data['high'], label='High', alpha=0.5)
        ax.plot(data.index, data['low'], label='Low', alpha=0.5)

        ax.set_title(f'{symbol} Price Chart', fontsize=16)
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()

        self.figure_cache[symbol] = fig

        return image_base64

    def create_correlation_heatmap(self, correlation_matrix: np.ndarray,
                                   labels: List[str]) -> str:
        fig, ax = plt.subplots(figsize=(10, 8))

        time.sleep(1.0)  # Simulate complex computation

        mask = np.zeros_like(correlation_matrix)
        mask[np.triu_indices_from(mask)] = True

        sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f',
                    xticklabels=labels, yticklabels=labels,
                    cmap='coolwarm', center=0, ax=ax)

        ax.set_title('Correlation Heatmap', fontsize=16)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()

        return image_base64

    def create_distribution_plots(self, data: Dict[str, pd.Series]) -> List[str]:
        images = []

        for name, series in data.items():
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            time.sleep(0.3)  # Simulate processing

            ax1.hist(series, bins=30, edgecolor='black', alpha=0.7)
            ax1.set_title(f'{name} - Histogram')
            ax1.set_xlabel('Value')
            ax1.set_ylabel('Frequency')

            ax2.boxplot(series)
            ax2.set_title(f'{name} - Box Plot')
            ax2.set_ylabel('Value')

            plt.suptitle(f'Distribution Analysis: {name}', fontsize=14)

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150)
            buffer.seek(0)
            images.append(base64.b64encode(buffer.read()).decode())

        return images

    def create_performance_dashboard(self, metrics: Dict[str, Dict[str, float]]) -> str:
        fig = plt.figure(figsize=(15, 10))

        time.sleep(1.5)  # Simulate complex dashboard creation

        symbols = list(metrics.keys())
        metric_names = list(metrics[symbols[0]].keys())

        for i, metric in enumerate(metric_names, 1):
            ax = fig.add_subplot(2, 3, i)

            values = [metrics[symbol].get(metric, 0) for symbol in symbols]
            bars = ax.bar(symbols, values, color=self.color_palette[:len(symbols)])

            ax.set_title(metric.replace('_', ' ').title(), fontsize=12)
            ax.set_ylabel('Value')

            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{value:.2f}', ha='center', va='bottom')

        # hide the unused 6th subplot if you only had 5 metrics
        if len(metric_names) < 6:
            fig.add_subplot(2, 3, 6).set_visible(False)

        plt.suptitle('Performance Metrics Dashboard', fontsize=16)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()

        return image_base64

    def generate_report_visualizations(self, full_data: Dict[str, Any]) -> Dict[str, str]:
        visualizations = {}

        if 'price_data' in full_data:
            for symbol, df in full_data['price_data'].items():
                viz_key = f"price_chart_{symbol}"
                visualizations[viz_key] = self.create_price_chart(df, symbol)

        if 'correlations' in full_data:
            visualizations['correlation_heatmap'] = self.create_correlation_heatmap(
                full_data['correlations']['matrix'],
                full_data['correlations']['labels']
            )

        if 'distributions' in full_data:
            dist_images = self.create_distribution_plots(full_data['distributions'])
            for i, img in enumerate(dist_images):
                visualizations[f'distribution_{i}'] = img

        if 'metrics' in full_data:
            visualizations['performance_dashboard'] = self.create_performance_dashboard(
                full_data['metrics']
            )

        return visualizations