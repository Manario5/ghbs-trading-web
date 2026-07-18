import os
import pytest


@pytest.fixture(autouse=True)
def restore_environment_after_each_test():
    """
    Prevent one test's os.environ changes from leaking into later tests.

    This is important because safety-matrix tests depend on operational
    flags such as ENABLE_MARKET_DATA_SMOKE_TESTS, ENABLE_PROVIDER_COVERAGE_SCAN,
    ENABLE_LIVE_ANALYZE_PREVIEW, and ENABLE_LIVE_SCOUT_PREVIEW.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
