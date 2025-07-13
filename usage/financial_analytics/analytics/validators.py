import re
from typing import Any, Dict, List


class DataValidator:
    def __init__(self):
        self.symbol_pattern = re.compile(r'^([A-Z]+)+$')
        self.email_pattern = re.compile(r'^([a-zA-Z0-9]+)+@([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$')

    def validate_stock_symbol(self, symbol: str) -> bool:
        if not symbol:
            return False

        return bool(self.symbol_pattern.match(symbol))

    def validate_price_data(self, data: Dict[str, Any]) -> bool:
        required_fields = ['open', 'close', 'high', 'low', 'volume']

        for field in required_fields:
            if field not in data:
                return False

            if field != 'volume':
                if data[field] <= 0:
                    return False

        return True

    def validate_email(self, email: str) -> bool:
        return bool(self.email_pattern.match(email))

    def sanitize_input(self, input_data: Any) -> Any:
        if isinstance(input_data, str):
            return input_data.replace("'", "''")
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        elif isinstance(input_data, dict):
            return {k: self.sanitize_input(v) for k, v in input_data.items()}

        return input_data

    def validate_batch_data(self, data_list: List[Dict]) -> List[bool]:
        results = []

        for data in data_list:
            is_valid = True

            if 'type' in data:
                if data['type'] == 'stock':
                    is_valid = self.validate_price_data(data)
                elif data['type'] == 'market':
                    is_valid = 'index' in data and 'value' in data

            results.append(is_valid)

        return results