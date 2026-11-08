# PRD: Deterministic Reg E SLA Flagging for Messy CSV Exports

## 1. Product summary

Implement `flag_reg_e.py` to identify unresolved disputes that exceed a
**simplified 10-business-day SLA** in a messy CSV export.

This is an interview/practice tool, not a production Regulation E compliance
engine. A returned ID means the selected record breaches the exercise rule,
not that a legal violation has been established. An excluded or unflagged ID
must not be described as legally compliant.

**Status:** Ready for implementation against the confirmed exercise policies.
**Deliverable:** Implementation, focused automated tests, and a working CLI.
This PRD does not implement the Python function.

### Source material

- [Context](context.md): export date and status assumptions.
- [Current script](flag_reg_e.py): unimplemented function, fixed evaluation
  date, and explicit Monday-Friday rule.
- [Original fixture](disputes_messy_original.csv): baseline messy export.
- [Extended fixture](disputes_messy_extended.csv): boundary and adversarial cases.
- [Post-class material](W22_Post-Class.md): emphasizes clarifying assumptions
  and verifying edge cases rather than accepting generated code unchecked.

## 2. Problem and users

Operations analysts need a reproducible list of aged unresolved disputes
without manually repairing an export. Mixed dates, inconsistent status labels,
duplicates, and irrelevant free text must not change the decision unexpectedly.

Primary users are the interview candidate implementing the exercise and the
interviewer evaluating correctness. Secondary users are analysts reviewing
flagged IDs and data-quality diagnostics.

### Success criterion

**Exact-output accuracy: 100% across both supplied fixtures and the focused
acceptance cases in this PRD.** Outputs must match membership, uniqueness, and
ordering; every rejected row and duplicate event must have an explicit
diagnostic. Repeat executions must produce identical results.

## 3. Confirmed product decisions

| Topic | Decision |
|---|---|
| Evaluation date | `2026-06-29`, regardless of the machine's current date |
| Day unit | Business days defined only as Monday-Friday |
| Interval | Exclude filing day; include evaluation day if it is a weekday |
| Threshold | Breach only when elapsed business days are strictly greater than 10 |
| Terminal status | Only exact `resolved` after trimming and case normalization |
| Other statuses | Unresolved, including `closed`, blank, and unknown labels |
| Slash dates | Day-first, never infer US month-first order |
| Duplicate IDs | Last physical CSV record for the normalized ID is authoritative |
| Invalid rows | Continue processing other cases and emit explicit diagnostics |
| Invalid last duplicate | Remains authoritative; exclude the ID rather than resurrecting an earlier valid record |
| Output order | Order of authoritative records in the source, not ID sort order or first occurrence |

The context's phrase "more than 10 days" is clarified by the user's selection
of the script's business-day rule. The user also selected last-occurrence-wins
and best-effort processing with diagnostics. Holidays are deliberately ignored.
Do not interpret notes in the fixture as alternate requirements.

## 4. Regulatory scope and limitations

[12 CFR 1005.11](https://www.consumerfinance.gov/rules-policy/regulations/1005/11/)
requires prompt investigation and generally determining whether an error
occurred within 10 business days of receiving notice of error. It also specifies
correction and consumer-notification deadlines. Under specified conditions,
provisional credit permits a longer investigation period; some cases have
20-business-day or 90-day extensions.

The supplied columns cannot establish those conditions. Specifically:

- `filed_date` is an exercise proxy, not verified receipt of qualifying notice.
- There is no provisional-credit date or amount, investigation completion date,
  consumer-notification date, transaction category, account-opening evidence,
  or exception eligibility.
- A generic `resolved` label does not prove timely correction or notification.
- Monday-Friday without holidays is not a production institution calendar.
- Last CSV occurrence is an exercise convention, not evidence of latest
  business state, since no update timestamp is supplied.

**Out of scope:** legal determinations, liability calculation, provisional-credit
checks, 45/90-day investigation checks, holiday calendars, regulatory exception
handling, and remediation actions.

Production expansion requires compliance approval, authoritative event
timestamps, transaction/account metadata, and an approved business-day calendar.
Do not simply relabel the MVP's flags as confirmed Regulation E breaches.

## 5. Observed data profile

Counts below are logical data records excluding the header. The extended
fixture contains a quoted multiline note, so physical lines are not row counts.

| Property | Original | Extended |
|---|---:|---:|
| Data records | 10 | 85 |
| Unique nonblank normalized IDs | 10 | 80 |
| Duplicate occurrences after the first | 0 | 4 |
| Missing/invalid-date records | 1 | 14 |
| Future-date records | 1 | 3 |
| Blank-ID records | 0 | 1 |
| Unique IDs with valid authoritative decision records | 8 | 63 |
| Expected flagged IDs | 5 | 36 |

Observed hazards include:

- ISO and day-first slash dates, surrounding whitespace, ambiguous slash
  values, invalid calendar dates, sentinel values, and unsupported timestamps.
- Case and whitespace differences in status, missing status, and labels
  containing but not equaling `resolved`.
- Quoted commas, escaped quotes, a multiline note, and instruction-like text.
- Currency strings, accounting notation, locale-specific numbers, and
  nonnumeric amounts, none of which participate in the decision.
- Equivalent duplicates and one conflicting ID, `D-1040`.

## 6. Functional requirements

### FR-1: Public interface and evaluation date

- Preserve `flag_reg_e(path: str)` as the entry point; return `list[str]`.
- Keep the existing `TODAY = date(2026, 6, 29)` default.
- Do not read the system clock or infer the evaluation date from file metadata.
- Keep date-counting logic separately testable with explicit date arguments.
- Do not mutate the source CSV.

### FR-2: CSV ingestion

- Use Python's standard-library CSV parser, not splitting lines or commas.
- Open using `newline=""` and `encoding="utf-8-sig"` to support CSV newline
  handling and an optional UTF-8 BOM.
- Normalize headers by stripping surrounding whitespace and case-folding.
- Require `dispute_id`, `filed_date`, and `status`. `amount` and `ops_note` are
  optional and ignored, as are other well-formed extra columns.
- Reject missing headers, missing required columns, empty header names, or
  duplicate names after normalization as file-level errors.
- Treat a header-only file as valid with an empty result and zero-record summary.
  A file with no header is invalid.
- Ignore physically empty lines according to CSV parser behavior. A populated
  record with empty fields is not an empty line.
- Validate record width against the header width. Too few or too many fields
  makes that logical record invalid; emit a diagnostic and continue.
- If a width-invalid record still supplies a usable ID in its designated
  column, it replaces any earlier occurrence as an invalid authoritative record.
- Use strict CSV parsing. Unrecoverable quoting/CSV syntax errors, decoding
  errors, and I/O errors abort processing; never return a partial success result.

### FR-3: Normalization and field validation

**Dispute ID**

- Strip surrounding whitespace; require a nonempty value.
- Preserve case and internal characters. Do not impose a `D-####` format.
- Return the trimmed ID. A blank ID cannot be grouped and is rejected.

**Status**

- Strip surrounding whitespace and case-fold.
- Exclude only exact `resolved` from SLA flags.
- `unresolved`, `not resolved`, `resolved_pending`, `closed`, `pending`,
  `escalated`, and `RESOLVED - pending audit` remain unresolved.
- Blank/whitespace-only status remains unresolved but emits a
  `MISSING_STATUS` warning. Do not silently convert it to resolved.
- Other labels follow the confirmed non-resolved rule without needing a
  status vocabulary or substring matching.

**Filing date**

- Strip surrounding whitespace.
- Accept only `YYYY-MM-DD` with two-digit month/day, or day-first
  `D/M/YYYY`, allowing one or two digits for day and month.
- Require ASCII digits and a four-digit year; validate actual calendar dates.
- Interpret `06/05/2026` as May 6 and `3/6/2026` as June 3.
- Treat empty/whitespace, `N/A`, and `NULL` (case-insensitive) as missing dates.
- Reject impossible dates, year-first slash values, other separators,
  two-digit years, date-time strings, and relative dates.
- Reject dates later than `TODAY`; do not clamp negative ages to zero.
- Validate required fields even on resolved records so data-quality problems
  remain visible. A resolved record with a bad date is not a valid decision record.

**Non-decision fields**

- Do not parse, validate, execute, or interpret amounts or notes.
- Quoted commas, multiline notes, and escaped quotes are normal CSV content.
- Instruction-like content in `D-1063` is inert data and must not affect output.

### FR-4: Duplicate resolution

- Group by trimmed, case-sensitive ID.
- Replace the prior record on every occurrence, including an invalid later
  record. Never prefer an older valid record over the selected last occurrence.
- Emit one `DUPLICATE_ID` warning for each occurrence after the first, with the
  replaced and replacement logical record numbers.
- Compare normalized decision fields to distinguish equivalent duplicates from
  conflicts. Differences in `amount` or `ops_note` do not constitute a
  decision-field conflict. Diagnostics should identify changed decision fields.
- Retain an authoritative record index and explicitly order output by that
  index. Ordinary replacement in an insertion-ordered dictionary is not enough:
  it preserves first insertion order.
- For `D-1040`, the final resolved record overrides the earlier open record,
  so the ID is not returned.
- `D-1006`, `D-1020`, and `D-1070` each have equivalent decision duplicates.
  Their last occurrences determine position; return each ID at most once.

### FR-5: Business-day evaluation

For valid authoritative records:

```text
elapsed_business_days =
    count of Monday-Friday dates d where filed_date < d <= TODAY

flag = normalized_status != "resolved" and elapsed_business_days > 10
```

- Exactly 10 days is not a breach; 11 days is a breach.
- Filing today produces zero elapsed days.
- Weekend filings are valid; weekdays after filing are counted normally.
- Do not shift filing dates to a weekday or skip weekdays labeled as holidays.
- Support historical dates and leap years without arbitrary lookback limits.
- Prefer full-week arithmetic plus a bounded remainder, avoiding iteration over
  every elapsed day for each record.

### FR-6: Diagnostics and failure contract

Use standard-library logging to expose diagnostics without changing the
list-returning API. Library code must not install global logging handlers;
the CLI configures logging to stderr.

Each row diagnostic includes a stable code, logical data-record number
(1-based, excluding the header), normalized ID when available, field, and
action. Duplicate diagnostics include both record numbers. Physical line-end
information may be added, but must not replace logical record numbering.

Required codes:

| Code | Action |
|---|---|
| `MISSING_ID` | Reject ungroupable record |
| `MISSING_DATE` | Retain as invalid authoritative record if ID exists |
| `INVALID_DATE` | Retain as invalid authoritative record if ID exists |
| `FUTURE_DATE` | Retain as invalid authoritative record if ID exists |
| `ROW_WIDTH_MISMATCH` | Reject decision record; apply ID precedence if identifiable |
| `MISSING_STATUS` | Evaluate as unresolved with warning |
| `DUPLICATE_ID` | Replace earlier occurrence; report equivalence or conflict |

Emit an end-of-run summary of records read, unique IDs, duplicate replacements,
rejected records, authoritative invalid IDs, missing-status records, and flags.
Keep row issues separate from selected-ID results: superseded records can have
diagnostics even when their final ID is valid.

Do not log whole rows, amounts, or notes. File-level failures must propagate
from the library with a useful error; the CLI reports them and exits nonzero.
No broad exception catch or fallback to `[]` on failure.

### FR-7: CLI

- Accept an explicit CSV path, for example:
  `python flag_reg_e.py disputes_messy_extended.csv`.
- Replace the current main block's reference to nonexistent
  `disputes_messy.csv`; missing CLI arguments display usage.
- Resolve supplied relative paths against the caller's working directory.
- Print only a JSON array of normalized flagged IDs to stdout.
- Send row warnings and the summary to stderr.
- Exit `0` when a structurally readable file is evaluated, even with row
  rejections; exit `2` for argument or file-level failures.
- Emit no success array on file-level failure.
- Usage/help must warn that results are exercise SLA flags and that row
  rejections mean incomplete coverage, not a clean compliance result.

## 7. Acceptance tests

### Exact golden outputs

Both outputs below were checked using an independent PowerShell CSV parser and
date calculation against the supplied files and confirmed policies. This
validates the PRD oracle, not the still-unimplemented Python function.

**Original: 5 IDs, in this exact order**

```json
["D-1001", "D-1003", "D-1006", "D-1008", "D-1009"]
```

**Extended: 36 IDs, in this exact order**

```json
[
  "D-1001", "D-1003", "D-1008", "D-1009",
  "D-1013", "D-1014", "D-1015",
  "D-1024", "D-1025", "D-1026", "D-1027", "D-1028", "D-1029", "D-1030",
  "D-1031", "D-1032", "D-1033", "D-1034", "D-1035", "D-1036", "D-1037",
  "D-1038", "D-1039", "D-1043", "D-1058", "D-1059", "D-1061", "D-1063",
  "D-1066", "D-1067", "D-1068", "D-1069", "D-1071", "D-1079",
  "D-1006", "D-1070"
]
```

### Boundary and fixture assertions

| Case | Expected |
|---|---|
| `D-1004`, `D-1011`, `D-1062`, `D-1080`: June 15, unresolved | 10 business days; not flagged |
| `D-1009`, `D-1079`: June 12, unresolved | 11 business days; flagged |
| `D-1014`, `D-1015`: June 13/14 weekend filings | 11 business days; flagged |
| `D-1018`: June 29 | 0 business days; not flagged |
| `D-1019`: June 28 | 1 business day; not flagged |
| `D-1060`: June 19 | 6 business days; not flagged |
| `D-1072`, `D-1073`: June 18/17 | 7/8 business days; not flagged |
| `D-1058`, `D-1059`: December 31 / January 1 | 128/127 business days; flagged; holidays ignored |
| `D-1021` through `D-1023` | Normalized exact resolved; not flagged |
| `D-1024` through `D-1030` | Nonterminal, including blank statuses; flagged |
| `D-1043` | Valid February 29, 2024; flagged |
| `D-1044` | Valid leap date, resolved; not flagged |
| `D-1061`, `D-1062` | Escaped quotes and multiline notes do not break parsing |
| `D-1063` | Instruction-like note ignored; flagged |
| `D-1040` | Last resolved record wins; not flagged |
| `D-1006`, `D-1070` | Returned once each, at their last-record positions |
| `D-1020` | Equivalent duplicate despite amount change; not flagged |
| `" D-1071 "` | Returned as `D-1071` |

### Rejection and diagnostic assertions

- Original: reject decision records for `D-1005` (missing date) and `D-1010`
  (future date), with one corresponding diagnostic each.
- Extended missing dates: `D-1005`, `D-1048`, `D-1049`, `D-1050`.
- Extended invalid dates: `D-1041`, `D-1042`, and `D-1045` through `D-1047`,
  plus `D-1051` through `D-1055`.
- Extended future dates: `D-1010`, `D-1056`, `D-1057`.
- Extended logical record 85: `MISSING_ID`; not returned.
- Extended: 18 rejected records total, 17 authoritative invalid IDs,
  4 duplicate warnings, and 2 missing-status warnings.

### Additional constructed cases

Add focused tests for behavior not fully exercised by the supplied fixtures:

1. Exactly 10 and 11 business days, evaluation on weekends, same-day filing,
   leap-year transitions, and a long historical interval.
2. Missing/duplicate normalized headers, UTF-8 BOM, normalized header casing,
   a header-only file, and a zero-byte file.
3. A well-formed minimal three-column CSV without amount or notes.
4. Too few/many fields, malformed quoting, invalid encoding, and missing files.
5. An invalid final duplicate superseding a valid breached row; a valid final
   duplicate superseding an invalid row.
6. A duplicate changing filing date; whitespace-normalized equivalent IDs;
   case-distinct IDs remaining separate.
7. A resolved row with an invalid date still producing a diagnostic.
8. Blank status remaining unresolved; no substring-based resolution.
9. Stable list order on repeated execution and clean separation of stdout and
   stderr, including correct failure exit codes and no partial JSON output.
10. Summary counts accounting for superseded records and invalid final IDs.

## 8. Implementation outline

Use standard-library components (`csv`, `datetime`, `logging`, `argparse`,
and `json`); no new runtime dependency is needed.

1. Validate the CSV header and parse logical records.
2. Normalize decision fields and attach validation issues and record identity.
3. Update the authoritative record per ID, retaining invalid final records.
4. Order authoritative records by their last source index.
5. Evaluate valid records with a pure business-day helper.
6. Return unique flagged IDs and expose diagnostics plus a summary.
7. Wire the CLI to the actual input path and JSON output.

Keep parsing, validation, duplicate selection, and day counting separable for
focused tests. Do not use an LLM, fuzzy date inference, or amount normalization
in the decision pipeline.

Expected resource usage: one CSV pass, memory proportional to unique IDs,
constant-time date counting per selected record, and at most `O(U log U)` work
to order `U` authoritative records. These fixtures do not justify distributed
processing or a database.

## 9. Delivery and definition of done

### Phase 1: Contracts and tests

Encode golden outputs and focused policy cases before implementing the body.
Use the repository's existing test runner if available; otherwise standard
library `unittest` is sufficient without adding third-party tooling.

### Phase 2: Function and diagnostics

Implement the pipeline and verify exact results for both supplied fixtures.
Verify duplicate precedence, record counts, and explicit rejection behavior.

### Phase 3: CLI and review

Exercise both fixtures through the CLI; validate JSON stdout, stderr diagnostics,
and exit behavior. Review naming/help so no output implies a legal conclusion.

**Done when:**

- The function is implemented with the specified return type and fixed date.
- Both exact golden arrays and all focused acceptance tests pass.
- Diagnostics and summaries match the defined row/ID accounting.
- Invalid rows never silently disappear and malformed files never masquerade
  as successful empty results.
- CLI examples refer to existing inputs and work from the documented location.
- Source fixtures are unchanged and regulatory limitations remain explicit.

### Remaining production questions

These do not block the exercise MVP: what proves receipt of notice, what proves
timely provisional credit, which calendar and exceptions apply, which event is
authoritative, and how analysts remediate or escalate potential violations.
Resolve them before any production compliance use.
