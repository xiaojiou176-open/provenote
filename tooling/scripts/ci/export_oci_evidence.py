#!/usr/bin/env python3
"""Export raw OCI release evidence from GHCR for release-proof consumption."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        required=True,
        help="Container repository path without registry host, e.g. lfnovo/open-notebook.",
    )
    parser.add_argument(
        "--subject-digest",
        required=True,
        help="Published image index or manifest digest, e.g. sha256:...",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Short label used in exported filenames, e.g. regular or single.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory that will receive raw OCI evidence files.",
    )
    return parser.parse_args()


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"expected JSON object from {url}")
    return parsed


def _http_get_bytes(url: str, headers: dict[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return response.read()


def _is_retryable_registry_error(exc: urllib.error.HTTPError) -> bool:
    return exc.code in {404, 408, 429, 500, 502, 503, 504}


def _retry_with_backoff(fetcher, *, description: str, attempts: int = 14):
    delay_seconds = 2.0
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetcher()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if attempt == attempts or not _is_retryable_registry_error(exc):
                raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == attempts:
                raise
        print(
            f"INFO: retrying {description} after transient registry delay (attempt {attempt}/{attempts})",
            file=sys.stderr,
        )
        time.sleep(delay_seconds)
        # Fresh GHCR digests can stay temporarily unreadable even after the
        # publish step reports success, so keep a wider backoff window here.
        delay_seconds = min(delay_seconds * 2, 64.0)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"retry loop for {description} exited unexpectedly")


def _resolve_registry_credentials(
    env: Mapping[str, str] | None = None,
) -> tuple[str, str] | None:
    source_env = os.environ if env is None else env
    username = (
        source_env.get("GHCR_USERNAME") or source_env.get("GITHUB_ACTOR") or ""
    ).strip()
    token = (
        source_env.get("GHCR_TOKEN") or source_env.get("GITHUB_TOKEN") or ""
    ).strip()
    if not username or not token:
        return None
    return username, token


def _build_token_headers(credentials: tuple[str, str] | None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if credentials is None:
        return headers

    username, token = credentials
    basic_auth = base64.b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    return {**headers, "Authorization": f"Basic {basic_auth}"}


def _ghcr_token_request_headers() -> dict[str, str]:
    return _build_token_headers(_resolve_registry_credentials())


def _get_ghcr_token(repository: str, credentials: tuple[str, str] | None = None) -> str:
    token_url = "https://ghcr.io/token?service=ghcr.io&scope=" + urllib.parse.quote(
        f"repository:{repository}:pull", safe=":/"
    )
    payload = _http_get_json(token_url, headers=_build_token_headers(credentials))
    token = payload.get("token")
    if not isinstance(token, str) or not token.strip():
        raise RuntimeError("failed to obtain GHCR pull token")
    return token.strip()


def _slugify(raw: str) -> str:
    pieces: list[str] = []
    for char in raw.lower():
        if char.isalnum():
            pieces.append(char)
        else:
            pieces.append("-")
    collapsed = "".join(pieces).strip("-")
    while "--" in collapsed:
        collapsed = collapsed.replace("--", "-")
    return collapsed or "unknown"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _export_subject_manifest(
    repository: str, subject_digest: str, headers: dict[str, str]
) -> dict[str, object]:
    manifest_url = f"https://ghcr.io/v2/{repository}/manifests/{subject_digest}"
    request_headers = {
        **headers,
        "Accept": (
            "application/vnd.oci.image.index.v1+json, "
            "application/vnd.oci.image.manifest.v1+json, "
            "application/json"
        ),
    }
    return _retry_with_backoff(
        lambda: _http_get_json(manifest_url, headers=request_headers),
        description=f"subject manifest {subject_digest}",
    )


def _platform_map(subject_manifest: dict[str, object]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    manifests = subject_manifest.get("manifests")
    if not isinstance(manifests, list):
        return mapping
    for entry in manifests:
        if not isinstance(entry, dict):
            continue
        digest = entry.get("digest")
        platform = entry.get("platform")
        if not isinstance(digest, str) or not isinstance(platform, dict):
            continue
        arch = str(platform.get("architecture", "unknown"))
        os_name = str(platform.get("os", "unknown"))
        mapping[digest] = f"{os_name}-{arch}"
    return mapping


def _classify_blob_kind(layer: dict[str, object]) -> str:
    annotations = layer.get("annotations")
    predicate = ""
    if isinstance(annotations, dict):
        raw_predicate = annotations.get("in-toto.io/predicate-type")
        if isinstance(raw_predicate, str):
            predicate = raw_predicate.lower()

    media_type = str(layer.get("mediaType", "")).lower()
    if "spdx" in predicate or "cyclonedx" in predicate or "sbom" in predicate:
        return "sbom"
    if "provenance" in predicate or "slsa" in predicate:
        return "provenance"
    if "spdx" in media_type or "cyclonedx" in media_type:
        return "sbom"
    return "attestation"


def _export_attestations(
    repository: str,
    label: str,
    output_dir: Path,
    subject_manifest: dict[str, object],
    headers: dict[str, str],
) -> dict[str, object]:
    platform_by_digest = _platform_map(subject_manifest)
    exported: list[dict[str, str]] = []

    manifests = subject_manifest.get("manifests")
    if not isinstance(manifests, list):
        return {"exported_files": exported}

    for entry in manifests:
        if not isinstance(entry, dict):
            continue
        annotations = entry.get("annotations")
        if not isinstance(annotations, dict):
            continue
        if annotations.get("vnd.docker.reference.type") != "attestation-manifest":
            continue

        attestation_digest = entry.get("digest")
        subject_digest = annotations.get("vnd.docker.reference.digest")
        if not isinstance(attestation_digest, str) or not isinstance(
            subject_digest, str
        ):
            continue

        platform_slug = _slugify(
            platform_by_digest.get(subject_digest, "unknown-unknown")
        )
        manifest_url = f"https://ghcr.io/v2/{repository}/manifests/{attestation_digest}"
        manifest_payload = _retry_with_backoff(
            lambda: _http_get_json(
                manifest_url,
                headers={
                    **headers,
                    "Accept": "application/vnd.oci.image.manifest.v1+json, application/json",
                },
            ),
            description=f"attestation manifest {attestation_digest}",
        )

        manifest_path = (
            output_dir / f"{label}-{platform_slug}-attestation-manifest.json"
        )
        _write_json(manifest_path, manifest_payload)
        exported.append(
            {
                "kind": "attestation-manifest",
                "path": str(manifest_path),
                "digest": attestation_digest,
                "subject_digest": subject_digest,
            }
        )

        layers = manifest_payload.get("layers")
        if not isinstance(layers, list):
            continue

        for index, layer in enumerate(layers, start=1):
            if not isinstance(layer, dict):
                continue
            blob_digest = layer.get("digest")
            if not isinstance(blob_digest, str):
                continue
            blob_kind = _classify_blob_kind(layer)
            blob_url = f"https://ghcr.io/v2/{repository}/blobs/{blob_digest}"
            blob_bytes = _retry_with_backoff(
                lambda: _http_get_bytes(blob_url, headers=headers),
                description=f"{blob_kind} blob {blob_digest}",
            )
            blob_path = output_dir / f"{label}-{platform_slug}-{blob_kind}-{index}.json"
            try:
                blob_payload = json.loads(blob_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                _write_bytes(blob_path, blob_bytes)
            else:
                _write_json(blob_path, blob_payload)

            exported.append(
                {
                    "kind": blob_kind,
                    "path": str(blob_path),
                    "digest": blob_digest,
                    "subject_digest": subject_digest,
                }
            )

    return {"exported_files": exported}


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    registry_credentials = _resolve_registry_credentials()
    try:
        token = _get_ghcr_token(args.repository, credentials=registry_credentials)
    except urllib.error.HTTPError as exc:
        auth_mode = "authenticated" if registry_credentials is not None else "anonymous"
        print(
            f"FAIL: unable to obtain GHCR pull token for ghcr.io/{args.repository} using {auth_mode} access: {exc}",
            file=sys.stderr,
        )
        return 1
    headers = {"Authorization": f"Bearer {token}"}

    try:
        subject_manifest = _export_subject_manifest(
            args.repository, args.subject_digest, headers
        )
    except urllib.error.HTTPError as exc:
        print(
            f"FAIL: unable to fetch subject manifest {args.subject_digest} from ghcr.io/{args.repository}: {exc}",
            file=sys.stderr,
        )
        return 1

    subject_media_type = str(subject_manifest.get("mediaType", ""))
    subject_kind = (
        "image-index"
        if subject_media_type == "application/vnd.oci.image.index.v1+json"
        else "image-manifest"
    )
    subject_path = output_dir / f"{args.label}-{subject_kind}.json"
    _write_json(subject_path, subject_manifest)

    attestation_export = _export_attestations(
        repository=args.repository,
        label=args.label,
        output_dir=output_dir,
        subject_manifest=subject_manifest,
        headers=headers,
    )

    export_manifest = {
        "repository": args.repository,
        "label": args.label,
        "subject_digest": args.subject_digest,
        "subject_media_type": subject_media_type,
        "subject_file": str(subject_path),
        **attestation_export,
    }
    _write_json(output_dir / f"{args.label}-export-index.json", export_manifest)

    exported_files = attestation_export["exported_files"]
    if not isinstance(exported_files, list) or not exported_files:
        print(
            f"FAIL: no attestation manifests were discovered for {args.subject_digest}",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS: exported raw OCI evidence for {args.label} from ghcr.io/{args.repository} into {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
