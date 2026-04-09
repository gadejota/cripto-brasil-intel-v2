"""Compat layer kept for legacy imports.

The original project mixed scraping, ranking and content generation in one file.
This module now exposes only the editorial generation surface used by the
publisher or external scripts.
"""
from __future__ import annotations

from app.editorial import build_editorial_package

__all__ = ['build_editorial_package']
