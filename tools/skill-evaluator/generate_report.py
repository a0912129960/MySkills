#!/usr/bin/env python3
"""Generate a self-contained offline evaluator report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def render_static_report(benchmark: dict[str, Any]) -> str:
    skill_name = html.escape(str(benchmark.get("skill_name", "")))
    rows: list[str] = []
    for name, summary in benchmark.get("configurations", {}).items():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(name))}</td>"
            f"<td>{summary.get('passed', 0)} / {summary.get('total', 0)}</td>"
            f"<td>{float(summary.get('pass_rate', 0)):.1%}</td>"
            f"<td>{html.escape(str(summary.get('mean_tokens')))}</td>"
            f"<td>{html.escape(str(summary.get('mean_duration_ms')))}</td>"
            "</tr>"
        )

    case_json = html.escape(
        json.dumps(benchmark.get("cases", []), ensure_ascii=False, indent=2)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{skill_name} evaluation</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 72rem; margin: auto; padding: 2rem; color: #17202a; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccd1d1; padding: .6rem; text-align: left; }}
th {{ background: #edf2f7; }}
pre {{ background: #f7f9f9; border: 1px solid #d5dbdb; padding: 1rem; overflow: auto; }}
</style>
</head>
<body>
<h1>{skill_name} evaluation</h1>
<table>
<thead><tr><th>Configuration</th><th>Assertions</th><th>Pass rate</th><th>Mean tokens</th><th>Mean ms</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<h2>Case evidence</h2>
<pre>{case_json}</pre>
</body>
</html>
"""


def write_static_report(
    benchmark: dict[str, Any], output_path: Path | str
) -> Path:
    output = Path(output_path)
    output.write_text(render_static_report(benchmark), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.benchmark.read_text(encoding="utf-8"))
    write_static_report(data, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
