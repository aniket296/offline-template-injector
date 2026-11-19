"""Measures line coverage across all modules in src/ using Python's built-in sys.settrace."""

from __future__ import annotations

import collections
import json
from pathlib import Path
import pytest
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Line execution record: {abs_file_path: set(executed_line_numbers)}
executed_lines = collections.defaultdict(set)


def trace_lines(frame, event, arg):
    if event == "line":
        code = frame.f_code
        filename = code.co_filename
        if "src" in filename and not ".venv" in filename and not "tests" in filename:
            executed_lines[Path(filename).resolve()].add(frame.f_lineno)
    return trace_lines


def get_executable_lines(file_path: Path) -> set[int]:
    """Finds non-blank, non-comment lines."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    executable = set()
    in_multiline = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if '"""' in stripped or "'''" in stripped:
            count = stripped.count('"""') + stripped.count("'''")
            if count % 2 != 0:
                in_multiline = not in_multiline
                continue
        if in_multiline:
            continue
        executable.add(idx)
    return executable


def main() -> None:
    print("=" * 70)
    print("  MEASURING TEST EXECUTION & LINE COVERAGE ACROSS src/")
    print("=" * 70)

    # Attach trace hook
    sys.settrace(trace_lines)

    # 1. Run pytest programmatically
    ret = pytest.main(["-q", str(PROJECT_ROOT / "tests")])

    # 2. Run live GUI automation suite programmatically
    try:
        from _qa_gui_runner import run_full_qa_audit_suite
        run_full_qa_audit_suite()
    except Exception as e:
        print(f"GUI suite execution error: {e}")

    # Detach trace hook
    sys.settrace(None)

    print(f"\nPytest execution finished with exit code: {ret}")

    src_dir = PROJECT_ROOT / "src"
    total_exec = 0
    total_hit = 0
    coverage_table = []

    for py_file in sorted(src_dir.glob("**/*.py")):
        if py_file.name == "__init__.py":
            continue
        resolved = py_file.resolve()
        exec_lines = get_executable_lines(py_file)
        hit_lines = executed_lines.get(resolved, set()) & exec_lines

        total_exec += len(exec_lines)
        total_hit += len(hit_lines)

        pct = (len(hit_lines) / len(exec_lines) * 100) if exec_lines else 100.0
        coverage_table.append({
            "module": str(py_file.relative_to(PROJECT_ROOT)),
            "executable_lines": len(exec_lines),
            "hit_lines": len(hit_lines),
            "coverage_pct": round(pct, 1),
        })

    overall_pct = (total_hit / total_exec * 100) if total_exec else 100.0
    print(f"\n{'MODULE':<45} | {'LINES':<8} | {'HIT':<8} | {'COVERAGE'}")
    print("-" * 75)
    for row in coverage_table:
        print(f"{row['module']:<45} | {row['executable_lines']:<8} | {row['hit_lines']:<8} | {row['coverage_pct']}%")
    print("-" * 75)
    print(f"{'OVERALL src/ CORE & ENGINE COVERAGE':<45} | {total_exec:<8} | {total_hit:<8} | {overall_pct:.1f}%\n")

    out_file = PROJECT_ROOT / "_qa_test_assets" / "telemetry" / "coverage_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "overall_coverage_pct": round(overall_pct, 1),
        "total_executable": total_exec,
        "total_hit": total_hit,
        "modules": coverage_table,
    }, indent=2), encoding="utf-8")
    print(f"Coverage telemetry saved to: {out_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
