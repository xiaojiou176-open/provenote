"""Run threshold checks for Ragas metrics.

The script supports two metric sources:
1. Inline metrics in config.yaml under `metrics`.
2. A JSON file path in config.yaml under `results_file`.

If any metric is missing or below threshold, the script exits with code 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _coerce_scalar(value: str) -> Any:
    raw = value.strip().strip('"').strip("'")
    lower = raw.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse a minimal YAML subset (top-level map + one nested map)."""
    parsed: dict[str, Any] = {}
    current_map: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if line.startswith((" ", "\t")):
            if current_map is None:
                continue
            item = line.strip()
            if ":" not in item:
                continue
            key, value = item.split(":", 1)
            container = parsed.setdefault(current_map, {})
            if isinstance(container, dict):
                container[key.strip()] = _coerce_scalar(value)
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            parsed[key] = {}
            current_map = key
        else:
            parsed[key] = _coerce_scalar(value)
            current_map = None

    return parsed


def _load_config(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")

    # JSON is valid YAML; support this path without extra dependencies.
    if content.lstrip().startswith("{"):
        loaded = json.loads(content)
        if isinstance(loaded, dict):
            return loaded
        raise ValueError("Config JSON must be an object")

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(content)
        if isinstance(loaded, dict):
            return loaded
        raise ValueError("Config YAML must be a mapping")
    except Exception:
        return _parse_simple_yaml(path)


def _normalize_metric_map(raw: Any, section_name: str) -> dict[str, float]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"`{section_name}` must be a mapping")

    normalized: dict[str, float] = {}
    for name, value in raw.items():
        try:
            normalized[str(name)] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"`{section_name}.{name}` must be numeric, got {value!r}"
            ) from exc
    return normalized


def _load_metrics_from_file(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, dict) and "metrics" in raw and isinstance(raw["metrics"], dict):
        return _normalize_metric_map(raw["metrics"], "results.metrics")

    if isinstance(raw, dict):
        return _normalize_metric_map(raw, "results")

    raise ValueError("Results JSON must be an object or contain a `metrics` object")


def evaluate_thresholds(config_path: Path) -> int:
    config = _load_config(config_path)

    thresholds = _normalize_metric_map(config.get("thresholds"), "thresholds")
    if not thresholds:
        raise ValueError(
            "No thresholds configured. Add at least one metric in `thresholds`."
        )

    actual_metrics = _normalize_metric_map(config.get("metrics"), "metrics")

    results_file = str(config.get("results_file", "")).strip()
    if results_file:
        resolved = (config_path.parent / results_file).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Configured results_file not found: {resolved}")
        actual_metrics.update(_load_metrics_from_file(resolved))

    missing: list[str] = []
    failed: list[tuple[str, float, float]] = []

    print(f"Loaded thresholds from {config_path}")
    print("Metric checks:")

    for metric, threshold in sorted(thresholds.items()):
        if metric not in actual_metrics:
            missing.append(metric)
            print(f"  - {metric}: MISSING (required >= {threshold:.4f})")
            continue

        actual = actual_metrics[metric]
        if actual < threshold:
            failed.append((metric, actual, threshold))
            print(f"  - {metric}: FAIL ({actual:.4f} < {threshold:.4f})")
        else:
            print(f"  - {metric}: PASS ({actual:.4f} >= {threshold:.4f})")

    if missing:
        print("\nMissing metrics:")
        for metric in missing:
            print(f"  - {metric}")

    if failed:
        print("\nThreshold failures:")
        for metric, actual, threshold in failed:
            print(f"  - {metric}: {actual:.4f} < {threshold:.4f}")

    return 1 if (missing or failed) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ragas threshold gate")
    parser.add_argument(
        "--config",
        default="evals/ragas/config.yaml",
        help="Path to ragas config file",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 2

    try:
        return evaluate_thresholds(config_path)
    except Exception as exc:
        print(f"Ragas gate failed with error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
