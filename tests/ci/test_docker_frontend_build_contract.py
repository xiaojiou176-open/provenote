from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "ops" / "docker" / "Dockerfile"
DOCKERFILE_SINGLE = REPO_ROOT / "ops" / "docker" / "Dockerfile.single"


def test_runtime_dockerfiles_copy_next_artifacts_from_app_local_dist_dir() -> None:
    expected_by_file = {
        DOCKERFILE: (
            "COPY --from=builder /app/apps/web/.runtime-cache/build/next/standalone /app/apps/web/",
            "COPY --from=builder /app/apps/web/.runtime-cache/build/next/static /app/apps/web/.runtime-cache/build/next/static",
        ),
        DOCKERFILE_SINGLE: (
            "COPY --from=apps-web-builder /app/apps/web/.runtime-cache/build/next/standalone /app/apps/web/",
            "COPY --from=apps-web-builder /app/apps/web/.runtime-cache/build/next/static /app/apps/web/.runtime-cache/build/next/static",
        ),
    }
    forbidden_by_file = {
        DOCKERFILE: (
            "COPY --from=builder /app/apps/web/.next/standalone /app/apps/web/",
            "COPY --from=builder /app/apps/web/.next/static /app/apps/web/.next/static",
        ),
        DOCKERFILE_SINGLE: (
            "COPY --from=apps-web-builder /app/apps/web/.next/standalone /app/apps/web/",
            "COPY --from=apps-web-builder /app/apps/web/.next/static /app/apps/web/.next/static",
        ),
    }

    for dockerfile_path, expected_tokens in expected_by_file.items():
        source = dockerfile_path.read_text(encoding="utf-8")
        for token in expected_tokens:
            assert token in source, f"{dockerfile_path.name} must include `{token}`"
        for token in forbidden_by_file[dockerfile_path]:
            assert token not in source, (
                f"{dockerfile_path.name} must not include `{token}`"
            )
