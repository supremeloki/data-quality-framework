# data-quality-framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Declarative data-quality checks: not-null, uniqueness, ranges, regex formats, and row-count bounds — with severity-aware reports that distinguish hard errors from soft warnings.

## 🚀 Overview

Bad data doesn't announce itself. `data-quality-framework` describes expectations as composable `Check` objects, runs them over any list of dict rows, and produces a frozen `QualityReport` with per-row failure attribution. Severity is a first-class concept: an ERROR fails the report, a WARNING records the problem without blocking — so pipelines can enforce what matters and merely log the rest.

## ✨ Features

- **Built-in checks:** `NotNullCheck`, `UniqueCheck`, `RangeCheck`, `RegexCheck`, `RowCountCheck`
- **Severity model:** ERROR / WARNING / INFO; `report.passed` only fails on errors
- **Row-level attribution:** failed row indexes returned (capped at 20 per check for sane logs)
- **Type-tolerant ranges:** non-numeric cells skipped rather than counted as violations
- **Fluent composition:** `QualitySuite().add(a).add(b).run(rows)`
- **Custom checks:** subclass `Check`, implement one method
- **Zero dependencies**

## 🚧 Structure

```
data-quality-framework/
├── src/data_quality/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/data-quality-framework.git
cd data-quality-framework
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from data_quality import NotNullCheck, QualitySuite, RangeCheck, UniqueCheck

suite = QualitySuite(
    NotNullCheck("user_id"),
    UniqueCheck("user_id"),
    RangeCheck("age", minimum=0, maximum=120),
)

report = suite.run(rows)
if not report.passed:
    for failure in report.errors():
        print(failure)
        print(f"  rows: {failure.failed_rows}")
```

## 🔧 Error Handling

```text
QualityError   # base class; checks themselves never raise on bad data —
               # bad data becomes failed CheckResults
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen results and reports
- Zero comments — names carry the meaning
- Severity semantics tested explicitly (warning-only suites still pass)

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi**

---

⭐ Star this repo if you find it useful!
