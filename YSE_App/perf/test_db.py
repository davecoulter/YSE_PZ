"""Run perf benchmarks against Django's migrated test database (same as unit tests)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment


@contextmanager
def benchmark_test_database() -> Iterator[None]:
    """
    Create test DB with migrations, yield for benchmark work, then tear down.

    manage.py test uses this path; record_perf_benchmark must too — the default
  YSE database from docker init SQL is missing tables such as
  YSE_App_transientphotdata_data_quality.
    """
    setup_test_environment()
    runner = DiscoverRunner(verbosity=0, interactive=False)
    old_config = runner.setup_databases()
    try:
        yield
    finally:
        runner.teardown_databases(old_config)
