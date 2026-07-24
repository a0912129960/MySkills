#!/usr/bin/env python3
"""Construct and execute isolated Claude and Codex evaluator commands."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Iterable


TARGETS = ("claude", "codex")


def prepare_isolated_workspace(
    skill_path: Path | str,
    target: str,
    workspace: Path | str,
) -> Path:
    """Stage one canonical Skill at the target's project discovery path."""

    if target not in TARGETS:
        raise ValueError(f"unsupported evaluator target: {target}")
    source = Path(skill_path).resolve()
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"not a Skill directory: {source}")

    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    discovery_root = (
        root / ".claude" / "skills"
        if target == "claude"
        else root / ".agents" / "skills"
    )
    destination = discovery_root / source.name
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return root


def build_command(
    target: str,
    prompt: str,
    skill_path: Path,
    model: str | None = None,
    *,
    explicit: bool = True,
    baseline: bool = False,
    safety: str = "read-only",
) -> list[str]:
    """Build the allowlisted target command without executing it."""

    if target not in TARGETS:
        raise ValueError(f"unsupported evaluator target: {target}")

    skill = Path(skill_path).resolve()
    evaluation_prompt = prompt
    if explicit:
        evaluation_prompt += (
            f"\n\nEvaluate the installed Skill named ${skill.name}. "
            "Return only evidence produced in this isolated run."
        )
    if target == "claude":
        command = [
            "claude",
            "-p",
            evaluation_prompt,
            "--output-format",
            "json",
            "--no-session-persistence",
        ]
        if baseline:
            command.append("--disable-slash-commands")
        if safety == "read-only":
            command.extend(["--tools", "Read,Glob,Grep"])
        else:
            command.extend(["--tools", "Read,Write,Edit,Glob,Grep,Bash"])
        if model:
            command.extend(["--model", model])
        return command

    sandbox = "read-only" if safety == "read-only" else "workspace-write"
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--json",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        sandbox,
    ]
    if model:
        command.extend(["--model", model])
    command.append(evaluation_prompt)
    return command


def _read_stream(
    stream,
    label: str,
    output: queue.Queue[tuple[str, str | None]],
) -> None:
    try:
        for line in iter(stream.readline, ""):
            output.put((label, line))
    finally:
        output.put((label, None))
        stream.close()


def run_command(
    command: Iterable[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: float = 300,
) -> dict[str, object]:
    """Run a target using reader threads so pipe handling works on Windows."""

    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None and process.stderr is not None

    output: queue.Queue[tuple[str, str | None]] = queue.Queue()
    for stream, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
        threading.Thread(
            target=_read_stream,
            args=(stream, label, output),
            daemon=True,
        ).start()

    buffers = {"stdout": [], "stderr": []}
    closed: set[str] = set()
    timed_out = False
    while len(closed) < 2:
        remaining = timeout_seconds - (time.monotonic() - started)
        if remaining <= 0:
            timed_out = True
            process.kill()
            remaining = 1
        try:
            label, line = output.get(timeout=min(max(remaining, 0.01), 0.25))
        except queue.Empty:
            continue
        if line is None:
            closed.add(label)
        else:
            buffers[label].append(line)

    return_code = process.wait()
    return {
        "command": list(command),
        "returncode": return_code,
        "timed_out": timed_out,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "stdout": "".join(buffers["stdout"]),
        "stderr": "".join(buffers["stderr"]),
    }


def evaluator_environment() -> dict[str, str]:
    """Return a clean child environment without nested-session sentinels."""

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


@contextmanager
def isolated_target_environment(
    target: str,
    *,
    allow_ephemeral_auth_copy: bool,
):
    """Isolate user Skills while copying only auth into an OS temp directory."""

    if target not in TARGETS:
        raise ValueError(f"unsupported evaluator target: {target}")
    if not allow_ephemeral_auth_copy:
        raise PermissionError(
            "Model runs require --allow-ephemeral-auth-copy so user-wide "
            "Skill discovery can be isolated without losing CLI authentication."
        )

    source_env = evaluator_environment()
    with tempfile.TemporaryDirectory(prefix=f"myskills-{target}-auth-") as temp_dir:
        isolated = Path(temp_dir)
        env = source_env.copy()
        if target == "codex":
            env["CODEX_HOME"] = str(isolated)
            if not env.get("OPENAI_API_KEY"):
                source_home = Path(
                    source_env.get("CODEX_HOME", Path.home() / ".codex")
                )
                _copy_auth_file(source_home / "auth.json", isolated / "auth.json")
        else:
            env["CLAUDE_CONFIG_DIR"] = str(isolated)
            if not env.get("ANTHROPIC_API_KEY"):
                source_home = Path(
                    source_env.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")
                )
                _copy_auth_file(
                    source_home / ".credentials.json",
                    isolated / ".credentials.json",
                )
        yield env


def _copy_auth_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(
            f"CLI authentication file is unavailable for isolated evaluation: {source}"
        )
    shutil.copyfile(source, destination)
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
