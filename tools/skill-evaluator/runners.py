#!/usr/bin/env python3
"""Construct and execute isolated Claude and Codex evaluator commands."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
from typing import Iterable


TARGETS = ("claude", "codex")
RUNTIME_TOOLS = ("obsidian-wiki", "skill-evaluator")
RUNTIME_GUARD = r'''from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


READ_ONLY_COMMANDS = {
    "obsidian-wiki": {
        "--help", "-h", "--version", "-V", "list", "info", "config",
        "graph-query", "batch-plan", "graph-analyse", "cache-check",
        "cache-hash", "ast-extract", "doctor", "lint", "trust-check", "query",
    },
    "skill-evaluator": {
        "--help", "-h", "validate", "digest", "smoke",
    },
}


def _require_workspace_path(value: str, workspace: Path) -> None:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        candidate.resolve().relative_to(workspace)
    except ValueError as error:
        raise ValueError(f"path escapes evaluation workspace: {value}") from error


def _validate_obsidian_paths(
    arguments: list[str],
    workspace: Path,
    source: Path,
) -> None:
    sys.path.insert(0, str(source))
    try:
        from obsidian_wiki.cli import build_parser

        try:
            parsed = build_parser().parse_args(arguments)
        except SystemExit as error:
            if error.code == 0:
                return
            raise ValueError("invalid read-only runtime arguments") from error
    finally:
        sys.path.pop(0)
    for field in ("vault", "cwd", "path", "source", "source_dir"):
        value = getattr(parsed, field, None)
        if value:
            _require_workspace_path(str(value), workspace)
    for value in getattr(parsed, "sources", None) or ():
        _require_workspace_path(str(value), workspace)


def _validate_evaluator_paths(arguments: list[str], workspace: Path) -> None:
    command, *values = arguments
    positional = [item for item in values if not item.startswith("-")]
    fixed_positions = {
        "validate": (0,),
        "digest": (0,),
    }
    for index in fixed_positions.get(command, ()):
        if index < len(positional):
            _require_workspace_path(positional[index], workspace)
def main() -> int:
    tool, source_text, safety, workspace_text, *arguments = sys.argv[1:]
    workspace = Path(workspace_text).resolve()
    source = Path(source_text).resolve()
    if (
        safety == "read-only"
        and (not arguments or arguments[0] not in READ_ONLY_COMMANDS[tool])
    ):
        command = arguments[0] if arguments else "<default>"
        print(
            f"{tool}: command blocked by read-only evaluation policy: {command}",
            file=sys.stderr,
        )
        return 2
    if safety == "read-only" and tool == "obsidian-wiki":
        try:
            _validate_obsidian_paths(arguments, workspace, source)
        except ValueError as error:
            print(f"{tool}: {error}", file=sys.stderr)
            return 2
    if safety == "read-only" and tool == "skill-evaluator":
        try:
            _validate_evaluator_paths(arguments, workspace)
        except ValueError as error:
            print(f"{tool}: {error}", file=sys.stderr)
            return 2
    env = os.environ.copy()
    if tool == "obsidian-wiki":
        env["PYTHONPATH"] = str(source)
        command = [sys.executable, "-m", "obsidian_wiki", *arguments]
    else:
        command = [sys.executable, str(source / "skill_evaluator.py"), *arguments]
    return subprocess.run(command, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
'''


def prepare_evaluation_workspace(
    skill_paths: Iterable[Path | str],
    target: str,
    workspace: Path | str,
    *,
    fixtures: Iterable[dict[str, str]] = (),
    git_fixture: dict[str, list[dict[str, str]]] | None = None,
) -> Path:
    """Stage only declared Skills and deterministic UTF-8 fixture files."""

    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if git_fixture is not None:
        _prepare_git_fixture(root, git_fixture)
    for skill_path in skill_paths:
        prepare_isolated_workspace(skill_path, target, root)
    _write_fixture_files(root, fixtures)
    return root


def prepare_runtime_environment(
    workspace: Path | str,
    runtime_tool_sources: dict[str, str],
    runtime_tool_digests: dict[str, str],
    *,
    repo_root: Path | str,
    safety: str,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Stage allowlisted repo tools without inheriting user tool settings."""

    if (
        not isinstance(runtime_tool_sources, dict)
        or not isinstance(runtime_tool_digests, dict)
        or set(runtime_tool_sources) != set(runtime_tool_digests)
        or any(name not in RUNTIME_TOOLS for name in runtime_tool_sources)
        or safety not in {"read-only", "temporary-workspace"}
    ):
        raise ValueError("runtime tool plan is invalid")

    root = Path(workspace).resolve()
    repository = Path(repo_root).resolve()
    runtime_root = root / ".runtime"
    local_app_data = runtime_root / "localappdata"
    myskills_root = local_app_data / "MySkills"
    tools_root = myskills_root / "tools"
    bin_root = myskills_root / "bin"
    config_root = root / ".obsidian-wiki"
    tools_root.mkdir(parents=True, exist_ok=True)
    bin_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)
    (bin_root / "runtime_guard.py").write_text(
        RUNTIME_GUARD,
        encoding="utf-8",
    )

    for name, source_text in runtime_tool_sources.items():
        source = Path(source_text).resolve()
        expected_source = (repository / "tools" / name).resolve()
        if source != expected_source:
            raise ValueError(
                f"runtime tool source is outside the repository allowlist: {name}"
            )
        if not source.is_dir():
            raise ValueError(f"runtime tool source is unavailable: {source}")
        tracked_files = _tracked_runtime_files(repository, source)
        expected_digest = runtime_tool_digests[name]
        if _files_digest(source, tracked_files) != expected_digest:
            raise ValueError(f"runtime tool source digest is stale: {name}")
        destination = tools_root / name
        if destination.exists():
            shutil.rmtree(destination)
        for relative in tracked_files:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
        if _files_digest(destination, tracked_files) != expected_digest:
            raise ValueError(f"runtime tool copy digest mismatch: {name}")
        _write_runtime_launcher(name, bin_root, safety, root)

    env = dict(base_env) if base_env is not None else evaluator_environment()
    original_path = env.get("PATH", "")
    env["LOCALAPPDATA"] = str(local_app_data.resolve())
    env["OBSIDIAN_WIKI_CONFIG_HOME"] = str(config_root.resolve())
    env["PATH"] = str(bin_root.resolve()) + os.pathsep + original_path
    return env


def _write_runtime_launcher(
    name: str,
    bin_root: Path,
    safety: str,
    workspace: Path,
) -> None:
    python = sys.executable.replace("%", "%%")
    if name not in RUNTIME_TOOLS:
        raise ValueError(f"unsupported runtime tool: {name}")
    content = (
        "@echo off\n"
        f'"{python}" "%~dp0runtime_guard.py" "{name}" '
        f'"%~dp0..\\tools\\{name}" "{safety}" "{workspace}" %*\n'
    )
    (bin_root / f"{name}.cmd").write_text(content, encoding="utf-8")


def _prepare_git_fixture(
    root: Path,
    git_fixture: dict[str, list[dict[str, str]]],
) -> None:
    if (
        not isinstance(git_fixture, dict)
        or set(git_fixture) != {"baseline_files", "working_tree_files"}
    ):
        raise ValueError(
            "git_fixture fields must be baseline_files and working_tree_files"
        )
    if (root / ".git").exists():
        raise ValueError("evaluation Git fixture workspace is already a repository")
    baseline = git_fixture["baseline_files"]
    working_tree = git_fixture["working_tree_files"]
    if (
        not isinstance(baseline, list)
        or not baseline
        or not isinstance(working_tree, list)
    ):
        raise ValueError("git_fixture file collections must be arrays")

    empty_template = root / ".myskills-empty-git-template"
    empty_template.mkdir()
    git_env = _git_fixture_environment(empty_template)
    _run_git(root, ["init", "--quiet"], env=git_env)
    empty_template.rmdir()
    _run_git(
        root,
        ["config", "--local", "user.name", "MySkills Evaluation Fixture"],
        env=git_env,
    )
    _run_git(
        root,
        [
            "config",
            "--local",
            "user.email",
            "evaluation@myskills.invalid",
        ],
        env=git_env,
    )
    _run_git(
        root,
        ["config", "--local", "core.autocrlf", "false"],
        env=git_env,
    )
    _run_git(
        root,
        ["config", "--local", "commit.gpgSign", "false"],
        env=git_env,
    )
    empty_hooks = root / ".git" / "myskills-empty-hooks"
    empty_hooks.mkdir()
    _run_git(
        root,
        ["config", "--local", "core.hooksPath", str(empty_hooks)],
        env=git_env,
    )
    _write_fixture_files(root, baseline)
    _run_git(root, ["add", "--all"], env=git_env)
    commit_env = git_env.copy()
    commit_env.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
        }
    )
    _run_git(
        root,
        [
            "-c",
            f"core.hooksPath={empty_hooks}",
            "-c",
            "commit.gpgSign=false",
            "commit",
            "--quiet",
            "-m",
            "fixture baseline",
        ],
        env=commit_env,
    )
    _write_fixture_files(root, working_tree)


def _git_fixture_environment(empty_template: Path) -> dict[str, str]:
    env = _isolated_git_environment(os.environ)
    env["GIT_TEMPLATE_DIR"] = str(empty_template.resolve())
    return env


def _isolated_git_environment(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    for key in tuple(env):
        if key.upper().startswith("GIT_"):
            env.pop(key)
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return env


def _write_fixture_files(
    root: Path,
    fixtures: Iterable[dict[str, str]],
) -> None:
    seen: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict) or set(fixture) != {"path", "content"}:
            raise ValueError("fixture fields must be exactly path and content")
        relative = fixture["path"]
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or ":" in relative
            or relative.startswith("/")
            or any(
                part in {"", ".", ".."}
                or part.endswith((".", " "))
                for part in relative.split("/")
            )
            or any(
                part.lower()
                in {".agents", ".claude", ".codex", ".gemini", ".git"}
                for part in relative.split("/")
            )
        ):
            raise ValueError(f"unsafe evaluation fixture path: {relative!r}")
        if relative in seen:
            raise ValueError(f"duplicate evaluation fixture path: {relative}")
        seen.add(relative)
        content = fixture["content"]
        if not isinstance(content, str):
            raise ValueError(f"evaluation fixture content must be text: {relative}")
        destination = (root / Path(*relative.split("/"))).resolve()
        try:
            destination.relative_to(root)
        except ValueError as error:
            raise ValueError(
                f"evaluation fixture escapes the workspace: {relative}"
            ) from error
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            content.replace(
                "{{WORKSPACE}}",
                root.as_posix(),
            ).encode("utf-8")
        )


def _run_git(
    root: Path,
    arguments: list[str],
    *,
    env: dict[str, str] | None = None,
) -> None:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"Git fixture command failed: {detail}")


def _files_digest(path: Path, files: Iterable[Path]) -> str:
    root = path.resolve()
    digest = hashlib.sha256()
    for relative_path in files:
        item = root / relative_path
        relative = relative_path.as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(struct.pack("<i", len(relative)))
        digest.update(relative)
        digest.update(struct.pack("<q", len(content)))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _tracked_runtime_files(repo_root: Path, source: Path) -> list[Path]:
    repository = repo_root.resolve()
    runtime = source.resolve()
    relative_source = runtime.relative_to(repository)
    env = _isolated_git_environment(os.environ)
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            relative_source.as_posix(),
        ],
        cwd=repository,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"cannot enumerate runtime source files: {detail}")
    tracked: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        candidate = (repository / raw.decode("utf-8")).resolve()
        try:
            relative = candidate.relative_to(runtime)
        except ValueError as error:
            raise ValueError(
                f"tracked runtime file escapes source: {candidate}"
            ) from error
        if not candidate.is_file():
            raise ValueError(f"tracked runtime file is unavailable: {candidate}")
        tracked.append(relative)
    if not tracked:
        raise ValueError(f"runtime tool has no source-controlled files: {runtime}")
    return sorted(tracked, key=lambda item: item.as_posix())


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
    runtime_tools: Iterable[str] = (),
) -> list[str]:
    """Build the allowlisted target command without executing it."""

    if target not in TARGETS:
        raise ValueError(f"unsupported evaluator target: {target}")

    declared_runtime_tools = tuple(runtime_tools)
    if (
        len(declared_runtime_tools) != len(set(declared_runtime_tools))
        or any(name not in RUNTIME_TOOLS for name in declared_runtime_tools)
    ):
        raise ValueError("runtime tools are invalid")

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
            tools = ["Read", "Glob", "Grep"]
            allowed_tools = list(tools)
            if declared_runtime_tools:
                tools.append("Bash")
            allowed_tools.extend(
                f"Bash({name} *)" for name in declared_runtime_tools
            )
            command.extend(["--tools", ",".join(tools)])
            command.extend(["--allowedTools", ",".join(allowed_tools)])
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

    source_env = _isolated_git_environment(evaluator_environment())
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
