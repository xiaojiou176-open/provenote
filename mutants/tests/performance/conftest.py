"""Pytest configuration for performance tests."""

import pytest


@pytest.fixture(scope="session")
def benchmark_config():
    """Configuration for benchmark tests."""
    return {
        "warmup_rounds": 2,
        "min_rounds": 5,
        "max_time": 10.0,  # max 10 seconds per benchmark
    }
