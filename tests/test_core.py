import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from data_quality import (
    NotNullCheck,
    QualitySuite,
    RangeCheck,
    RegexCheck,
    RowCountCheck,
    Severity,
    UniqueCheck,
)


@pytest.fixture
def clean_rows():
    return [
        {"id": "1", "email": "a@x.com", "age": "30"},
        {"id": "2", "email": "b@x.com", "age": "45"},
    ]


def test_not_null_catches_empty(clean_rows):
    rows = clean_rows + [{"id": "", "email": None, "age": "20"}]
    result = NotNullCheck("id").validate(rows)
    assert not result.passed
    assert 2 in result.failed_rows


def test_unique_detects_duplicates():
    rows = [{"uid": "1"}, {"uid": "2"}, {"uid": "1"}]
    result = UniqueCheck("uid").validate(rows)
    assert not result.passed
    assert 2 in result.failed_rows


def test_range_flags_out_of_bounds():
    rows = [{"age": "10"}, {"age": "200"}, {"age": "40"}]
    result = RangeCheck("age", minimum=0, maximum=120).validate(rows)
    failed = set(result.failed_rows)
    assert failed == {1}


def test_range_ignores_non_numeric():
    rows = [{"age": ""}, {"age": None}, {"age": "30"}]
    result = RangeCheck("age", minimum=0, maximum=120).validate(rows)
    assert result.passed


def test_regex_validates_format():
    check = RegexCheck("email", r"[^@\s]+@[^@\s]+")
    good = check.validate([{"email": "ok@mail.com"}])
    bad = check.validate([{"email": "no-at-sign"}])
    assert good.passed
    assert not bad.passed


def test_row_count_enforces_bounds():
    few = RowCountCheck(expected_min=10).validate([{"x": 1} for _ in range(5)])
    ok = RowCountCheck(expected_min=3).validate([{"x": i} for i in range(5)])
    many = RowCountCheck(expected_min=1, expected_max=3).validate(
        [{"x": i} for i in range(9)]
    )
    assert not few.passed
    assert ok.passed
    assert not many.passed


def test_suite_runs_all_checks(clean_rows):
    suite = QualitySuite(
        NotNullCheck("id"),
        UniqueCheck("id"),
        RangeCheck("age", 0, 120),
    )
    report = suite.run(clean_rows)
    assert report.row_count == 2
    assert len(report.results) == 3
    assert report.passed


def test_suite_report_distinguishes_severity():
    suite = QualitySuite(
        NotNullCheck("required_col", severity=Severity.ERROR),
        RegexCheck("optional_col", r"\d+", severity=Severity.WARNING),
    )
    rows = [
        {"required_col": "v1", "optional_col": "not-digits"},
        {"required_col": None, "optional_col": "42"},
    ]
    report = suite.run(rows)
    assert len(report.errors()) >= 1
    assert len(report.warnings()) >= 1
    assert not report.passed


def test_warning_only_failure_still_passes():
    suite = QualitySuite(RegexCheck("code", r"\d+", severity=Severity.WARNING))
    report = suite.run([{"code": "letters"}])
    assert not report.results[0].passed
    assert report.passed


def test_check_names_exposed():
    suite = QualitySuite(NotNullCheck("a"), UniqueCheck("b"))
    assert suite.check_names == ("not_null[a]", "unique[b]")


def test_fluent_add_chaining():
    suite = QualitySuite().add(NotNullCheck("x")).add(RangeCheck("y", 0, 1))
    assert len(suite.check_names) == 2
