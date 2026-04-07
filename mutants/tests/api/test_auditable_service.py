from services.api.auditable_service import AuditableService


def _base_record() -> dict:
    return {
        "id": "auditable_run:1",
        "source": "source:1",
        "status": "completed",
        "model_id": "gemini-3.1-pro-preview",
        "language": "zh-CN",
        "near_dedup_threshold": 0.97,
        "coverage_json": {
            "coverage_rate": 0.75,
            "missing_pids": ["P000003"],
            "duplicate_pids": ["P000002"],
            "unknown_pids": ["P999999"],
            "unclassified_pids": ["P000004"],
        },
        "dedup_json": {"group_count": 2},
        "result_markdown": "# markdown",
        "source_paragraphs": [],
        "sections": [],
        "claims": [],
        "dedup_entries": [],
        "created": "2026-01-01T00:00:00+00:00",
        "updated": "2026-01-01T00:00:00+00:00",
    }


def test_to_response_falls_back_when_metrics_is_empty_dict():
    record = _base_record()
    record["metrics"] = {}

    response = AuditableService._to_response(record)

    assert response.metrics.coverage_rate == 0.75
    assert response.metrics.missing_count == 1
    assert response.metrics.duplicate_count == 1
    assert response.metrics.unknown_pid_count == 1
    assert response.metrics.unclassified_count == 1
    assert response.metrics.dedup_group_count == 2


def test_to_response_falls_back_when_metrics_is_partial_dict():
    record = _base_record()
    record["metrics"] = {"coverage_rate": 0.99}

    response = AuditableService._to_response(record)

    assert response.metrics.coverage_rate == 0.75
    assert response.metrics.missing_count == 1
    assert response.metrics.dedup_group_count == 2
