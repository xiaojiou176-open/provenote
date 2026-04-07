from fastapi import APIRouter

from packages.core.application.models import (
    UITestReportResponse,
    UITestRunRequest,
    UITestRunResponse,
)
from packages.core.application.ui_test_service import ui_test_service
from packages.core.exceptions import RateLimitError
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()


@router.post("/ui-tests/run", response_model=UITestRunResponse)
@with_router_error_handling(
    log_template="Error starting UI test run",
    detail_template="Error starting UI test run",
    include_exception_detail=False,
    exception_status_map={RateLimitError: 429},
)
async def run_ui_test(request: UITestRunRequest):
    return await ui_test_service.run(request)


@router.get("/ui-tests/{run_id}", response_model=UITestRunResponse)
@with_router_error_handling(
    log_template="Error getting UI test run {run_id}",
    detail_template="Error fetching UI test run",
    include_exception_detail=False,
)
async def get_ui_test_run(run_id: str):
    return await ui_test_service.get(run_id)


@router.get("/ui-tests/{run_id}/report", response_model=UITestReportResponse)
@with_router_error_handling(
    log_template="Error getting UI test report {run_id}",
    detail_template="Error fetching UI test report",
    include_exception_detail=False,
)
async def get_ui_test_report(run_id: str):
    return await ui_test_service.report(run_id)
