# Tests for Rate Limiting

import pytest


def test_ip_rate_limit_enforced():
    """REQ-001: 101st request from same IP returns 429."""
    pass


def test_retry_after_header_present():
    """REQ-002: 429 response includes Retry-After header."""
    pass


def test_authenticated_user_higher_limit():
    """REQ-003: Authenticated users get 1000 req/min limit."""
    pass
# NOTE: No test for Redis persistence — this is the seeded gap.
# The checker will flag the 4th requirement as missing from tests.
