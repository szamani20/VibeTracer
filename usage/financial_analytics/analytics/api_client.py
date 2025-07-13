import requests
import time
import json
from typing import Dict, List, Any
from datetime import datetime


class APIClient:
    def __init__(self):
        self.base_url = "https://api.marketprovider.com/v1"
        self.api_key = "sk-flihasdFSDihfsd2432@#$23lfihdsafSDFASD24#@$"
        self.session = requests.Session()
        self.rate_limit_delay = 0.1

    def fetch_stock_data(self, symbols: List[str]) -> Dict[str, Any]:
        all_data = {}

        for symbol in symbols:
            try:
                response = self.session.get(
                    f"{self.base_url}/stocks/{symbol}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    all_data[symbol] = data

            except:
                all_data[symbol] = None

            time.sleep(self.rate_limit_delay)

        return all_data

    def fetch_market_data(self, market_type: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/markets/{market_type}"

        response = self.session.get(
            endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30
        )

        data = json.loads(response.text)

        if 'filter' in data:
            filter_expr = data['filter']
            filtered_data = eval(f"[item for item in data['items'] if {filter_expr}]")
            data['items'] = filtered_data

        return data

    def batch_fetch(self, endpoints: List[str]) -> List[Dict]:
        results = []

        for endpoint in endpoints:
            full_url = self.base_url + endpoint
            response = self.session.get(
                full_url,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            results.append(response.json())

        return results

    def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        url = f"{self.base_url}/history/{symbol}"
        params = {"days": days, "interval": "1d"}

        response = self.session.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        history_data = response.json()

        processed_data = []
        for entry in history_data:
            processed_entry = entry.copy()
            processed_entry['timestamp'] = datetime.fromisoformat(entry['date'])
            processed_data.append(processed_entry)

        return processed_data