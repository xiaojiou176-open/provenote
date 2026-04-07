import asyncio
import hashlib
import json
import weakref
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from surreal_commands import get_command_status, submit_command

from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.observability.logger import logger


class CommandNotFoundError(ValueError):
    """Raised when command or dead-letter entry does not exist."""


class CommandConflictError(ValueError):
    """Raised when command operation violates lifecycle constraints."""


RETRY_POLICY_TRANSACTIONAL: Dict[str, Any] = {
    "max_attempts": 5,
    "wait_strategy": "exponential_jitter",
    "wait_min": 1,
    "wait_max": 60,
    "stop_on": [],
    "retry_log_level": "debug",
}
RETRY_POLICY_DEEP_QUEUE: Dict[str, Any] = {
    "max_attempts": 15,
    "wait_strategy": "exponential_jitter",
    "wait_min": 1,
    "wait_max": 120,
    "stop_on": [],
    "retry_log_level": "debug",
}
RETRY_POLICY_SINGLE_ATTEMPT: Dict[str, Any] = {"max_attempts": 1}

CANCELLABLE_STATUSES = {"new", "queued", "pending"}
RUNNING_STATUSES = {"running"}
TERMINAL_STATUSES = {"completed", "failed", "canceled", "cancelled"}
_IDEMPOTENCY_LOCKS: weakref.WeakValueDictionary[str, asyncio.Lock] = (
    weakref.WeakValueDictionary()
)
_IDEMPOTENCY_LOCKS_GUARD = asyncio.Lock()
_DEAD_LETTER_LOCKS: weakref.WeakValueDictionary[str, asyncio.Lock] = (
    weakref.WeakValueDictionary()
)
_DEAD_LETTER_LOCKS_GUARD = asyncio.Lock()
IDEMPOTENCY_STATUS_PROCESSING = "processing"
IDEMPOTENCY_STATUS_SUBMITTED = "submitted"
IDEMPOTENCY_STATUS_FAILED = "failed"
IDEMPOTENCY_FAILED_RETRY_TTL_SECONDS = 300
_IDEMPOTENCY_SCHEMA_REPAIR_GUARD = asyncio.Lock()
_IDEMPOTENCY_SCHEMA_REPAIRED = False


def _stable_request_hash(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _idempotency_record_id(idempotency_key: str) -> str:
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"command_idempotency:{digest}"


def _dead_letter_record_id(command_id: str) -> str:
    digest = hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    return f"command_dead_letter:{digest}"


def _sanitize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(row)
    if result.get("id") is not None:
        result["id"] = str(result["id"])
    if result.get("command_id") is not None:
        result["command_id"] = str(result["command_id"])
    if result.get("last_requeued_command_id") is not None:
        result["last_requeued_command_id"] = str(result["last_requeued_command_id"])
    if result.get("status") is not None:
        result["status"] = _normalize_status(str(result["status"]))
    return result


def _normalize_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized == "cancelled":
        return "canceled"
    return normalized


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _is_idempotency_schema_field_error(error: Exception) -> bool:
    """Return True when idempotency writes fail on missing schema fields."""
    message = str(error).lower()
    if "status" not in message and "last_error" not in message:
        return False
    if "command_idempotency" in message:
        return True
    return "field" in message or "schema" in message


class CommandService:
    """Generic service layer for command operations."""

    @staticmethod
    async def _ensure_idempotency_schema_fields() -> None:
        """Repair legacy command_idempotency schema on already-migrated instances."""
        global _IDEMPOTENCY_SCHEMA_REPAIRED
        if _IDEMPOTENCY_SCHEMA_REPAIRED:
            return

        async with _IDEMPOTENCY_SCHEMA_REPAIR_GUARD:
            if _IDEMPOTENCY_SCHEMA_REPAIRED:
                return
            await repo_query(
                'DEFINE FIELD IF NOT EXISTS status ON command_idempotency TYPE string DEFAULT "processing"'
            )
            await repo_query(
                "DEFINE FIELD IF NOT EXISTS last_error ON command_idempotency TYPE option<string>"
            )
            _IDEMPOTENCY_SCHEMA_REPAIRED = True

    @staticmethod
    async def _run_idempotency_write_query(
        query: str,
        params: Dict[str, Any],
    ) -> Any:
        try:
            return await repo_query(query, params)
        except Exception as write_err:
            if not _is_idempotency_schema_field_error(write_err):
                raise
            logger.exception(
                "Detected command_idempotency write failure; attempting runtime schema repair."
            )
            logger.warning(
                "Detected legacy command_idempotency schema; applying runtime repair and retrying write."
            )
            await CommandService._ensure_idempotency_schema_fields()
            return await repo_query(query, params)

    @staticmethod
    async def _get_existing_idempotent_command(
        idempotency_key: str,
        request_hash: str,
    ) -> Optional[str]:
        record_id = _idempotency_record_id(idempotency_key)
        rows = await repo_query(
            "SELECT * FROM $record_id",
            {"record_id": ensure_record_id(record_id)},
        )
        if not rows:
            return None

        record = rows[0]
        stored_hash = str(record.get("request_hash", ""))
        if stored_hash and stored_hash != request_hash:
            raise CommandConflictError(
                "Idempotency key was already used with different payload."
            )

        existing_command_id = record.get("command_id")
        return str(existing_command_id) if existing_command_id else None

    @staticmethod
    async def _reserve_idempotency_placeholder(
        idempotency_key: str,
        request_hash: str,
        app_name: str,
        command_name: str,
    ) -> Optional[str]:
        record_id = _idempotency_record_id(idempotency_key)
        now = datetime.now(timezone.utc)
        placeholder_payload = {
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
            "app": app_name,
            "name": command_name,
            "status": IDEMPOTENCY_STATUS_PROCESSING,
            "command_id": None,
            "last_error": None,
            "created": now,
            "updated": now,
        }

        try:
            await CommandService._run_idempotency_write_query(
                f"CREATE {record_id} CONTENT $data",
                {"data": placeholder_payload},
            )
            return None
        except Exception as create_err:
            logger.exception(
                "Idempotency placeholder create failed; checking whether the placeholder already exists."
            )
            logger.debug(
                "Idempotency placeholder already exists key='{}': {}",
                idempotency_key,
                create_err,
            )

        rows = await repo_query(
            "SELECT * FROM $record_id",
            {"record_id": ensure_record_id(record_id)},
        )
        if not rows:
            raise CommandConflictError(
                "Idempotency placeholder state is unavailable; retry request."
            )

        record = rows[0]
        stored_hash = str(record.get("request_hash", ""))
        if stored_hash and stored_hash != request_hash:
            raise CommandConflictError(
                "Idempotency key was already used with different payload."
            )

        existing_command_id = record.get("command_id")
        if existing_command_id:
            return str(existing_command_id)

        existing_status = _normalize_status(
            str(record.get("status", IDEMPOTENCY_STATUS_PROCESSING))
        )
        if existing_status == IDEMPOTENCY_STATUS_PROCESSING:
            raise CommandConflictError(
                "Idempotency key is currently being processed; retry later."
            )
        if existing_status == IDEMPOTENCY_STATUS_FAILED:
            now = datetime.now(timezone.utc)
            failed_at = _parse_datetime(record.get("updated")) or _parse_datetime(
                record.get("created")
            )
            if not failed_at:
                raise CommandConflictError(
                    "Idempotency key is cooling down after failure; retry later."
                )

            cooldown_remaining = (
                failed_at + timedelta(seconds=IDEMPOTENCY_FAILED_RETRY_TTL_SECONDS)
            ) - now
            if cooldown_remaining.total_seconds() > 0:
                raise CommandConflictError(
                    "Idempotency key is cooling down after failure; retry later."
                )

            reclaimed_rows = await CommandService._run_idempotency_write_query(
                "UPDATE $record_id MERGE $data "
                "WHERE string::lowercase(status) = $failed_status "
                "AND command_id = NONE "
                "AND request_hash = $request_hash "
                "RETURN AFTER",
                {
                    "record_id": ensure_record_id(record_id),
                    "failed_status": IDEMPOTENCY_STATUS_FAILED,
                    "request_hash": request_hash,
                    "data": {
                        "status": IDEMPOTENCY_STATUS_PROCESSING,
                        "command_id": None,
                        "last_error": None,
                        "updated": now,
                    },
                },
            )
            if reclaimed_rows:
                return None

            refreshed_rows = await repo_query(
                "SELECT * FROM $record_id",
                {"record_id": ensure_record_id(record_id)},
            )
            if refreshed_rows:
                refreshed_command_id = refreshed_rows[0].get("command_id")
                if refreshed_command_id:
                    return str(refreshed_command_id)
                refreshed_status = _normalize_status(
                    str(refreshed_rows[0].get("status", ""))
                )
                if refreshed_status == IDEMPOTENCY_STATUS_PROCESSING:
                    raise CommandConflictError(
                        "Idempotency key is currently being processed; retry later."
                    )
            raise CommandConflictError(
                "Idempotency key is cooling down after failure; retry later."
            )
        raise CommandConflictError(
            "Idempotency key is in invalid state without a command result."
        )

    @staticmethod
    async def _store_idempotency_mapping(
        idempotency_key: str,
        request_hash: str,
        app_name: str,
        command_name: str,
        command_id: str,
    ) -> None:
        record_id = _idempotency_record_id(idempotency_key)
        now = datetime.now(timezone.utc)
        await CommandService._run_idempotency_write_query(
            f"UPSERT {record_id} MERGE $data",
            {
                "data": {
                    "idempotency_key": idempotency_key,
                    "request_hash": request_hash,
                    "app": app_name,
                    "name": command_name,
                    "status": IDEMPOTENCY_STATUS_SUBMITTED,
                    "command_id": ensure_record_id(command_id),
                    "last_error": None,
                    "updated": now,
                }
            },
        )

    @staticmethod
    async def _mark_idempotency_failure(
        idempotency_key: str,
        error_message: str,
    ) -> None:
        record_id = _idempotency_record_id(idempotency_key)
        await CommandService._run_idempotency_write_query(
            "UPDATE $record_id MERGE $data",
            {
                "record_id": ensure_record_id(record_id),
                "data": {
                    "status": IDEMPOTENCY_STATUS_FAILED,
                    "last_error": error_message[:1024],
                    "updated": datetime.now(timezone.utc),
                },
            },
        )

    @staticmethod
    async def _get_idempotency_lock(idempotency_key: str) -> asyncio.Lock:
        async with _IDEMPOTENCY_LOCKS_GUARD:
            lock = _IDEMPOTENCY_LOCKS.get(idempotency_key)
            if lock is None:
                lock = asyncio.Lock()
                _IDEMPOTENCY_LOCKS[idempotency_key] = lock
            return lock

    @staticmethod
    async def _get_dead_letter_lock(entry_id: str) -> asyncio.Lock:
        async with _DEAD_LETTER_LOCKS_GUARD:
            lock = _DEAD_LETTER_LOCKS.get(entry_id)
            if lock is None:
                lock = asyncio.Lock()
                _DEAD_LETTER_LOCKS[entry_id] = lock
            return lock

    @staticmethod
    async def _submit_command_job_impl(
        module_name: str,
        command_name: str,
        command_args: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        idempotency_key: Optional[str],
    ) -> str:
        owns_idempotency_placeholder = False
        request_hash = _stable_request_hash(
            {
                "app": module_name,
                "command": command_name,
                "args": command_args,
                "context": context or {},
            }
        )
        if idempotency_key:
            existing_command_id = await CommandService._get_existing_idempotent_command(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
            )
            if existing_command_id:
                logger.info(
                    "Idempotency hit key='{}' returning existing job={}",
                    idempotency_key,
                    existing_command_id,
                )
                return existing_command_id
            placeholder_command_id = (
                await CommandService._reserve_idempotency_placeholder(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    app_name=module_name,
                    command_name=command_name,
                )
            )
            if placeholder_command_id:
                logger.info(
                    "Idempotency replay key='{}' returning reserved job={}",
                    idempotency_key,
                    placeholder_command_id,
                )
                return placeholder_command_id
            owns_idempotency_placeholder = True

        try:
            cmd_id = submit_command(
                module_name,
                command_name,
                command_args,
                context=context,
            )
            if not cmd_id:
                raise ValueError("Failed to get cmd_id from submit_command")

            cmd_id_str = str(cmd_id)
            logger.info(
                f"Submitted command job: {cmd_id_str} for {module_name}.{command_name}"
            )
            if idempotency_key:
                await CommandService._store_idempotency_mapping(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    app_name=module_name,
                    command_name=command_name,
                    command_id=cmd_id_str,
                )
            return cmd_id_str
        except Exception as submit_err:
            if idempotency_key and owns_idempotency_placeholder:
                try:
                    await CommandService._mark_idempotency_failure(
                        idempotency_key=idempotency_key,
                        error_message=str(submit_err),
                    )
                except Exception as mark_err:
                    logger.exception(
                        "Failed to mark idempotency placeholder as failed after submit error."
                    )
                    logger.error(
                        "Failed to mark idempotency placeholder as failed for key='{}': {}",
                        idempotency_key,
                        mark_err,
                    )
            raise

    @staticmethod
    async def submit_command_job(
        module_name: str,  # Actually app_name for surreal-commands
        command_name: str,
        command_args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Submit a generic command job for background processing."""
        try:
            # Ensure command modules are imported before submitting.
            try:
                import packages.core.application.commands.embedding_commands  # noqa: F401
                import packages.core.application.commands.podcast_commands  # noqa: F401
                import packages.core.application.commands.source_commands  # noqa: F401
            except ImportError as import_err:
                logger.error(f"Failed to import command modules: {import_err}")
                raise ValueError("Command modules not available") from import_err

            if idempotency_key:
                lock = await CommandService._get_idempotency_lock(idempotency_key)
                async with lock:
                    return await CommandService._submit_command_job_impl(
                        module_name=module_name,
                        command_name=command_name,
                        command_args=command_args,
                        context=context,
                        idempotency_key=idempotency_key,
                    )
            return await CommandService._submit_command_job_impl(
                module_name=module_name,
                command_name=command_name,
                command_args=command_args,
                context=context,
                idempotency_key=None,
            )
        except Exception as e:
            logger.exception("Failed to submit command job with stack evidence.")
            logger.error(f"Failed to submit command job: {e}")
            raise

    @staticmethod
    async def _upsert_dead_letter_from_failure(
        *,
        command_id: str,
        app: Optional[str],
        name: Optional[str],
        args: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        error_message: str,
        command_updated: Optional[datetime],
    ) -> None:
        dead_letter_id = _dead_letter_record_id(command_id)
        existing = await repo_query(
            "SELECT * FROM $record_id",
            {"record_id": ensure_record_id(dead_letter_id)},
        )

        now = datetime.now(timezone.utc)
        first_row = existing[0] if existing else None
        previous_row = first_row if isinstance(first_row, dict) else None
        previous_failures = (
            int(previous_row.get("failure_count", 0)) if previous_row else 0
        )
        previous_last_failed = _parse_datetime(
            previous_row.get("last_failed_at") if previous_row else None
        )

        should_increment = True
        if previous_row and command_updated and previous_last_failed:
            # Avoid re-counting the same failed state when status/list endpoints are polled.
            should_increment = previous_last_failed < command_updated

        payload = {
            "command_id": ensure_record_id(command_id),
            "app": app or "",
            "name": name or "",
            "args": args or {},
            "context": context or {},
            "error_message": error_message,
            "status": "failed",
            "failure_count": previous_failures + 1
            if should_increment
            else previous_failures,
            "first_failed_at": previous_row.get("first_failed_at")
            if previous_row
            else now,
            "last_failed_at": (
                now
                if should_increment
                else (previous_row.get("last_failed_at") if previous_row else None)
            ),
            "requeue_count": int(previous_row.get("requeue_count", 0))
            if previous_row
            else 0,
            "last_requeued_command_id": previous_row.get("last_requeued_command_id")
            if previous_row
            else None,
            "last_requeued_at": previous_row.get("last_requeued_at")
            if previous_row
            else None,
            "updated": now,
            "created": previous_row.get("created") if previous_row else now,
        }
        await repo_query(f"UPSERT {dead_letter_id} MERGE $data", {"data": payload})

    @staticmethod
    async def _sync_dead_letter_if_failed(command_row: Dict[str, Any]) -> None:
        status = _normalize_status(str(command_row.get("status", "")))
        if status != "failed":
            return

        command_id = str(command_row.get("id", ""))
        if not command_id:
            return

        await CommandService._upsert_dead_letter_from_failure(
            command_id=command_id,
            app=str(command_row.get("app") or ""),
            name=str(command_row.get("name") or ""),
            args=command_row.get("args", {}) or {},
            context=command_row.get("context", {}) or {},
            error_message=str(command_row.get("error_message", "") or ""),
            command_updated=_parse_datetime(command_row.get("updated")),
        )

    @staticmethod
    async def record_command_failure_event(
        command_id: str,
        *,
        error_message: str,
        app: Optional[str] = None,
        name: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        row: Dict[str, Any] = {}
        if not app or not name:
            rows = await repo_query(
                "SELECT id, app, name, args, context, updated, error_message FROM $command_id",
                {"command_id": ensure_record_id(command_id)},
            )
            if rows:
                row = rows[0]

        await CommandService._upsert_dead_letter_from_failure(
            command_id=command_id,
            app=app or str(row.get("app", "") or ""),
            name=name or str(row.get("name", "") or ""),
            args=args if args is not None else (row.get("args", {}) or {}),
            context=context if context is not None else (row.get("context", {}) or {}),
            error_message=error_message or str(row.get("error_message", "") or ""),
            command_updated=_parse_datetime(row.get("updated")),
        )

    @staticmethod
    async def get_command_status(job_id: str) -> Dict[str, Any]:
        """Get status of any command job."""
        try:
            status = await get_command_status(job_id)
            if status and _normalize_status(str(status.status)) == "failed":
                await CommandService.record_command_failure_event(
                    job_id,
                    error_message=str(getattr(status, "error_message", "") or ""),
                )
            return {
                "job_id": job_id,
                "status": _normalize_status(str(status.status))
                if status
                else "unknown",
                "result": status.result if status else None,
                "error_message": getattr(status, "error_message", None)
                if status
                else None,
                "created": str(status.created)
                if status and hasattr(status, "created") and status.created
                else None,
                "updated": str(status.updated)
                if status and hasattr(status, "updated") and status.updated
                else None,
                "progress": getattr(status, "progress", None) if status else None,
            }
        except Exception as e:
            logger.exception("Failed to get command status with stack evidence.")
            logger.error(f"Failed to get command status: {e}")
            raise

    @staticmethod
    async def list_command_jobs(
        module_filter: Optional[str] = None,
        command_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List command jobs with optional filtering."""
        filters: list[str] = []
        params: Dict[str, Any] = {
            "limit": max(1, min(limit, 200)),
            "offset": max(0, offset),
        }
        if module_filter:
            filters.append("string::lowercase(app) = string::lowercase($module_filter)")
            params["module_filter"] = module_filter
        if command_filter:
            filters.append(
                "string::lowercase(name) = string::lowercase($command_filter)"
            )
            params["command_filter"] = command_filter
        if status_filter:
            normalized_status_filter = _normalize_status(status_filter)
            if normalized_status_filter == "canceled":
                filters.append(
                    "(string::lowercase(status) = 'canceled' OR string::lowercase(status) = 'cancelled')"
                )
            else:
                filters.append(
                    "string::lowercase(status) = string::lowercase($status_filter)"
                )
                params["status_filter"] = normalized_status_filter

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = (
            "SELECT id, app, name, args, context, status, result, error_message, created, updated "
            f"FROM command {where_clause} ORDER BY created DESC LIMIT $limit START $offset"
        )
        rows = await repo_query(query, params)
        for row in rows:
            if _normalize_status(str(row.get("status", ""))) == "failed":
                await CommandService._sync_dead_letter_if_failed(row)
        return [_sanitize_row(row) for row in rows]

    @staticmethod
    async def cancel_command_job(job_id: str) -> Dict[str, Any]:
        """Cancel a queued command job with lifecycle-safe semantics."""
        try:
            rows = await repo_query(
                "SELECT id, status FROM $command_id",
                {"command_id": ensure_record_id(job_id)},
            )
            if not rows:
                raise CommandNotFoundError(f"Command not found: {job_id}")

            row = rows[0]
            current_status = _normalize_status(str(row.get("status", "")))
            if current_status in CANCELLABLE_STATUSES:
                updated_rows = await repo_query(
                    "UPDATE $command_id MERGE $data "
                    "WHERE string::lowercase(status) IN $cancellable_statuses "
                    "RETURN AFTER",
                    {
                        "command_id": ensure_record_id(job_id),
                        "cancellable_statuses": sorted(CANCELLABLE_STATUSES),
                        "data": {
                            "status": "canceled",
                            "error_message": "Cancelled by API request",
                            "updated": datetime.now(timezone.utc),
                        },
                    },
                )
                if updated_rows:
                    return {
                        "job_id": job_id,
                        "cancelled": True,
                        "status": "canceled",
                        "message": "Command cancelled before execution.",
                    }
                refreshed_rows = await repo_query(
                    "SELECT id, status FROM $command_id",
                    {"command_id": ensure_record_id(job_id)},
                )
                if not refreshed_rows:
                    raise CommandNotFoundError(f"Command not found: {job_id}")
                current_status = _normalize_status(
                    str(refreshed_rows[0].get("status", ""))
                )
            if current_status == "running":
                raise CommandConflictError(
                    "Command is already running and cannot be canceled safely."
                )

            return {
                "job_id": job_id,
                "cancelled": False,
                "status": current_status,
                "message": f"Command is already in terminal state '{current_status}'.",
            }
        except Exception as e:
            logger.exception("Failed to cancel command job with stack evidence.")
            logger.error(f"Failed to cancel command job: {e}")
            raise

    @staticmethod
    async def list_dead_letter_entries(
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List dead-lettered command entries."""
        rows = await repo_query(
            "SELECT * FROM command_dead_letter ORDER BY last_failed_at DESC LIMIT $limit START $offset",
            {"limit": max(1, min(limit, 200)), "offset": max(0, offset)},
        )
        result: list[Dict[str, Any]] = []
        for row in rows:
            entry = _sanitize_row(row)
            requeued_id = row.get("last_requeued_command_id")
            if not requeued_id:
                entry["last_requeued_status"] = None
            else:
                last_rows = await repo_query(
                    "SELECT status FROM $command_id",
                    {"command_id": ensure_record_id(requeued_id)},
                )
                entry["last_requeued_status"] = (
                    _normalize_status(str(last_rows[0].get("status", "")))
                    if last_rows
                    else "unknown"
                )
            result.append(entry)
        return result

    @staticmethod
    async def requeue_dead_letter(entry_id: str) -> Dict[str, Any]:
        """Requeue a dead-lettered command entry."""
        lock = await CommandService._get_dead_letter_lock(entry_id)
        async with lock:
            rows = await repo_query(
                "SELECT * FROM $entry_id",
                {"entry_id": ensure_record_id(entry_id)},
            )
            if not rows:
                raise CommandNotFoundError(f"Dead-letter entry not found: {entry_id}")

            entry = rows[0]
            app = str(entry.get("app", "")).strip()
            name = str(entry.get("name", "")).strip()
            args = entry.get("args", {}) or {}
            context = entry.get("context", {}) or {}

            if not app or not name:
                raise CommandConflictError(
                    "Dead-letter entry is missing app/name metadata."
                )

            last_requeued_command_id = entry.get("last_requeued_command_id")
            if last_requeued_command_id:
                prior_status_rows = await repo_query(
                    "SELECT status FROM $command_id",
                    {"command_id": ensure_record_id(last_requeued_command_id)},
                )
                if prior_status_rows:
                    prior_status = _normalize_status(
                        str(prior_status_rows[0].get("status", ""))
                    )
                    if prior_status in (CANCELLABLE_STATUSES | RUNNING_STATUSES):
                        raise CommandConflictError(
                            "Dead-letter entry already has an active requeued command."
                        )

            command_id = await CommandService.submit_command_job(
                module_name=app,
                command_name=name,
                command_args=args,
                context=context,
            )
            now = datetime.now(timezone.utc)
            await repo_query(
                "UPDATE $entry_id MERGE $data",
                {
                    "entry_id": ensure_record_id(entry_id),
                    "data": {
                        "status": "requeued",
                        "requeue_count": int(entry.get("requeue_count", 0)) + 1,
                        "last_requeued_command_id": ensure_record_id(command_id),
                        "last_requeued_at": now,
                        "updated": now,
                    },
                },
            )
            return {
                "entry_id": entry_id,
                "command_id": command_id,
                "message": "Dead-letter entry requeued successfully.",
            }
