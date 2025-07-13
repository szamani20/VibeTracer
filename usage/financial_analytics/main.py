import sys
import time
from datetime import datetime

from analytics import APIClient, CacheManager, DataValidator
from data_fetcher import DataProcessor, MetricsCalculator, DataAggregator
from reporting import ReportFormatter, ReportExporter, DataVisualizer


def main():
    print(f"Starting Financial Analytics System at {datetime.now()}")

    # Initialize components
    api_client = APIClient()
    cache_manager = CacheManager()
    validator = DataValidator()

    processor = DataProcessor()
    calculator = MetricsCalculator()
    aggregator = DataAggregator()

    formatter = ReportFormatter()
    exporter = ReportExporter()
    visualizer = DataVisualizer()

    # Define stocks to analyze
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

    # Fetch data
    print("\n1. Fetching stock data...")
    raw_data = {}

    for symbol in symbols:
        cached_data = cache_manager.get(symbol)
        if cached_data:
            raw_data[symbol] = cached_data
        else:
            # Simulate API response
            stock_data = {
                'records': [
                    {
                        'date': f'2024-01-{i:02d}',
                        'open': 100 + i * 2 + (i % 3),
                        'close': 102 + i * 2 + (i % 2),
                        'high': 105 + i * 2,
                        'low': 99 + i * 2,
                        'volume': 1000000 + i * 50000
                    }
                    for i in range(1, 21)
                ]
            }
            raw_data[symbol] = stock_data
            cache_manager.set(symbol, stock_data)

    # Validate data
    validator.validate_batch_data([
        {'type': 'stock', **record}
        for data in raw_data.values()
        for record in data.get('records', [])
    ])

    # Process data
    print("\n2. Processing data...")
    processed_dfs = {}

    for symbol, data in raw_data.items():
        df = processor.process_raw_data({symbol: data})
        df = processor.normalize_prices(df)
        df = processor.calculate_moving_averages(df)

        # Detect outliers
        processor.detect_outliers(df, 'close')

        processed_dfs[symbol] = df

    # Calculate metrics
    print("\n3. Calculating metrics...")
    all_metrics = {}

    for symbol, df in processed_dfs.items():
        returns = calculator.calculate_returns(df['close'])

        metrics = {
            'returns': returns.mean() * 252,
            'volatility': calculator.calculate_volatility(returns),
            'sharpe': calculator.calculate_sharpe_ratio(returns),
            'var_95': calculator.calculate_value_at_risk(returns)
        }

        # Calculate max drawdown
        max_dd, _, _ = calculator.calculate_maximum_drawdown(df['close'])
        metrics['max_drawdown'] = max_dd

        all_metrics[symbol] = metrics

    # Aggregate data
    print("\n4. Aggregating data...")
    hierarchical_data = aggregator.create_hierarchical_aggregation(processed_dfs)

    # Calculate correlations
    aggregator.calculate_cross_correlations(processed_dfs)

    summary_stats = aggregator.generate_summary_statistics(hierarchical_data)

    # Format reports
    print("\n5. Formatting reports...")
    report_data = {
        'executive_summary': {
            'total_symbols': len(symbols),
            'analysis_period': '2024-01-01 to 2024-01-20',
            'generated_at': datetime.now().isoformat()
        },
        'performance_metrics': all_metrics,
        'summary_statistics': summary_stats
    }

    report_content = formatter.format_financial_report(report_data,
                                                       "Financial Analysis Report")

    # Save report
    formatter.save_report("Q1 2024 Analysis", report_content)

    # Generate visualizations
    print("\n6. Creating visualizations...")
    viz_data = {
        'price_data': processed_dfs,
        'metrics': all_metrics,
        'correlations': {
            'matrix': processor.calculate_correlations(processor.merge_datasets(
                list(processed_dfs.values()))),
            'labels': symbols
        }
    }

    # Generate visualizations
    visualizer.generate_report_visualizations(viz_data)

    # Export data
    print("\n7. Exporting results...")
    export_data = {
        'metrics': [{'symbol': k, **v} for k, v in all_metrics.items()],
        'summary': [{'section': k, 'data': str(v)} for k, v in summary_stats.items()]
    }

    exported_files = exporter.bulk_export(export_data, "financial_report")

    # Clean up old files
    cache_manager.clear_old_entries()
    exporter.clean_old_exports()

    print(f"\n✓ Analysis complete! Exported {len(exported_files)} files.")
    print(f"Finished at {datetime.now()}")

    return 0


if __name__ == "__main__":
    main()