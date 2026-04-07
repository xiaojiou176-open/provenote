from __future__ import annotations

import importlib.util
import sys
import textwrap
import tomllib
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_coverage_thresholds.py"
)
PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"
SPEC = importlib.util.spec_from_file_location("check_coverage_thresholds", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


def test_parse_frontend_lcov_collects_line_and_branch_coverage(tmp_path: Path) -> None:
    lcov_path = tmp_path / "lcov.info"
    lcov_path.write_text(
        "\n".join(
            [
                "SF:/tmp/repo/apps/web/src/lib/api/client.ts",
                "DA:1,1",
                "DA:2,0",
                "BRDA:1,0,0,1",
                "BRDA:1,0,1,0",
                "end_of_record",
            ]
        ),
        encoding="utf-8",
    )

    result = GUARD._parse_frontend_lcov(lcov_path)

    assert result.global_line_rate == 50.0
    assert result.global_branch_rate == 50.0
    assert result.per_file_line_rate["src/lib/api/client.ts"] == 50.0
    assert result.per_file_branch_rate["src/lib/api/client.ts"] == 50.0


def test_check_thresholds_reports_low_branch_and_missing_modules() -> None:
    result = GUARD.CoverageResult(
        global_line_rate=82.0,
        global_branch_rate=70.0,
        per_file_line_rate={"src/lib/api/client.ts": 96.0},
        per_file_branch_rate={"src/lib/api/client.ts": 79.0},
    )

    errors = GUARD._check_thresholds(
        result,
        label="apps/web",
        global_min=95.0,
        key_modules={
            "src/lib/api/client.ts": 95.0,
            "src/lib/utils/error-handler.ts": 95.0,
        },
    )

    assert any(
        "key module src/lib/api/client.ts branch coverage 79.00% is below 95.00%"
        in item
        for item in errors
    )
    assert any(
        "key module missing from coverage report: src/lib/utils/error-handler.ts"
        in item
        for item in errors
    )


def test_resolve_backend_key_modules_accepts_phase1() -> None:
    modules = GUARD._resolve_backend_key_modules("phase1")
    assert "services/api/routers/auditable_runs.py" in modules
    assert "services/api/auth.py" in modules


def test_parse_backend_coverage_xml_normalizes_absolute_paths(tmp_path: Path) -> None:
    xml_path = tmp_path / ".runtime-cache/test/coverage/backend/coverage.xml"
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(
        textwrap.dedent(
            """\
            <coverage line-rate="0.98" branch-rate="0.97">
              <packages>
                <package name="services.api.routers">
                  <classes>
                    <class filename="/tmp/workspace/api/routers/auditable_runs.py" line-rate="1.0" branch-rate="0.99" />
                  </classes>
                </package>
                <package name="packages.core.auditable">
                  <classes>
                    <class filename="/tmp/workspace/packages/core/auditable/pipeline.py" line-rate="0.97" branch-rate="0.96" />
                  </classes>
                </package>
              </packages>
            </coverage>
            """
        ),
        encoding="utf-8",
    )

    result = GUARD._parse_backend_coverage_xml(xml_path)

    assert result.global_line_rate == 98.0
    assert result.global_branch_rate == 97.0
    assert result.per_file_line_rate["services/api/routers/auditable_runs.py"] == 100.0
    assert result.per_file_branch_rate["services/api/routers/auditable_runs.py"] == 99.0
    assert result.per_file_line_rate["packages/core/auditable/pipeline.py"] == 97.0
    assert result.per_file_branch_rate["packages/core/auditable/pipeline.py"] == 96.0


def test_pyproject_coverage_fail_under_is_95_percent() -> None:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    assert data["tool"]["coverage"]["report"]["fail_under"] == 95


def test_global_thresholds_are_95_percent() -> None:
    assert GUARD.BACKEND_GLOBAL_MIN == 95.0
    assert GUARD.FRONTEND_GLOBAL_MIN == 95.0


def test_build_arg_parser_uses_safe_dest_names_for_frontend_flags() -> None:
    parser = GUARD.build_arg_parser()
    args = parser.parse_args([])

    assert args.frontend_lcov == ".runtime-cache/test/coverage/apps/web/lcov.info"
    assert args.skip_frontend is False
