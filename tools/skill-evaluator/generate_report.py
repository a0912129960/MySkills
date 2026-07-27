#!/usr/bin/env python3
"""Generate a self-contained offline evaluator report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path, PurePosixPath
from typing import Any


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _json_text(value: object) -> str:
    return html.escape(
        json.dumps(value, ensure_ascii=False, indent=2),
        quote=True,
    )


def _relative_href(value: object) -> str:
    candidate = str(value or "").replace("\\", "/")
    path = PurePosixPath(candidate)
    if not candidate or path.is_absolute() or ".." in path.parts:
        return "#"
    return "./" + candidate


def _render_expectations(case: dict[str, Any]) -> str:
    items: list[str] = []
    for expectation in case.get("expectations") or ():
        passed = expectation.get("passed")
        evidence = str(expectation.get("evidence") or "")
        if evidence == "PENDING HUMAN REVIEW":
            state = "PENDING"
            css_class = "pending"
        elif passed is True:
            state = "PASS"
            css_class = "pass"
        else:
            state = "FAIL"
            css_class = "fail"
        items.append(
            "<li>"
            f'<span class="badge {css_class}">{state}</span> '
            f"<strong>{_escape(expectation.get('text'))}</strong>"
            f"<div class=\"evidence\">{_escape(evidence)}</div>"
            "</li>"
        )
    if not items:
        return (
            '<p><span class="badge pending">PENDING</span> '
            "No grading expectations were recorded.</p>"
        )
    return "<ul class=\"expectations\">" + "".join(items) + "</ul>"


def _render_fixtures(case: dict[str, Any]) -> str:
    fixtures = case.get("fixtures") or ()
    if not fixtures:
        return "<p>No fixture files declared.</p>"
    parts: list[str] = []
    for fixture in fixtures:
        parts.append(
            "<details>"
            f"<summary>{_escape(fixture.get('path'))}</summary>"
            f"<pre>{_escape(fixture.get('content'))}</pre>"
            "</details>"
        )
    return "".join(parts)


def _render_git_fixture(case: dict[str, Any]) -> str:
    git_fixture = case.get("git_fixture") or {}
    if not git_fixture:
        return "<p>No Git fixture declared.</p>"
    parts: list[str] = []
    for field, label in (
        ("baseline_files", "Committed baseline files"),
        ("working_tree_files", "Working-tree changes"),
    ):
        files = git_fixture.get(field) or ()
        rendered_files = []
        for fixture in files:
            rendered_files.append(
                "<details>"
                f"<summary>{_escape(fixture.get('path'))}</summary>"
                f"<pre>{_escape(fixture.get('content'))}</pre>"
                "</details>"
            )
        parts.append(
            f"<h4>{label}</h4>"
            + (
                "".join(rendered_files)
                if rendered_files
                else "<p>None declared.</p>"
            )
        )
    return "".join(parts)


def _render_declared_assertions(case: dict[str, Any]) -> str:
    assertions = case.get("assertions") or ()
    if not assertions:
        return (
            "<p>No plan-level assertions; use the configuration-specific "
            "grading criteria below.</p>"
        )
    return "<ul>" + "".join(
        f"<li>{_escape(assertion)}</li>" for assertion in assertions
    ) + "</ul>"


def _render_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "<p>No structured tool events were exposed by this target.</p>"
    parts: list[str] = []
    for index, event in enumerate(events, start=1):
        event_type = _escape(event.get("type"))
        if event.get("type") == "command_execution":
            body = (
                f"<p><strong>Command</strong></p>"
                f"<pre>{_escape(event.get('command'))}</pre>"
                f"<p><strong>Exit/status</strong>: "
                f"{_escape(event.get('exit_code'))} / "
                f"{_escape(event.get('status'))}</p>"
                f"<p><strong>Output</strong></p>"
                f"<pre>{_escape(event.get('output'))}</pre>"
            )
        elif event.get("type") == "agent_message":
            body = f"<pre>{_escape(event.get('text'))}</pre>"
        elif event.get("type") == "tool_use":
            body = (
                f"<p><strong>Tool</strong>: "
                f"{_escape(event.get('name'))}</p>"
                f"<p><strong>Input</strong></p>"
                f"<pre>{_json_text(event.get('input'))}</pre>"
            )
        elif event.get("type") == "tool_result":
            body = (
                f"<p><strong>Tool use ID</strong>: "
                f"{_escape(event.get('tool_use_id'))}</p>"
                f"<p><strong>Error</strong>: "
                f"{_escape(event.get('is_error'))}</p>"
                f"<p><strong>Output</strong></p>"
                f"<pre>{_json_text(event.get('content'))}</pre>"
            )
        elif event.get("type") == "error":
            body = f"<pre>{_escape(event.get('message'))}</pre>"
        else:
            body = f"<pre>{_json_text(event)}</pre>"
        parts.append(
            "<details>"
            f"<summary>Event {index}: {event_type}</summary>"
            f"{body}</details>"
        )
    return "".join(parts)


def _render_run(case: dict[str, Any]) -> str:
    configuration = case.get("configuration")
    title = "With Skill" if configuration == "with_skill" else "Baseline"
    process = case.get("process") or {}
    model = case.get("model_evidence") or {}
    returncode = process.get("returncode")
    timed_out = process.get("timed_out")
    identity_returncode = case.get("target_identity_returncode")
    process_state = (
        "PROCESS PASS"
        if (
            identity_returncode == 0
            and returncode == 0
            and timed_out is False
        )
        else "PROCESS FAIL"
    )
    process_class = "pass" if process_state == "PROCESS PASS" else "fail"
    raw_isolation = case.get("isolation_violations")
    audit_state = case.get("isolation_audit_state")
    if audit_state is None:
        audit_state = (
            "fail" if isinstance(raw_isolation, list) and raw_isolation
            else "pass" if isinstance(raw_isolation, list)
            else "missing"
        )
    isolation_violations = (
        list(raw_isolation)
        if isinstance(raw_isolation, list)
        else []
    )
    isolation_passed = audit_state == "pass" and not isolation_violations
    isolation_state = (
        "ISOLATION PASS" if isolation_passed else "ISOLATION FAIL"
    )
    isolation_class = "pass" if isolation_passed else "fail"
    isolation_details = (
        "<ul>"
        + "".join(
            f"<li>{_escape(violation)}</li>"
            for violation in isolation_violations
        )
        + "</ul>"
        if isolation_violations
        else (
            "<p>No successful out-of-workspace tool access was detected.</p>"
            if isolation_passed
            else (
                "<p>Isolation audit is missing, malformed, or does not match "
                "the raw trace.</p>"
            )
        )
    )
    result_path = _relative_href(case.get("result_path"))
    grading_path = _relative_href(case.get("grading_path"))
    external_tool_evidence = case.get("external_tool_evidence") or {}
    return f"""
<article class="run-card">
  <h4>{title}</h4>
  <p>
    <span class="badge {process_class}">{process_state}</span>
    <span class="badge {isolation_class}">{isolation_state}</span>
    <span class="badge {_escape(case.get('review_state'))}">
      HUMAN REVIEW: {_escape(str(case.get('review_state')).upper())}
    </span>
  </p>
  <dl>
    <dt>Target identity</dt><dd>{_escape(case.get('target_identity'))}</dd>
    <dt>Identity return code</dt><dd>{_escape(identity_returncode)}</dd>
    <dt>Return code</dt><dd>{_escape(returncode)}</dd>
    <dt>Timed out</dt><dd>{_escape(timed_out)}</dd>
    <dt>Duration</dt><dd>{_escape(process.get('duration_ms'))} ms</dd>
    <dt>Total tokens</dt><dd>{_escape(process.get('total_tokens'))}</dd>
    <dt>Safety</dt><dd>{_escape(case.get('safety'))}</dd>
    <dt>Explicit Skill invocation</dt><dd>{_escape(case.get('explicit'))}</dd>
    <dt>Execution workspace</dt>
    <dd>{_escape(case.get('execution_workspace'))}</dd>
  </dl>
  <h5>Machine isolation audit</h5>
  <p>Audit state: {_escape(audit_state)}</p>
  {isolation_details}
  <h5>Exact logical launch command (includes the actual prompt)</h5>
  <pre>{_json_text(process.get('command'))}</pre>
  <p>
    <a href="{_escape(result_path)}">Raw result.json</a> ·
    <a href="{_escape(grading_path)}">Human grading.json</a>
  </p>
  <h5>Model's final response</h5>
  <pre class="response">{_escape(model.get('final_response'))}</pre>
  <h5>Declared assertions for this run</h5>
  {_render_declared_assertions(case)}
  <h5>Current assertion grading</h5>
  {_render_expectations(case)}
  <details>
    <summary>External runtime identity and setup</summary>
    <pre>{_json_text(external_tool_evidence)}</pre>
  </details>
  <details>
    <summary>Structured model/tool trace</summary>
    {_render_events(list(model.get('events') or ()))}
  </details>
  <details>
    <summary>Execution metadata</summary>
    <pre>{_json_text(model.get('metadata') or {})}</pre>
  </details>
  <details>
    <summary>Raw stdout</summary>
    <pre>{_escape(model.get('raw_stdout'))}</pre>
  </details>
  <details>
    <summary>Raw stderr</summary>
    <pre>{_escape(model.get('raw_stderr'))}</pre>
  </details>
  <details>
    <summary>Parse warnings</summary>
    <pre>{_json_text(model.get('parse_errors') or [])}</pre>
  </details>
</article>
"""


def _render_case_group(case_name: str, cases: list[dict[str, Any]]) -> str:
    exemplar = cases[0]
    baseline = exemplar.get("baseline") or {}
    targets: list[str] = []
    for target in ("claude", "codex"):
        if any(case.get("target") == target for case in cases):
            targets.append(target)
    target_sections: list[str] = []
    for target in targets:
        target_runs = {
            case.get("configuration"): case
            for case in cases
            if case.get("target") == target
        }
        cards = "".join(
            _render_run(target_runs[configuration])
            for configuration in ("with_skill", "baseline")
            if configuration in target_runs
        )
        target_sections.append(
            f"<h3>{_escape(target.title())}</h3>"
            f'<div class="comparison">{cards}</div>'
        )
    return f"""
<section class="case">
  <h2>{_escape(case_name)}</h2>
  <dl>
    <dt>Mode</dt><dd>{_escape(exemplar.get('mode'))}</dd>
    <dt>Expected invocation</dt>
    <dd>{_escape(exemplar.get('expected_invocation'))}</dd>
    <dt>Canonical Skill path</dt><dd>{_escape(exemplar.get('skill_path'))}</dd>
    <dt>Skill digest</dt><dd><code>{_escape(exemplar.get('skill_digest'))}</code></dd>
    <dt>Baseline kind</dt><dd>{_escape(baseline.get('kind'))}</dd>
    <dt>Baseline identity</dt><dd>{_escape(baseline.get('identity'))}</dd>
    <dt>Runtime tools</dt><dd>{_escape(', '.join(exemplar.get('runtime_tools') or ()) or 'none')}</dd>
    <dt>External tools</dt><dd>{_escape(', '.join(exemplar.get('external_tools') or ()) or 'none')}</dd>
    <dt>Companion Skills</dt><dd>{_escape(', '.join(exemplar.get('companion_skills') or ()) or 'none')}</dd>
  </dl>
  <h3>Declared/base prompt</h3>
  <pre>{_escape(exemplar.get('prompt'))}</pre>
  <details>
    <summary>Fixture files visible to both configurations</summary>
    {_render_fixtures(exemplar)}
  </details>
  <details>
    <summary>Git fixture repository state</summary>
    {_render_git_fixture(exemplar)}
  </details>
  {''.join(target_sections)}
</section>
"""


def render_static_report(benchmark: dict[str, Any]) -> str:
    skill_name = html.escape(str(benchmark.get("skill_name", "")))
    rows: list[str] = []
    for name, summary in benchmark.get("configurations", {}).items():
        review_states = summary.get("review_states") or {}
        review_state_text = ", ".join(
            f"{state}: {review_states.get(state, 0)}"
            for state in ("pending", "pass", "fail")
        )
        rows.append(
            "<tr>"
            f"<td>{_escape(name)}</td>"
            f"<td>{summary.get('passed', 0)} / {summary.get('total', 0)}</td>"
            f"<td>{float(summary.get('pass_rate', 0)):.1%}</td>"
            f"<td>{_escape(review_state_text)}</td>"
            f"<td>{_escape(summary.get('mean_tokens'))}</td>"
            f"<td>{_escape(summary.get('mean_duration_ms'))}</td>"
            "</tr>"
        )

    cases = list(benchmark.get("cases") or ())
    case_names = sorted(
        {
            str(case.get("case"))
            for case in cases
        }
    )
    case_sections = "".join(
        _render_case_group(
            case_name,
            [case for case in cases if str(case.get("case")) == case_name],
        )
        for case_name in case_names
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{skill_name} evaluation</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 96rem; margin: auto; padding: 2rem; color: #17202a; background: #f8fafc; }}
h1, h2, h3, h4, h5 {{ line-height: 1.2; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccd1d1; padding: .6rem; text-align: left; }}
th {{ background: #edf2f7; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f7f9f9; border: 1px solid #d5dbdb; padding: 1rem; overflow: auto; }}
code {{ overflow-wrap: anywhere; }}
.notice {{ border-left: .4rem solid #b7791f; background: #fffaf0; padding: 1rem; margin: 1rem 0 2rem; }}
.case {{ background: white; border: 1px solid #cbd5e0; border-radius: .5rem; padding: 1.25rem; margin: 2rem 0; }}
.comparison {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }}
.run-card {{ border: 1px solid #cbd5e0; border-radius: .4rem; padding: 1rem; min-width: 0; }}
.run-card h4 {{ margin-top: 0; }}
.response {{ min-height: 10rem; background: #f0fff4; }}
.badge {{ display: inline-block; border-radius: 999px; padding: .15rem .55rem; font-size: .78rem; font-weight: 700; margin-right: .35rem; background: #e2e8f0; }}
.badge.pass {{ color: #22543d; background: #c6f6d5; }}
.badge.fail {{ color: #742a2a; background: #fed7d7; }}
.badge.pending {{ color: #744210; background: #fefcbf; }}
dl {{ display: grid; grid-template-columns: max-content 1fr; gap: .25rem 1rem; }}
dt {{ font-weight: 700; }}
dd {{ margin: 0; min-width: 0; overflow-wrap: anywhere; }}
details {{ border-top: 1px solid #e2e8f0; padding: .55rem 0; }}
summary {{ cursor: pointer; font-weight: 650; }}
.expectations {{ padding-left: 1.3rem; }}
.expectations li {{ margin: .65rem 0; }}
.evidence {{ margin: .25rem 0 0; color: #4a5568; }}
@media (max-width: 70rem) {{ .comparison {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>{skill_name} evaluation</h1>
<div class="notice">
  <strong>Human-review evidence, not an automatic verdict.</strong>
  A successful process only proves that the model command completed. Compare
  With Skill against Baseline for each target, inspect the final response and
  tool trace, then record a specific PASS or FAIL reason in grading.json.
</div>
<table>
<thead><tr><th>Configuration</th><th>Recorded assertions</th><th>Recorded pass rate</th><th>Review states</th><th>Mean tokens</th><th>Mean ms</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
{case_sections}
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
