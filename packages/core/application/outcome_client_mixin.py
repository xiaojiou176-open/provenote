"""Outcome-oriented API client mixin for drafts, research threads, and auditable runs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Union


class _OutcomeRequestClient(Protocol):
    def _make_request(
        self, method: str, endpoint: str, timeout: Optional[float] = None, **kwargs: Any
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]: ...

    def _make_text_request(
        self, method: str, endpoint: str, timeout: Optional[float] = None, **kwargs: Any
    ) -> str: ...

    def _make_binary_request(
        self, method: str, endpoint: str, timeout: Optional[float] = None, **kwargs: Any
    ) -> tuple[Optional[str], bytes]: ...


class OutcomeAPIClientMixin:
    """Provide outcome-lane API helpers on top of the base API client transport methods."""

    def get_drafts(
        self: _OutcomeRequestClient, notebook_id: str
    ) -> List[Dict[Any, Any]]:
        """Get drafts for a notebook."""
        result = self._make_request("GET", f"/api/notebooks/{notebook_id}/drafts")
        return result if isinstance(result, list) else [result]

    def create_draft(
        self: _OutcomeRequestClient,
        notebook_id: str,
        source_ids: List[str],
        note_ids: Optional[List[str]] = None,
        thread_ids: Optional[List[str]] = None,
        title: Optional[str] = None,
        model_id: Optional[str] = None,
        language: Optional[str] = None,
        near_dedup_threshold: Optional[float] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Create a notebook draft."""
        data: Dict[str, Any] = {"source_ids": source_ids}
        if note_ids is not None:
            data["note_ids"] = note_ids
        if thread_ids is not None:
            data["thread_ids"] = thread_ids
        if title is not None:
            data["title"] = title
        if model_id is not None:
            data["model_id"] = model_id
        if language is not None:
            data["language"] = language
        if near_dedup_threshold is not None:
            data["near_dedup_threshold"] = near_dedup_threshold
        return self._make_request(
            "POST", f"/api/notebooks/{notebook_id}/drafts", json=data
        )

    def verify_draft(
        self: _OutcomeRequestClient, draft_id: str
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Verify a draft."""
        return self._make_request("POST", f"/api/drafts/{draft_id}/verify")

    def get_draft_markdown(self: _OutcomeRequestClient, draft_id: str) -> str:
        """Get draft markdown as plain text."""
        return self._make_text_request("GET", f"/api/drafts/{draft_id}/markdown")

    def get_draft(
        self: _OutcomeRequestClient, draft_id: str
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Get one draft payload."""
        return self._make_request("GET", f"/api/drafts/{draft_id}")

    def get_draft_bundle(
        self: _OutcomeRequestClient, draft_id: str
    ) -> tuple[Optional[str], bytes]:
        """Download the draft export bundle."""
        return self._make_binary_request("GET", f"/api/drafts/{draft_id}/bundle")

    def get_research_threads(
        self: _OutcomeRequestClient, notebook_id: str
    ) -> List[Dict[Any, Any]]:
        """Get research threads for a notebook."""
        result = self._make_request(
            "GET", f"/api/notebooks/{notebook_id}/research-threads"
        )
        return result if isinstance(result, list) else [result]

    def get_research_thread(
        self: _OutcomeRequestClient, thread_id: str
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Get one research thread payload."""
        return self._make_request("GET", f"/api/research-threads/{thread_id}")

    def create_research_thread(
        self: _OutcomeRequestClient,
        notebook_id: str,
        title: str,
        seed_kind: str,
        source_ids: Optional[List[str]] = None,
        note_ids: Optional[List[str]] = None,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        insight_id: Optional[str] = None,
        insight_type: Optional[str] = None,
        search_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Create a research thread."""
        data: Dict[str, Any] = {
            "title": title,
            "seed_kind": seed_kind,
            "source_ids": source_ids or [],
            "note_ids": note_ids or [],
            "search_results": search_results or [],
        }
        if question is not None:
            data["question"] = question
        if answer is not None:
            data["answer"] = answer
        if insight_id is not None:
            data["insight_id"] = insight_id
        if insight_type is not None:
            data["insight_type"] = insight_type
        return self._make_request(
            "POST", f"/api/notebooks/{notebook_id}/research-threads", json=data
        )

    def append_research_thread(
        self: _OutcomeRequestClient,
        thread_id: str,
        entry_type: str,
        content: str,
        title: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        note_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Append an entry to a research thread."""
        data: Dict[str, Any] = {
            "entry_type": entry_type,
            "content": content,
            "source_ids": source_ids or [],
            "note_ids": note_ids or [],
            "metadata": metadata or {},
        }
        if title is not None:
            data["title"] = title
        return self._make_request(
            "POST", f"/api/research-threads/{thread_id}/entries", json=data
        )

    def create_draft_from_thread(
        self: _OutcomeRequestClient, thread_id: str
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Create a draft from a research thread."""
        return self._make_request("POST", f"/api/research-threads/{thread_id}/drafts")

    def get_auditable_runs(
        self: _OutcomeRequestClient, source_id: str
    ) -> List[Dict[Any, Any]]:
        """Get auditable runs for a source."""
        result = self._make_request("GET", f"/api/sources/{source_id}/auditable-runs")
        return result if isinstance(result, list) else [result]

    def get_auditable_run(
        self: _OutcomeRequestClient, run_id: str
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Get one auditable run payload."""
        return self._make_request("GET", f"/api/auditable-runs/{run_id}")

    def create_auditable_run(
        self: _OutcomeRequestClient,
        source_id: str,
        model_id: Optional[str] = None,
        language: Optional[str] = None,
        near_dedup_threshold: Optional[float] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Create an auditable run for a source."""
        data: Dict[str, Any] = {}
        if model_id is not None:
            data["model_id"] = model_id
        if language is not None:
            data["language"] = language
        if near_dedup_threshold is not None:
            data["near_dedup_threshold"] = near_dedup_threshold
        return self._make_request(
            "POST", f"/api/sources/{source_id}/auditable-runs", json=data
        )

    def get_auditable_run_markdown(self: _OutcomeRequestClient, run_id: str) -> str:
        """Get auditable markdown as plain text."""
        return self._make_text_request("GET", f"/api/auditable-runs/{run_id}/markdown")

    def repair_auditable_claim(
        self: _OutcomeRequestClient,
        run_id: str,
        target_index: int,
        model_id: Optional[str] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Repair a claim in an auditable run."""
        data: Dict[str, Any] = {"target_index": target_index}
        if model_id is not None:
            data["model_id"] = model_id
        return self._make_request(
            "POST", f"/api/auditable-runs/{run_id}/repair-claim", json=data
        )

    def repair_auditable_section(
        self: _OutcomeRequestClient,
        run_id: str,
        target_index: int,
        model_id: Optional[str] = None,
    ) -> Union[Dict[Any, Any], List[Dict[Any, Any]]]:
        """Repair a section in an auditable run."""
        data: Dict[str, Any] = {"target_index": target_index}
        if model_id is not None:
            data["model_id"] = model_id
        return self._make_request(
            "POST", f"/api/auditable-runs/{run_id}/repair-section", json=data
        )
