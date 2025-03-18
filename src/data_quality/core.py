from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class QualityError(Exception):
    pass


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class CheckResult:
    check_name: str
    column: str | None
    passed: bool
    severity: Severity
    failed_rows: tuple[int, ...] = ()
    detail: str = ""

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        target = self.column or "dataset"
        return f"[{status}] {target}: {self.check_name} ({self.severity.value})"


@dataclass(frozen=True)
class QualityReport:
    results: tuple[CheckResult, ...]
    row_count: int

    @property
    def passed(self) -> bool:
        return all(r.passed or r.severity != Severity.ERROR for r in self.results)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def errors(self) -> tuple[CheckResult, ...]:
        return tuple(r for r in self.results if not r.passed and r.severity == Severity.ERROR)

    def warnings(self) -> tuple[CheckResult, ...]:
        return tuple(r for r in self.results if not r.passed and r.severity == Severity.WARNING)


class Check:
    name: str = "check"
    severity: Severity = Severity.ERROR
    applies_to_column: str | None = None

    def validate(self, rows: Sequence[dict[str, Any]]) -> CheckResult:
        failed_rows = self.find_failures(rows)
        return CheckResult(
            check_name=self.name,
            column=self.applies_to_column,
            passed=not failed_rows,
            severity=self.severity,
            failed_rows=tuple(failed_rows[:20]),
            detail=f"{len(failed_rows)} row(s) failed",
        )

    @abstractmethod
    def find_failures(self, rows: Sequence[dict[str, Any]]) -> list[int]:
        raise NotImplementedError


class NotNullCheck(Check):
    def __init__(self, column: str,
                 severity: Severity = Severity.ERROR) -> None:
        self.name = f"not_null[{column}]"
        self.severity = severity
        self.applies_to_column = column

    def find_failures(self, rows):
        return [i for i, row in enumerate(rows)
                if row.get(self.applies_to_column) in (None, "")]


class UniqueCheck(Check):
    def __init__(self, column: str,
                 severity: Severity = Severity.ERROR) -> None:
        self.name = f"unique[{column}]"
        self.severity = severity
        self.applies_to_column = column

    def find_failures(self, rows):
        seen: dict[Any, int] = {}
        duplicates = []
        for i, row in enumerate(rows):
            value = row.get(self.applies_to_column)
            if value in seen:
                duplicates.append(i)
            else:
                seen[value] = i
        return duplicates


class RangeCheck(Check):
    def __init__(self, column: str, minimum: float, maximum: float,
                 severity: Severity = Severity.ERROR) -> None:
        self.name = f"range[{column}:{minimum}..{maximum}]"
        self.severity = severity
        self.applies_to_column = column
        self._min = minimum
        self._max = maximum

    def find_failures(self, rows):
        failures = []
        for i, row in enumerate(rows):
            raw = row.get(self.applies_to_column)
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            if not self._min <= value <= self._max:
                failures.append(i)
        return failures


class RegexCheck(Check):
    def __init__(self, column: str, pattern: str,
                 severity: Severity = Severity.WARNING) -> None:
        self._pattern = re.compile(pattern)
        self.name = f"regex[{column}]"
        self.severity = severity
        self.applies_to_column = column

    def find_failures(self, rows):
        return [
            i for i, row in enumerate(rows)
            if row.get(self.applies_to_column) is not None
            and not self._pattern.fullmatch(str(row[self.applies_to_column]))
        ]


class RowCountCheck(Check):
    def __init__(self, expected_min: int, expected_max: int | None = None,
                 severity: Severity = Severity.WARNING) -> None:
        self.name = f"row_count[>={expected_min}]"
        self.severity = severity
        self._min = expected_min
        self._max = expected_max

    def find_failures(self, rows):
        count = len(rows)
        too_few = count < self._min
        too_many = self._max is not None and count > self._max
        return [] if not (too_few or too_many) else [0]


class QualitySuite:
    def __init__(self, *checks: Check) -> None:
        self._checks = list(checks)

    def add(self, check: Check) -> "QualitySuite":
        self._checks.append(check)
        return self

    @property
    def check_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self._checks)

    def run(self, rows: Sequence[dict[str, Any]]) -> QualityReport:
        results = tuple(check.validate(rows) for check in self._checks)
        return QualityReport(results=results, row_count=len(rows))
