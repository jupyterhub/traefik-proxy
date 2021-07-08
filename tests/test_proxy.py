"""Tests for the base traefik proxy"""

import pytest

from proxytest import *

# Mark all tests in this file as asyncio and slow
pytestmark = [pytest.mark.asyncio, pytest.mark.slow]


@pytest.fixture(
    params=[
        "toml_proxy",
        "external_toml_proxy",
    ]
)
def proxy(request):
    return request.getfixturevalue(request.param)
