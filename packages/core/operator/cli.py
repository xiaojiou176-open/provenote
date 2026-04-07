"""First-party operator CLI for Provenote outcome lanes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

import httpx

from packages.core.application.client import APIClient

DEFAULT_API_BASE = "http://127.0.0.1:5055"
DEFAULT_OUTPUT_DIR = Path.cwd()
DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_THRESHOLD = 0.97
DEFAULT_TIMEOUT = 300.0
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _normalize_api_base(raw_base: str | None) -> str:
    base = (
        raw_base
        or os.getenv("OPEN_NOTEBOOK_API_BASE")
        or os.getenv("OPEN_NOTEBOOK_URL")
        or DEFAULT_API_BASE
    ).rstrip("/")
    if base.endswith("/api"):
        return base[: -len("/api")]
    return base


def _resolve_password(cli_password: str | None) -> str | None:
    password = (
        cli_password
        if cli_password is not None
        else os.getenv("OPEN_NOTEBOOK_PASSWORD")
    )
    if password is None:
        return None
    stripped = password.strip()
    return stripped or None


def _requires_auth(api_base: str) -> bool:
    parsed = urlparse(api_base)
    host = (parsed.hostname or "").lower()
    return host not in LOCAL_HOSTS


def _validate_remote_config(api_base: str, password: str | None) -> None:
    parsed = urlparse(api_base)
    if parsed.username or parsed.password:
        raise ValueError(
            "Credentials inside --api-base are not allowed. Use --password or "
            "OPEN_NOTEBOOK_PASSWORD instead."
        )
    if _requires_auth(api_base) and not password:
        raise ValueError(
            "OPEN_NOTEBOOK_PASSWORD or --password is required for non-local "
            "--api-base targets."
        )


def _build_client(api_base: str, password: str | None) -> APIClient:
    resolved_password = _resolve_password(password)
    _validate_remote_config(api_base, resolved_password)
    client = APIClient(base_url=api_base)
    if resolved_password:
        client.headers["Authorization"] = f"Bearer {resolved_password}"
    return client


def _normalize_prefixed_id(raw_id: str, prefix: str) -> str:
    return raw_id if raw_id.startswith(f"{prefix}:") else f"{prefix}:{raw_id}"


def _coerce_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return result[0]
    raise RuntimeError("Unexpected API response shape.")


def _build_named_output_path(name: str, output_dir: str | None) -> Path:
    destination = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    if not destination.is_absolute():
        destination = DEFAULT_OUTPUT_DIR / destination
    destination.mkdir(parents=True, exist_ok=True)
    return destination / name


def _build_text_output_path(run_id: str, output: str | None) -> Path:
    filename = f"auditable-{run_id.replace(':', '_')}.md"
    if not output:
        return DEFAULT_OUTPUT_DIR / filename

    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = DEFAULT_OUTPUT_DIR / output_path
    if output_path.exists() and output_path.is_dir():
        return output_path / filename
    if output.endswith("/") or output.endswith("\\"):
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def _write_text_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def _write_binary_file(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return str(path)


def _fetch_health(api_base: str, password: str | None) -> dict[str, Any]:
    try:
        resolved_password = _resolve_password(password)
        headers = {}
        if resolved_password:
            headers["Authorization"] = f"Bearer {resolved_password}"
        response = httpx.get(
            f"{api_base}/health", headers=headers, timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_status(payload: dict[str, Any]) -> None:
    print(f"api_base={payload['api_base']}")
    print(f"healthy={payload['healthy']}")
    print(f"health_payload={json.dumps(payload['health'], ensure_ascii=False)}")
    print(f"auth_configured={payload['auth_configured']}")
    print(f"operator_entrypoint={payload['entrypoints']['operator']}")
    print(f"mcp_entrypoint={payload['entrypoints']['mcp']}")
    print("inspect_surfaces=" + ",".join(payload["inspect_surfaces"]))
    print("operator_workflows=" + ",".join(payload["operator_workflows"]))


def _print_inspection(payload: dict[str, Any]) -> None:
    print(f"object_type={payload['object_type']}")
    print(f"object_id={payload['object_id']}")
    print(f"payload={json.dumps(payload['payload'], ensure_ascii=False)}")


def _print_thread_to_draft(payload: dict[str, Any]) -> None:
    print(f"thread_id={payload['thread_id']}")
    print(f"draft_id={payload['draft']['id']}")
    print(f"verified={payload['verified']}")
    if payload.get("saved_markdown"):
        print(f"saved_markdown={payload['saved_markdown']}")
    if payload.get("saved_bundle"):
        print(f"saved_bundle={payload['saved_bundle']}")


def _print_auditable_markdown(payload: dict[str, Any]) -> None:
    print(f"source_id={payload['source_id']}")
    print(f"run_id={payload['run']['id']}")
    print(f"saved_markdown={payload['saved_markdown']}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="provenote",
        description="Operate Provenote outcome lanes from a first-party CLI surface.",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("OPEN_NOTEBOOK_URL") or DEFAULT_API_BASE,
        help="Provenote API base URL. Accepts root URL or /api URL.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Override OPEN_NOTEBOOK_PASSWORD for this command only.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser(
        "status",
        help="Inspect operator readiness without mutating outcome objects.",
    )
    status.add_argument("--json", action="store_true", help="Print JSON output.")
    status.add_argument(
        "--require-healthy",
        action="store_true",
        help="Return non-zero when the local /health check is unreachable or unhealthy.",
    )

    inspect = subparsers.add_parser(
        "inspect",
        help="Inspect one notebook or one outcome object before a workflow.",
    )
    inspect_subparsers = inspect.add_subparsers(dest="inspect_command", required=True)

    inspect_notebook = inspect_subparsers.add_parser(
        "notebook",
        help="Show notebook metadata plus draft and research-thread state.",
    )
    inspect_notebook.add_argument("notebook_id", help="Notebook id.")
    inspect_notebook.add_argument(
        "--source-id",
        default=None,
        help="Optional source id to include auditable-run state.",
    )
    inspect_notebook.add_argument(
        "--json", action="store_true", help="Print JSON output."
    )
    inspect_notebook.set_defaults(handler=_run_inspect_notebook)

    inspect_draft = inspect_subparsers.add_parser(
        "draft",
        help="Show one draft payload.",
    )
    inspect_draft.add_argument("draft_id", help="Draft id, e.g. draft:123 or 123.")
    inspect_draft.add_argument("--json", action="store_true", help="Print JSON output.")
    inspect_draft.set_defaults(handler=_run_inspect_draft)

    inspect_thread = inspect_subparsers.add_parser(
        "research-thread",
        help="Show one research thread payload.",
    )
    inspect_thread.add_argument(
        "thread_id",
        help="Research thread id, e.g. research_thread:123 or 123.",
    )
    inspect_thread.add_argument(
        "--json", action="store_true", help="Print JSON output."
    )
    inspect_thread.set_defaults(handler=_run_inspect_research_thread)

    inspect_run = inspect_subparsers.add_parser(
        "auditable-run",
        help="Show one auditable run payload.",
    )
    inspect_run.add_argument(
        "run_id",
        help="Auditable run id, e.g. auditable_run:123 or 123.",
    )
    inspect_run.add_argument("--json", action="store_true", help="Print JSON output.")
    inspect_run.set_defaults(handler=_run_inspect_auditable_run)

    auditable = subparsers.add_parser(
        "auditable-markdown",
        help="Create one auditable run and download its markdown.",
    )
    auditable.add_argument("source_id", help="Source id, e.g. source:123 or 123.")
    auditable.add_argument(
        "--model-id",
        default=DEFAULT_MODEL,
        help="Model name for the auditable run.",
    )
    auditable.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Target language for the auditable run.",
    )
    auditable.add_argument(
        "--near-dedup-threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Near-duplicate threshold in [0, 1].",
    )
    auditable.add_argument(
        "--output",
        default=None,
        help="Markdown output path or directory. Defaults to cwd.",
    )
    auditable.add_argument("--json", action="store_true", help="Print JSON output.")

    thread = subparsers.add_parser(
        "research-thread-to-draft",
        help="Promote a research thread into a draft, then optionally verify and download artifacts.",
    )
    thread.add_argument(
        "thread_id",
        help="Research thread id, e.g. research_thread:123 or 123.",
    )
    thread.add_argument(
        "--verify",
        action="store_true",
        help="Verify the created draft before downloading artifacts.",
    )
    thread.add_argument(
        "--download-markdown",
        action="store_true",
        help="Download the draft markdown after promotion.",
    )
    thread.add_argument(
        "--download-bundle",
        action="store_true",
        help="Download the draft export bundle after promotion.",
    )
    thread.add_argument(
        "--output-dir",
        default=None,
        help="Directory for any downloaded artifacts. Defaults to cwd.",
    )
    thread.add_argument("--json", action="store_true", help="Print JSON output.")

    return parser


def _run_status(args: argparse.Namespace) -> int:
    try:
        api_base = _normalize_api_base(args.api_base)
        resolved_password = _resolve_password(args.password)
        _validate_remote_config(api_base, resolved_password)
        health = _fetch_health(api_base, args.password)
        healthy = health.get("status") == "healthy" and "error" not in health
        payload = {
            "api_base": api_base,
            "healthy": healthy,
            "health": health,
            "auth_configured": bool(resolved_password),
            "entrypoints": {
                "operator": "provenote",
                "mcp": "provenote-mcp",
            },
            "inspect_surfaces": [
                "notebook",
                "draft",
                "research_thread",
                "auditable_run",
            ],
            "operator_workflows": [
                "research-thread-to-draft",
                "auditable-markdown",
            ],
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_status(payload)
    if args.require_healthy and not payload["healthy"]:
        return 1
    return 0


def _run_inspect_notebook(args: argparse.Namespace) -> int:
    try:
        client = _build_client(_normalize_api_base(args.api_base), args.password)
        notebook_id = _normalize_prefixed_id(args.notebook_id, "notebook")
        payload: dict[str, Any] = {
            "notebook": client.get_notebook(notebook_id),
            "drafts": client.get_drafts(notebook_id),
            "research_threads": client.get_research_threads(notebook_id),
        }
        if args.source_id:
            source_id = _normalize_prefixed_id(args.source_id, "source")
            payload["auditable_runs"] = client.get_auditable_runs(source_id)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_json(payload)
    return 0


def _run_inspect_draft(args: argparse.Namespace) -> int:
    try:
        client = _build_client(_normalize_api_base(args.api_base), args.password)
        draft_id = _normalize_prefixed_id(args.draft_id, "draft")
        payload = {
            "object_type": "draft",
            "object_id": draft_id,
            "payload": client.get_draft(draft_id),
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_inspection(payload)
    return 0


def _run_inspect_research_thread(args: argparse.Namespace) -> int:
    try:
        client = _build_client(_normalize_api_base(args.api_base), args.password)
        thread_id = _normalize_prefixed_id(args.thread_id, "research_thread")
        payload = {
            "object_type": "research_thread",
            "object_id": thread_id,
            "payload": client.get_research_thread(thread_id),
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_inspection(payload)
    return 0


def _run_inspect_auditable_run(args: argparse.Namespace) -> int:
    try:
        client = _build_client(_normalize_api_base(args.api_base), args.password)
        run_id = _normalize_prefixed_id(args.run_id, "auditable_run")
        payload = {
            "object_type": "auditable_run",
            "object_id": run_id,
            "payload": client.get_auditable_run(run_id),
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_inspection(payload)
    return 0


def _run_auditable_markdown(args: argparse.Namespace) -> int:
    if not 0.0 <= args.near_dedup_threshold <= 1.0:
        print("Error: --near-dedup-threshold must be in [0, 1].", file=sys.stderr)
        return 2

    client = _build_client(_normalize_api_base(args.api_base), args.password)
    source_id = _normalize_prefixed_id(args.source_id, "source")

    try:
        run_payload = _coerce_result(
            client.create_auditable_run(
                source_id,
                model_id=args.model_id,
                language=args.language,
                near_dedup_threshold=args.near_dedup_threshold,
            )
        )
        run_id = str(run_payload["id"])
        markdown = client.get_auditable_run_markdown(run_id)
        output_path = _build_text_output_path(run_id, args.output)
        saved_markdown = _write_text_file(output_path, markdown)
        payload = {
            "source_id": source_id,
            "run": run_payload,
            "saved_markdown": saved_markdown,
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_auditable_markdown(payload)
    return 0


def _run_research_thread_to_draft(args: argparse.Namespace) -> int:
    client = _build_client(_normalize_api_base(args.api_base), args.password)
    thread_id = _normalize_prefixed_id(args.thread_id, "research_thread")

    try:
        draft_payload = _coerce_result(client.create_draft_from_thread(thread_id))
        draft_id = str(draft_payload["id"])
        verified_payload = None
        if args.verify:
            verified_payload = _coerce_result(client.verify_draft(draft_id))

        saved_markdown = None
        if args.download_markdown:
            markdown = client.get_draft_markdown(draft_id)
            markdown_path = _build_named_output_path(
                f"draft-{draft_id.replace(':', '_')}.md",
                args.output_dir,
            )
            saved_markdown = _write_text_file(markdown_path, markdown)

        saved_bundle = None
        if args.download_bundle:
            bundle_name, bundle_payload = client.get_draft_bundle(draft_id)
            resolved_name = bundle_name or f"draft-{draft_id.replace(':', '_')}.zip"
            bundle_path = _build_named_output_path(resolved_name, args.output_dir)
            saved_bundle = _write_binary_file(bundle_path, bundle_payload)

        payload = {
            "thread_id": thread_id,
            "draft": draft_payload,
            "verified": verified_payload is not None,
            "verified_payload": verified_payload,
            "saved_markdown": saved_markdown,
            "saved_bundle": saved_bundle,
        }
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(payload)
    else:
        _print_thread_to_draft(payload)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "status":
        return _run_status(args)
    if args.command == "inspect":
        return args.handler(args)
    if args.command == "auditable-markdown":
        return _run_auditable_markdown(args)
    if args.command == "research-thread-to-draft":
        return _run_research_thread_to_draft(args)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
