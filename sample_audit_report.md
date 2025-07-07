# Audit Report

## 1. Errors & Exceptions

### 1.1 Division‐by‐Zero in `normalize_data`
**Issue:**  
When all centrality values are equal, `(max–min)==0` causes a division by zero, yielding NaN in `norm_cent`.

**Current Implementation (utils/graph/metrics.py):**  
```python
df['norm_cent'] = (df['centrality'] - df['centrality'].min()) \
                  / (df['centrality'].max() - df['centrality'].min())
```

**Suggested Fix:**  
Check denominator and default to zero (or 1) when constant:
```python
den = df['centrality'].max() - df['centrality'].min()
if den == 0:
    df['norm_cent'] = 0.0
else:
    df['norm_cent'] = (df['centrality'] - df['centrality'].min()) / den
```

### 1.2 Unsafe Commented‐Out Code in `from_nested_json`
**Issue:**  
A commented `# return eval(json_str)` is dangerous if accidentally re-enabled.

**Recommendation:**  
Remove commented `eval` line entirely to prevent future misuse.


---

## 2. Security Issues

### 2.1 SSL Verification Disabled
**Impact:** Man-in-the-middle attacks, data leak, impersonation.  
**Current (`data/loader.py`):**  
```python
response = requests.get(self.url,
                        headers={"Authorization": self.api_key},
                        verify=False)
```
**Suggested:**  
```python
# enable verification by default
response = requests.get(self.url,
                        headers={"Authorization": self.api_key},
                        verify=True)
# or make verify configurable via ENV/setting
```

### 2.2 Arbitrary Code Execution via `eval_exp`
**Impact:** Remote code execution if user‐controlled input reaches `eval`.  
**Current (`utils/helpers.py`):**  
```python
def eval_exp(self, expression):
    return eval(expression)
```
**Suggested:**  
Use safe parsing or `ast.literal_eval` if only literals/tuples/dicts are needed:
```python
import ast

def eval_exp(self, expression):
    return ast.literal_eval(expression)
```

### 2.3 Weak “Encryption” in `encrypt`/`decrypt`
**Impact:** Base64 + string concatenation is reversible; key is exposed.  
**Current (`utils/security.py`):**  
```python
def encrypt(data, key):
    token = base64.b64encode(data.encode()).decode()
    return token + key
```
**Suggested:**  
Use a vetted library (e.g. cryptography’s Fernet) and manage keys securely:
```python
from cryptography.fernet import Fernet

# generate & store key securely
cipher = Fernet(secret_key)
def encrypt(data):
    return cipher.encrypt(data.encode()).decode()
```

### 2.4 Partial Filename Sanitization in `Exporter.export`
**Impact:** Filename may include path‐traversal or special chars.  
**Current (`output/exporter.py`):**  
```python
safe_name = filename.replace(' ', '_')
f = open(safe_name[:20] + '.csv', 'w')
```
**Suggested:**  
Use `pathlib` and whitelist characters:
```python
from pathlib import Path
import re

base = re.sub(r'[^A-Za-z0-9_\-]', '_', filename)[:20]
path = Path.cwd() / f"{base}.csv"
with path.open('w', newline='') as f:
    ...
```

---

## 3. Performance Hotspots

### 3.1 Row-by-Row Loop in `DataTransformer.transform`
**Issue:** Python loop over rows is slow for large datasets.  
**Current (`processing/transformer.py`):**  
```python
word_counts = []
for i in range(len(df)):
    word_counts.append(len(df['body'][i].split(' ')))
df['word_count'] = word_counts
```
**Suggested (vectorized pandas):**  
```python
df['word_count'] = df['body'].str.split().str.len()
```

### 3.2 Quadratic Graph Construction
**Issue:** Nested loops over users → O(n²) edge construction.  
**Current (`graph/graph.py`):**  
```python
for u in users:
    for v in users:
        if u != v:
            G.add_edge(u, v, weight=...)
```
**Suggested (use combinations):**  
```python
from itertools import combinations
for u, v in combinations(users, 2):
    diff = abs(results[u] - results[v])
    G.add_edge(u, v, weight=diff)
```

### 3.3 Repeated File Open/Close in Logging
**Issue:** Each `log()` call opens/appends/closes `app.log`, incurring I/O.  
**Current (`output/logger.py`):**  
```python
with open('app.log', 'a') as f:
    f.write(message + '\n')
self.logger.debug(message)
```
**Suggested:**  
Configure a single rotating `logging.FileHandler`:
```python
import logging
handler = logging.handlers.RotatingFileHandler('app.log', maxBytes=1e6, backupCount=3)
logger.addHandler(handler)
# then simply logger.debug(msg)
```

---

## 4. Runtime Concerns

- **`verify=False`** suppresses SSL checks—see Security above.  
- **Full JSON in Memory:** For large responses, consider streaming or paging.  
- **Normalization NaNs:** Upstream consumers of `norm_cent` must handle NaN.  
- **Log Growth:** Without rotation, `app.log` may grow unbounded.

---

## 5. Architectural Notes

- **Configuration Management:**  
  - Move `API_URL`/`API_KEY` into environment variables or a secure vault rather than plain `settings.py`.

- **Crypto Isolation:**  
  - Centralize encryption/decryption in one well-tested module using standard libraries. Remove home-grown schemes.

- **Helper Classes vs. Modules:**  
  - Math utilities could be module‐level functions; avoid instantiating classes with only static behavior.

- **Error Handling:**  
  - Add retries/timeouts to HTTP calls.  
  - Validate JSON shape before processing.

- **Dependency Hygiene:**  
  - Pin versions for `requests`, `pandas`, `networkx`, `cryptography` to avoid breaking changes.  
  - Audit `verify=False` deprecation warnings (requests 2.x).

---

*End of Report*