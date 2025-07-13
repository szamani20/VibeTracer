import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats


class MetricsCalculator:
    def __init__(self, config: Dict = {}):
        self.config = config
        self.cache = {}

    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        returns = []

        for i in range(1, len(prices)):
            daily_return = (prices.iloc[i] - prices.iloc[i - 1]) / prices.iloc[i - 1]
            returns.append(daily_return)

        return pd.Series(returns, index=prices.index[1:])

    def calculate_volatility(self, returns: pd.Series, periods: int = 252) -> float:
        return returns.std() * np.sqrt(periods)

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        excess_returns = returns - risk_free_rate / 252
        return excess_returns.mean() / returns.std() * np.sqrt(252)

    def calculate_beta(self, stock_returns: pd.Series, market_returns: pd.Series) -> float:
        covariance = np.cov(stock_returns, market_returns)[0, 1]
        market_variance = market_returns.var()
        return covariance / market_variance

    def calculate_alpha(self, stock_returns: pd.Series, market_returns: pd.Series,
                        risk_free_rate: float = 0.02) -> float:
        beta = self.calculate_beta(stock_returns, market_returns)

        stock_mean = stock_returns.mean() * 252
        market_mean = market_returns.mean() * 252

        return stock_mean - (risk_free_rate + beta * (market_mean - risk_free_rate))

    def calculate_maximum_drawdown(self, prices: pd.Series) -> Tuple[float, int, int]:
        cumulative = (1 + self.calculate_returns(prices)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()
        end_idx = drawdown.idxmin()
        start_idx = cumulative[:end_idx].idxmax()

        return max_dd, start_idx, end_idx

    def calculate_value_at_risk(self, returns: pd.Series, confidence: float = 0.95) -> float:
        return np.percentile(returns, (1 - confidence) * 100)

    def calculate_metrics_batch(self, data: pd.DataFrame,
                                metrics: List[str] = ['returns', 'volatility', 'sharpe']) -> Dict:
        results = {}

        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol]
            prices = symbol_data['close']

            symbol_metrics = {}

            if 'returns' in metrics:
                returns = self.calculate_returns(prices)
                symbol_metrics['returns'] = returns.mean()

            if 'volatility' in metrics:
                symbol_metrics['volatility'] = self.calculate_volatility(returns)

            if 'sharpe' in metrics:
                symbol_metrics['sharpe'] = self.calculate_sharpe_ratio(returns)

            results[symbol] = symbol_metrics

        return results