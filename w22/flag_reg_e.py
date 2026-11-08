"""Simplified Reg E SLA flagging for messy dispute CSV exports.

Simplified interview rule, NOT a production Regulation E compliance decision.
No credit-posting field, exceptions, or bank holiday calendar is modeled.
Returns the dispute_ids that are BREACHED:
  more than 10 business days (Mon-Fri) elapsed between filed_date and TODAY,
  AND status is not 'resolved'.

A returned ID is an exercise SLA flag, not an established legal violation, and
an unflagged or rejected ID must not be read as legally compliant.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterator, Optional

TODAY = date(2026, 6, 29)  # hardcode for deterministic grading

SLA_BUSINESS_DAYS = 10
TERMINAL_STATUS = "resolved"
REQUIRED_COLUMNS = ("dispute_id", "filed_date", "status")
MISSING_DATE_SENTINELS = frozenset({"", "n/a", "null"})

_ISO_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_DAY_FIRST_DATE = re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})")

logger = logging.getLogger(__name__)


class CsvFileError(ValueError):
    """File-level failure: the export cannot be evaluated as a whole."""


@dataclass(frozen=True)
class Diagnostic:
    code: str
    record: Optional[int]
    dispute_id: Optional[str]
    field: Optional[str]
    action: str
    detail: str = ""
    replaced_record: Optional[int] = None

    def message(self) -> str:
        parts = [f"code={self.code}"]
        if self.record is not None:
            parts.append(f"record={self.record}")
        if self.replaced_record is not None:
            parts.append(f"replaced_record={self.replaced_record}")
        parts.append(f"id={self.dispute_id!r}" if self.dispute_id else "id=<none>")
        if self.field:
            parts.append(f"field={self.field}")
        parts.append(f"action={self.action}")
        if self.detail:
            parts.append(f"detail={self.detail}")
        return " ".join(parts)


@dataclass
class DisputeRecord:
    index: int
    dispute_id: str
    filed_date: Optional[date]
    raw_filed_date: Optional[str]
    status: Optional[str]
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def decision_fields(self) -> dict[str, object]:
        filed = self.filed_date if self.filed_date is not None else self.raw_filed_date
        return {"filed_date": filed, "status": self.status}


@dataclass
class Summary:
    records_read: int = 0
    unique_ids: int = 0
    duplicate_replacements: int = 0
    rejected_records: int = 0
    authoritative_invalid_ids: int = 0
    missing_status_records: int = 0
    flagged: int = 0


@dataclass
class EvaluationResult:
    flagged: list[str]
    diagnostics: list[Diagnostic]
    summary: Summary


def count_business_days(start: date, end: date) -> int:
    """Count Monday-Friday dates d where start < d <= end.

    Returns a negative count when end precedes start; callers decide how to
    treat such dates (they are never clamped to zero here).
    """
    if end < start:
        return -count_business_days(end, start)
    full_weeks, remainder = divmod((end - start).days, 7)
    count = full_weeks * 5
    base = start + timedelta(days=full_weeks * 7)
    for offset in range(1, remainder + 1):
        if (base + timedelta(days=offset)).weekday() < 5:
            count += 1
    return count


def parse_filed_date(raw: Optional[str], today: date) -> tuple[Optional[date], Optional[str]]:
    """Parse a filing date. Returns (date, None) or (None, diagnostic code)."""
    value = (raw or "").strip()
    if value.casefold() in MISSING_DATE_SENTINELS:
        return None, "MISSING_DATE"

    iso = _ISO_DATE.fullmatch(value)
    slash = _DAY_FIRST_DATE.fullmatch(value)
    try:
        if iso:
            year, month, day = (int(part) for part in iso.groups())
        elif slash:
            day, month, year = (int(part) for part in slash.groups())
        else:
            return None, "INVALID_DATE"
        parsed = date(year, month, day)
    except ValueError:
        return None, "INVALID_DATE"

    if parsed > today:
        return None, "FUTURE_DATE"
    return parsed, None


def normalize_status(raw: Optional[str]) -> str:
    return (raw or "").strip().casefold()


def is_breached(record: DisputeRecord, today: date) -> bool:
    if not record.valid or record.filed_date is None:
        return False
    if record.status == TERMINAL_STATUS:
        return False
    return count_business_days(record.filed_date, today) > SLA_BUSINESS_DAYS


def _read_header(reader: Iterator[list[str]]) -> dict[str, int]:
    for row in reader:
        if row:
            break
    else:
        raise CsvFileError("CSV has no header row")

    columns: dict[str, int] = {}
    for position, name in enumerate(row):
        normalized = name.strip().casefold()
        if not normalized:
            raise CsvFileError(f"CSV header has an empty column name at position {position + 1}")
        if normalized in columns:
            raise CsvFileError(f"CSV header has duplicate column {normalized!r} after normalization")
        columns[normalized] = position

    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise CsvFileError(f"CSV header is missing required column(s): {', '.join(missing)}")
    return columns


def evaluate_disputes(path: str, today: Optional[date] = None) -> EvaluationResult:
    """Parse, validate, de-duplicate, and evaluate a dispute export.

    Raises CsvFileError, csv.Error-derived CsvFileError, UnicodeDecodeError, or
    OSError for file-level failures; never returns a partial result.
    """
    today = TODAY if today is None else today
    diagnostics: list[Diagnostic] = []
    summary = Summary()
    authoritative: dict[str, DisputeRecord] = {}

    def emit(diagnostic: Diagnostic) -> None:
        diagnostics.append(diagnostic)
        logger.warning("%s", diagnostic.message())

    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            columns = _read_header(reader)
            width = len(columns)
            id_col = columns["dispute_id"]
            date_col = columns["filed_date"]
            status_col = columns["status"]

            for row in reader:
                if not row:
                    continue
                summary.records_read += 1
                index = summary.records_read
                raw_id = row[id_col] if id_col < len(row) else ""
                dispute_id = raw_id.strip() or None

                if len(row) != width:
                    emit(Diagnostic(
                        "ROW_WIDTH_MISMATCH", index, dispute_id, None,
                        "reject decision record" + ("; apply ID precedence" if dispute_id else ""),
                        detail=f"expected {width} fields, got {len(row)}",
                    ))
                    summary.rejected_records += 1
                    if dispute_id is None:
                        continue
                    record = DisputeRecord(index, dispute_id, None, None, None,
                                           errors=["ROW_WIDTH_MISMATCH"])
                elif dispute_id is None:
                    emit(Diagnostic("MISSING_ID", index, None, "dispute_id",
                                    "reject ungroupable record"))
                    summary.rejected_records += 1
                    continue
                else:
                    raw_date = row[date_col]
                    filed, date_error = parse_filed_date(raw_date, today)
                    status = normalize_status(row[status_col])
                    record = DisputeRecord(index, dispute_id, filed, raw_date.strip(), status)
                    if date_error:
                        record.errors.append(date_error)
                        emit(Diagnostic(date_error, index, dispute_id, "filed_date",
                                        "retain as invalid authoritative record",
                                        detail=f"value={raw_date.strip()!r}"))
                        summary.rejected_records += 1
                    if not status:
                        summary.missing_status_records += 1
                        emit(Diagnostic("MISSING_STATUS", index, dispute_id, "status",
                                        "evaluate as unresolved"))

                previous = authoritative.get(dispute_id)
                if previous is not None:
                    before, after = previous.decision_fields(), record.decision_fields()
                    changed = [name for name in ("filed_date", "status")
                               if before[name] != after[name]]
                    detail = ("conflict: changed " + ", ".join(changed)) if changed else "equivalent"
                    summary.duplicate_replacements += 1
                    emit(Diagnostic("DUPLICATE_ID", index, dispute_id, None,
                                    "replace earlier occurrence", detail=detail,
                                    replaced_record=previous.index))
                authoritative[dispute_id] = record
        except csv.Error as exc:
            raise CsvFileError(f"malformed CSV near line {reader.line_num}: {exc}") from exc

    ordered = sorted(authoritative.values(), key=lambda rec: rec.index)
    flagged = [rec.dispute_id for rec in ordered if is_breached(rec, today)]

    summary.unique_ids = len(authoritative)
    summary.authoritative_invalid_ids = sum(1 for rec in ordered if not rec.valid)
    summary.flagged = len(flagged)
    logger.info(
        "summary records_read=%d unique_ids=%d duplicate_replacements=%d "
        "rejected_records=%d authoritative_invalid_ids=%d missing_status_records=%d flagged=%d",
        summary.records_read, summary.unique_ids, summary.duplicate_replacements,
        summary.rejected_records, summary.authoritative_invalid_ids,
        summary.missing_status_records, summary.flagged,
    )
    return EvaluationResult(flagged, diagnostics, summary)


def flag_reg_e(path: str) -> list[str]:
    """Return unique dispute IDs breaching the exercise SLA, in authoritative record order."""
    return evaluate_disputes(path, TODAY).flagged


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Flag unresolved disputes older than 10 business days (Mon-Fri, no holidays) "
            f"as of {TODAY.isoformat()}. Output is an exercise SLA flag list, NOT a "
            "Regulation E compliance determination. Rejected rows (see stderr) mean "
            "incomplete coverage, not a clean compliance result."
        ),
    )
    parser.add_argument("csv_path", help="path to the dispute CSV export")
    args = parser.parse_args(argv)

    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        flagged = flag_reg_e(args.csv_path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(flagged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
