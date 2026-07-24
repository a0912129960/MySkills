"""MySkills-owned deterministic CLI for the managed Wiki suite."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version as distribution_version
import json
import os
import sys
from pathlib import Path

from obsidian_wiki import config_resolution


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _config_home() -> Path:
    override = os.environ.get("OBSIDIAN_WIKI_CONFIG_HOME", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return config_resolution.user_home() / ".obsidian-wiki"


def _config_path() -> Path:
    return _config_home() / "config"


def _content_hash() -> str:
    digest = hashlib.sha256()
    package = Path(__file__).resolve().parent
    for path in sorted(package.rglob("*.py"), key=lambda item: item.as_posix()):
        relative = path.relative_to(package).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def local_version() -> str:
    release = "0.0.0"
    package_json = _repo_root() / "package.json"
    try:
        release = str(json.loads(package_json.read_text(encoding="utf-8"))["version"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        try:
            release = distribution_version("obsidian-wiki-myskills")
        except PackageNotFoundError:
            pass
    return f"myskills-{release}+{_content_hash()[:12]}"


def _read_config_value(key: str) -> str:
    path = _config_path()
    if not path.is_file():
        return ""
    return config_resolution.read_config(path).get(key, "").strip()


def _json_print(value: object, *, pretty: bool) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2 if pretty else None,
            sort_keys=True,
        )
    )


def _resolved_vault(raw: str | None) -> Path | None:
    candidate = raw or _read_config_value("OBSIDIAN_VAULT_PATH")
    if not candidate:
        print(
            "error: vault not configured; pass a vault path or run obsidian-wiki setup",
            file=sys.stderr,
        )
        return None
    vault = Path(os.path.expandvars(os.path.expanduser(candidate))).resolve()
    if not vault.is_dir():
        print(f"error: vault not found: {vault}", file=sys.stderr)
        return None
    return vault


def _safe_initial_vault(vault: Path) -> list[str]:
    created: list[str] = []
    vault.mkdir(parents=True, exist_ok=True)
    directories = (
        "concepts",
        "entities",
        "projects",
        "references",
        "synthesis",
        "misc",
        "_raw",
        "_archives",
        "attachments",
    )
    for relative in directories:
        path = vault / relative
        if not path.exists():
            path.mkdir(parents=True)
            created.append(relative + "/")
    defaults = {
        "index.md": "# Wiki Index\n",
        "hot.md": "# Hot\n",
        "log.md": "# Activity Log\n",
        ".manifest.json": '{\n  "sources": {}\n}\n',
    }
    for relative, content in defaults.items():
        path = vault / relative
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(relative)
    return created


def cmd_setup(args: argparse.Namespace) -> int:
    config = _config_path()
    if config.exists():
        values = config_resolution.read_config(config)
        configured = values.get("OBSIDIAN_VAULT_PATH", "").strip()
        requested = str(Path(args.vault).expanduser().resolve()) if args.vault else ""
        if requested and configured and Path(configured).expanduser().resolve() != Path(requested):
            _json_print(
                {
                    "status": "conflict",
                    "config_path": str(config),
                    "vault_path": configured,
                    "error": "existing config is preserved; edit it explicitly to change vault",
                },
                pretty=args.pretty,
            )
            return 4
        if not configured:
            _json_print(
                {
                    "status": "conflict",
                    "config_path": str(config),
                    "vault_path": "",
                    "error": "existing config does not contain OBSIDIAN_VAULT_PATH",
                },
                pretty=args.pretty,
            )
            return 4
        vault = Path(os.path.expandvars(os.path.expanduser(configured))).resolve()
        status = "preserved"
    else:
        if not args.vault:
            _json_print(
                {
                    "status": "not-found",
                    "config_path": str(config),
                    "vault_path": "",
                    "error": "--vault is required for first setup",
                },
                pretty=args.pretty,
            )
            return 4
        vault = Path(args.vault).expanduser().resolve()
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(f'OBSIDIAN_VAULT_PATH="{vault}"\n', encoding="utf-8")
        status = "created"

    created = _safe_initial_vault(vault)
    result = {
        "status": status,
        "config_path": str(config),
        "vault_path": str(vault),
        "created": created,
        "preserved": not bool(created),
    }
    _json_print(result, pretty=args.pretty)
    return 0


def cmd_config_resolve(args: argparse.Namespace) -> int:
    config = _config_path()
    result = config_resolution._candidate(config, "global")
    if result is None:
        result = {
            "status": "not-found",
            "source": "global",
            "config_path": str(config),
            "vault_path": "",
            "error": "no config found",
        }
    _json_print(result, pretty=args.pretty)
    return 0 if result["status"] == "resolved" else 4


def cmd_graph_query(args: argparse.Namespace) -> int:
    from obsidian_wiki.graphrag import query

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    _json_print(
        query(vault, args.question, top_n=args.top, max_should_read=args.max_read),
        pretty=args.pretty,
    )
    return 0


def cmd_batch_plan(args: argparse.Namespace) -> int:
    from obsidian_wiki.batch import plan_batches

    vault = _resolved_vault(args.vault)
    source = Path(args.source_dir).expanduser().resolve()
    if vault is None:
        return 1
    if not source.is_dir():
        print(f"error: source directory not found: {source}", file=sys.stderr)
        return 1
    result = plan_batches(
        source,
        vault,
        max_batch_mb=args.max_mb,
        max_batch_files=args.max_files,
        skip_unchanged=not args.no_cache,
        include_code=args.include_code,
    )
    _json_print(result, pretty=args.pretty)
    return 0


def cmd_graph_analyse(args: argparse.Namespace) -> int:
    from obsidian_wiki.graph_analysis import analyse_vault

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    _json_print(analyse_vault(vault, top_n=args.top), pretty=args.pretty)
    return 0


def cmd_cache_check(args: argparse.Namespace) -> int:
    from obsidian_wiki.cache import check_sources

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    sources = [Path(item).expanduser().resolve() for item in args.sources]
    _json_print(check_sources(vault, sources), pretty=args.pretty)
    return 0


def cmd_cache_update(args: argparse.Namespace) -> int:
    from obsidian_wiki.cache import update_source

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    source = Path(args.source).expanduser().resolve()
    content_hash = update_source(vault, source, pages_produced=args.pages or [])
    _json_print(
        {"path": str(source), "content_hash": content_hash},
        pretty=args.pretty,
    )
    return 0


def cmd_cache_hash(args: argparse.Namespace) -> int:
    from obsidian_wiki.cache import hash_file

    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        print(f"error: path not found: {path}", file=sys.stderr)
        return 1
    _json_print({"path": str(path), "sha256": hash_file(path)}, pretty=args.pretty)
    return 0


def cmd_ast_extract(args: argparse.Namespace) -> int:
    from obsidian_wiki.ast_extractor import extract

    try:
        result = extract(Path(args.path).expanduser().resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _json_print(result, pretty=args.pretty)
    return 0


def _doctor_report(vault_override: str | None) -> dict[str, object]:
    checks: list[dict[str, str]] = []
    config = _config_path()
    resolution = config_resolution._candidate(config, "global")
    if resolution is None:
        checks.append(
            {
                "name": "config",
                "status": "fail",
                "detail": f"config not found: {config}",
            }
        )
        vault = None
    elif resolution["status"] != "resolved":
        checks.append(
            {
                "name": "config",
                "status": "fail",
                "detail": str(resolution["error"]),
            }
        )
        vault = None
    else:
        checks.append(
            {
                "name": "config",
                "status": "pass",
                "detail": str(config),
            }
        )
        vault = Path(vault_override or str(resolution["vault_path"])).expanduser().resolve()

    if vault is not None:
        if not vault.is_dir():
            checks.append(
                {"name": "vault", "status": "fail", "detail": f"not found: {vault}"}
            )
        else:
            checks.append({"name": "vault", "status": "pass", "detail": str(vault)})
            missing = [
                name
                for name in ("index.md", "hot.md", "log.md", ".manifest.json")
                if not (vault / name).is_file()
            ]
            checks.append(
                {
                    "name": "vault-shape",
                    "status": "warn" if missing else "pass",
                    "detail": "missing: " + ", ".join(missing) if missing else "complete",
                }
            )
            try:
                manifest = json.loads((vault / ".manifest.json").read_text(encoding="utf-8"))
                valid = isinstance(manifest, dict) and isinstance(
                    manifest.get("sources", {}), dict
                )
                if not valid:
                    raise ValueError("manifest root/sources must be objects")
                checks.append(
                    {"name": "manifest-json", "status": "pass", "detail": "valid"}
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                checks.append(
                    {"name": "manifest-json", "status": "fail", "detail": str(exc)}
                )
    statuses = {item["status"] for item in checks}
    status = "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"
    return {"status": status, "version": local_version(), "checks": checks}


def cmd_doctor(args: argparse.Namespace) -> int:
    report = _doctor_report(args.vault)
    if args.json:
        _json_print(report, pretty=args.pretty)
    else:
        print(f"obsidian-wiki doctor: {report['status']}")
        for check in report["checks"]:
            print(f"{check['status'].upper()} {check['name']}: {check['detail']}")
    return int(
        report["status"] == "fail" or (args.strict and report["status"] == "warn")
    )


def cmd_lint(args: argparse.Namespace) -> int:
    from obsidian_wiki.lint import lint_vault

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    report = lint_vault(vault, require_trust_ledger=True)
    if args.json:
        _json_print(report, pretty=args.pretty)
    else:
        print(f"obsidian-wiki lint: {report['status']}")
        print(f"pages: {report['stats']['pages']}  links: {report['stats']['link_count']}")
        for name, count in report["stats"]["findings"].items():
            print(f"{name}: {count}")
    return int(
        report["status"] == "fail" or (args.strict and report["status"] == "warn")
    )


def cmd_trust_record(args: argparse.Namespace) -> int:
    from obsidian_wiki.trust import (
        TRUST_LEDGER_RELATIVE_PATH,
        build_trust_ledger,
        update_trust_ledger,
        write_trust_ledger,
    )

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    path = vault / TRUST_LEDGER_RELATIVE_PATH
    try:
        if args.all:
            ledger = build_trust_ledger(vault, reviewed_at=args.reviewed_at)
            count = len(ledger["pages"])
        else:
            ledger = update_trust_ledger(
                vault,
                path,
                reviewed_at=args.reviewed_at,
                page_paths=args.page,
            )
            count = len(set(args.page))
        write_trust_ledger(path, ledger, vault=vault)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    result = {
        "status": "recorded",
        "ledger_path": str(path),
        "recorded_pages": count,
        "reviewed_at": args.reviewed_at,
        "method": ledger["method"],
    }
    _json_print(result, pretty=args.pretty)
    return 0


def cmd_trust_check(args: argparse.Namespace) -> int:
    from obsidian_wiki.trust import check_trust_ledger

    vault = _resolved_vault(args.vault)
    if vault is None:
        return 1
    report = check_trust_ledger(vault)
    _json_print(report, pretty=args.pretty)
    return int(
        report["status"] == "fail" or (args.strict and report["status"] == "warn")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obsidian-wiki",
        description="MySkills-owned deterministic CLI for the managed Wiki suite.",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"obsidian-wiki {local_version()}"
    )
    commands = parser.add_subparsers(dest="command")

    setup = commands.add_parser("setup", help="initialize or repair Wiki config and vault")
    setup.add_argument("--vault", help="absolute path to the single configured vault")
    setup.add_argument("--pretty", action="store_true")
    setup.set_defaults(func=cmd_setup)

    config = commands.add_parser("config", help="resolve Wiki configuration")
    config_commands = config.add_subparsers(dest="config_command")
    resolve = config_commands.add_parser("resolve", help="resolve the configured vault")
    resolve.add_argument("--cwd", help=argparse.SUPPRESS)
    resolve.add_argument("--pretty", action="store_true")
    resolve.set_defaults(func=cmd_config_resolve)

    graph_query = commands.add_parser("graph-query")
    graph_query.add_argument("vault")
    graph_query.add_argument("question")
    graph_query.add_argument("--top", type=int, default=8)
    graph_query.add_argument("--max-read", type=int, default=3)
    graph_query.add_argument("--pretty", action="store_true")
    graph_query.set_defaults(func=cmd_graph_query)

    batch = commands.add_parser("batch-plan")
    batch.add_argument("vault")
    batch.add_argument("source_dir")
    batch.add_argument("--max-mb", type=float, default=2.0)
    batch.add_argument("--max-files", type=int, default=20)
    batch.add_argument("--no-cache", action="store_true")
    batch.add_argument("--include-code", action="store_true")
    batch.add_argument("--pretty", action="store_true")
    batch.set_defaults(func=cmd_batch_plan)

    graph = commands.add_parser("graph-analyse")
    graph.add_argument("vault")
    graph.add_argument("--top", type=int, default=20)
    graph.add_argument("--pretty", action="store_true")
    graph.set_defaults(func=cmd_graph_analyse)

    cache_check = commands.add_parser("cache-check")
    cache_check.add_argument("vault")
    cache_check.add_argument("sources", nargs="+")
    cache_check.add_argument("--pretty", action="store_true")
    cache_check.set_defaults(func=cmd_cache_check)

    cache_update = commands.add_parser("cache-update")
    cache_update.add_argument("vault")
    cache_update.add_argument("source")
    cache_update.add_argument("--pages", nargs="*")
    cache_update.add_argument("--pretty", action="store_true")
    cache_update.set_defaults(func=cmd_cache_update)

    cache_hash = commands.add_parser("cache-hash")
    cache_hash.add_argument("path")
    cache_hash.add_argument("--pretty", action="store_true")
    cache_hash.set_defaults(func=cmd_cache_hash)

    ast = commands.add_parser("ast-extract")
    ast.add_argument("path")
    ast.add_argument("--pretty", action="store_true")
    ast.set_defaults(func=cmd_ast_extract)

    doctor = commands.add_parser("doctor")
    doctor.add_argument("--vault")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--pretty", action="store_true")
    doctor.add_argument("--strict", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    lint = commands.add_parser("lint")
    lint.add_argument("vault", nargs="?")
    lint.add_argument("--json", action="store_true")
    lint.add_argument("--pretty", action="store_true")
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(func=cmd_lint)

    trust_record = commands.add_parser("trust-record")
    trust_record.add_argument("vault", nargs="?")
    selection = trust_record.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--page", action="append")
    trust_record.add_argument("--reviewed-at", required=True)
    trust_record.add_argument("--approved", action="store_true", required=True)
    trust_record.add_argument("--pretty", action="store_true")
    trust_record.set_defaults(func=cmd_trust_record)

    trust_check = commands.add_parser("trust-check")
    trust_check.add_argument("vault", nargs="?")
    trust_check.add_argument("--pretty", action="store_true")
    trust_check.add_argument("--strict", action="store_true")
    trust_check.set_defaults(func=cmd_trust_check)

    query = commands.add_parser("query")
    query.add_argument("question")
    query.add_argument("--vault")
    query.add_argument("--top", type=int, default=8)
    query.add_argument("--max-read", type=int, default=3)
    query.add_argument("--json", action="store_true")
    query.add_argument("--pretty", action="store_true")
    query.set_defaults(func=cmd_graph_query)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not hasattr(args, "func"):
        build_parser().print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
