import pickle
import os
import time
from typing import Any, Optional, Dict
from collections import defaultdict


class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.memory_cache = {}
        self.access_times = defaultdict(list)

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get(self, key: str) -> Optional[Any]:
        if key in self.memory_cache:
            self.access_times[key].append(time.time())
            return self.memory_cache[key]

        file_path = os.path.join(self.cache_dir, f"{key}.pkl")

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                self.memory_cache[key] = data
                return data

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self.memory_cache[key] = value

        file_path = os.path.join(self.cache_dir, f"{key}.pkl")
        with open(file_path, 'wb') as f:
            pickle.dump(value, f)

    def clear_old_entries(self, max_age: int = 86400) -> int:
        current_time = time.time()
        removed_count = 0

        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)

            try:
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    os.remove(file_path)
                    removed_count += 1
            except:
                pass

        return removed_count

    def get_stats(self) -> Dict[str, Any]:
        total_size = 0
        file_count = 0

        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            total_size += os.path.getsize(file_path)
            file_count += 1

        return {
            "total_size": total_size,
            "file_count": file_count,
            "memory_entries": len(self.memory_cache),
            "access_patterns": dict(self.access_times)
        }