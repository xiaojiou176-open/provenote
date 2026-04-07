#!/usr/bin/env python3
"""Compatibility wrapper for the first-party operator CLI auditable lane."""

from __future__ import annotations

import sys

from packages.core.operator.cli import main as operator_main

if __name__ == "__main__":
    raise SystemExit(operator_main(["auditable-markdown", *sys.argv[1:]]))
