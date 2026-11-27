#!/usr/bin/env python3
"""Deterministic validation of the *published* Windows TLS dataset.

Does not inspect private PCAPNGs or claim to reproduce their TLS handshakes.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

CLIENTS = ("curl", "ps51", "ps77", "edge", "chrome", "firefox")
BROWSERS = ("edge", "chrome", "firefox")
SCHEMA = (
    "run_id", "state", "server_profile", "client", "repetition",
    "attempt", "cohort", "operator_result", "expected_group_or_result",
    "capture_sha256", "metadata_sha256", "client_hello_count",
    "server_hello_count", "hrr_count", "alert_count",
    "selected_groups", "validation",
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def expected_cases() -> dict[str, tuple[str, str, str]]:
    """run_id -> (cohort, expected operator result, expected selected group)."""
    cases = {}

    def add(s, p, c, r, a, cohort, result, group):
        run = f"{s}-{p}-{c}-r{r:02d}-a{a:02d}"
        if run in cases:
            raise AssertionError(f"duplicate expected run {run}")
        cases[run] = (cohort, result, group)

    for client in CLIENTS:
        for rep in (1, 2, 3):
            add("A", "S1", client, rep, 1, "primary", "HTTP200", "4588" if client in BROWSERS else "29")
            add("B", "S1", client, rep, 4 if client == "curl" and rep == 1 else 1, "primary", "HTTP200", "4588")
        if client in BROWSERS:
            add("A", "S2", client, 1, 3, "primary", "HTTP200", "4588")
        else:
            add("A", "S2", client, 1, 1, "primary", "TLS_ERROR", "")
        add("B", "S2", client, 1, 1, "primary", "HTTP200", "4588")

    for client in BROWSERS:
        for rep in (1, 2, 3):
            add("A", "S1", client, rep, 2, "supplemental", "HTTP200", "4588")
        add("A", "S2", client, 1, 4, "supplemental", "HTTP200", "4588")
    assert len(cases) == 60
    return cases


def validate(path: Path) -> list[str]:
    issues = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SCHEMA:
            return ["CSV columns differ from the frozen publication schema"]
        rows = list(reader)

    cases = expected_cases()
    seen = set()
    cohorts = Counter()
    groups = Counter()
    results = Counter()
    for row in rows:
        rid = row["run_id"]
        if rid in seen:
            issues.append(f"duplicate run_id: {rid}")
            continue
        seen.add(rid)
        if rid not in cases:
            issues.append(f"unregistered run_id: {rid}")
            continue
        cohort, operator, group = cases[rid]
        s, p, c, r, a = re.fullmatch(
            r"(A|B)-(S1|S2)-(curl|ps51|ps77|edge|chrome|firefox)-r(0[1-3])-a(0[1-9])", rid
        ).groups()
        checks = {
            "state": s, "server_profile": p, "client": c,
            "repetition": str(int(r)), "attempt": str(int(a)),
            "cohort": cohort, "expected_group_or_result": "TLS_ERROR" if not group else group,
            "selected_groups": group, "validation": "PASS",
        }
        for key, val in checks.items():
            if row[key] != val:
                issues.append(f"{rid}: invalid {key}: {row[key]!r}")
        if row["operator_result"].replace(" ", "").upper() != operator:
            issues.append(f"{rid}: unexpected operator_result")
        for key in ("capture_sha256", "metadata_sha256"):
            if not SHA256.fullmatch(row[key]):
                issues.append(f"{rid}: invalid {key}")
        try:
            ch, sh, hrr, alerts = (
                int(row[k]) for k in (
                    "client_hello_count", "server_hello_count", "hrr_count", "alert_count"
                )
            )
            if ch < 1 or sh < 0 or hrr != 0 or alerts < 0:
                issues.append(f"{rid}: invalid handshake counts")
            if operator == "TLS_ERROR":
                if sh != 0 or alerts != 1:
                    issues.append(f"{rid}: expected failed handshake counts")
            elif sh < 1 or sh > ch:
                issues.append(f"{rid}: selected ServerHello without corresponding ClientHello")
        except ValueError:
            issues.append(f"{rid}: noninteger handshake count")
        cohorts[cohort] += 1
        groups[group or "none"] += 1
        results[operator] += 1

    if len(rows) != 60 or seen != set(cases):
        issues.append(f"expected exactly the 60 specified runs, got {len(rows)} rows")
    if cohorts != Counter({"primary": 48, "supplemental": 12}):
        issues.append(f"unexpected cohort counts: {cohorts}")
    if groups != Counter({"4588": 48, "29": 9, "none": 3}):
        issues.append(f"unexpected negotiated groups: {groups}")
    if results != Counter({"HTTP200": 57, "TLS_ERROR": 3}):
        issues.append(f"unexpected operator results: {results}")
    return issues


def main() -> int:
    default = Path(__file__).resolve().parents[1] / "docs/windows-tls-reality-check/v0.1/results.csv"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    try:
        errors = validate(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: cannot validate {path}: {exc}", file=sys.stderr)
        return 1
    if errors:
        for issue in errors:
            print(f"FAIL: {issue}", file=sys.stderr)
        return 1
    print("PASS: public dataset — 60 selected runs, 48 primary + 12 supplemental")
    print("PASS: groups 4588=48, 29=9, failed=3; operator outcomes 57 HTTP200 + 3 TLS_ERROR")
    print("SCOPE: CSV consistency only; private PCAPNG evidence is not available to CI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
