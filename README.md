# VibeTracer

[![PyPI version](https://img.shields.io/pypi/v/vibetracer.svg)](https://pypi.org/project/vibetracer)
[![Python versions](https://img.shields.io/pypi/pyversions/vibetracer.svg)](https://pypi.org/project/vibetracer)
[![License](https://img.shields.io/pypi/l/vibetracer.svg)](./LICENSE)

![VibeTracer](https://github.com/szamani20/VibeTracer/blob/main/vibetracer.png)

> **VibeTracer is vibecoders’ best friend** – instrument, trace & *audit* your Python vibes **locally**, with
> LLM‑powered insights.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Quick Start](#quick-start)
3. [Command‑line Reference](#command-line-reference)
4. [Generated Reports](#generated-reports)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Security & Privacy](#security--privacy)
8. [Why VibeTracer?](#why-vibetracer)
9. [Roadmap](#roadmap)
10. [Contributing](#contributing)
11. [License](#license)
12. [Changelog](#changelog)

---

## Key Features

* **One‑line instrumentation** – decorate any function with `@info_decorator` to capture its implementation, arguments,
  return value, runtime, exceptions, and more, both statically & dynamically.
* **Project‑wide tracing** – `vibetracer run path/to/main.py` auto‑instruments every in‑house function (external
  packages are ignored) and stores rich execution data in a local **SQLite** DB.
* **LLM‑powered analysis** – `vibetracer analyze` turns raw traces into two Markdown reports: *human‑readable* and
  *LLM‑ready*. Plug in Anthropic, OpenAI, or Google with your API key for a full audit.
* **Actionable insights** – Errors, security issues, performance hotspots, resource concerns, and architectural notes –
  each with concrete suggestions.
* **All‑local, zero infra** – no remote telemetry, no servers to run, API keys never leave your machine (check the
  source!).
* **One‑shot convenience** – `vibetracer runalyze` runs & analyzes in a single command.

---

## Quick Start

### 1· Decorator‑level tracing

```python
from vibetracer import info_decorator


@info_decorator
def greet(name: str) -> str:
    return f"Hello, {name}!"


print(greet("Vibe coder"))
```

After execution you’ll find an `execution_<timestamp>.db` SQLite file in `.vibetracer/`.

### 2· Project‑wide tracing

```bash
vibetracer run path/to/main.py
```

### 3· AI‑assisted analysis

```bash
export LLM_PROVIDER=openai   # or anthropic / google
export {LLM_PROVIDER}_API_KEY=<your‑LLM-provideer-api‑key>

vibetracer analyze .vibetracer/execution_latest.db
```

### 4· All‑in‑one

```bash
vibetracer runalyze path/to/main.py --provider='openai' --api_key=$OPENAI_API_KEY
```

---

## Command‑line Reference

| Command               | Purpose                 | Required Arg                                    | Optional Flags / Env Vars                                                                                                       |
|-----------------------|-------------------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `vibetracer run`      | Trace an entire project | Path to entry `main.py`                         | –                                                                                                                               |
| `vibetracer analyze`  | Analyze a trace DB      | Path to `.db` file **or** folder (picks latest) | `--provider` (`openai`/`anthropic`/`google`, default **openai**) *or* `LLM_PROVIDER`, `--api_key` *or* `{LLM_PROVIDER}_API_KEY` |
| `vibetracer runalyze` | Run + analyze in one go | Path to entry `main.py`                         | Same as **analyze**                                                                                                             |

> **ℹ️ API keys stay local** – they are only used to call the selected provider *from your machine*.

---

## Generated Reports

Each analysis produces two Markdown files:

1. **Human Report** – readable, annotated summary of runtime findings.
2. **LLM Report** – structured, token‑balanced context ready for further prompts.

Both contain five sections:

| Section              | Description                              |
|----------------------|------------------------------------------|
| Errors & Exceptions  | Runtime failures + fixes                 |
| Security Issues      | Potential vulnerabilities + mitigations  |
| Performance Hotspots | Slow spots + optimization ideas          |
| Runtime Concerns     | Memory / I/O / resource notes            |
| Architectural Notes  | Organization & best‑practice suggestions |

Paste either report into your favourite chat‑GPT‑like tool to continue iterating – or just read it yourself.

[Check out this sample report from a real project vibe traced using vibetracer.](./sample_audit_report.md)

---

## Installation

```bash
pip install vibetracer
```

---

## Configuration

| Env Var                  | Purpose                                        | Default        |
|--------------------------|------------------------------------------------|----------------|
| `LLM_PROVIDER`           | LLM provider (`openai`, `anthropic`, `google`) | `openai`       |
| `{LLM_PROVIDER}_API_KEY` | API key for provider                           | –              |

Config can also be given via CLI flags (see above). CLI flags override env vars.

---

## Security & Privacy

* **Local‑first**: All traces & analysis stay on disk – no external telemetry.
* **Transparent**: Open‑source code – verify what happens with your data.
* **Ephemeral keys**: API keys are read once, kept in memory, never stored.

---

## Why VibeTracer?

| Feature                | VibeTracer | PySnooper | Manual Telemetry |
|------------------------|------------|-----------|------------------|
| Static+dynamic capture | ✅          | ❌         | ⚠️               |
| LLM‑powered audit      | ✅          | ❌         | ❌                |
| Zero infra / local only | ✅          | ✅         | ❌                |
| SQLite storage         | ✅          | ❌         | –                |
| One‑shot run+analyze   | ✅          | ❌         | –                |

---

## Roadmap

* [ ] Plugin system for custom analyzers
* [ ] VS Code extension for in‑editor highlights
* [ ] Cloud‑hosted dashboard (opt‑in)

---

## Contributing

1. Fork, clone, `git checkout -b feat/<name>`.
2. Dev
3. Open a PR

---

## License

Distributed under the **MIT** license. See [LICENSE](./LICENSE) for more information.

---

## Changelog

See [CHANGELOG](./CHANGELOG.md) for release notes.

---

*Powered by vibes & ☕️ – happy tracing!*
