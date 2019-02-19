"""Tests for the base traefik proxy"""

import pytest

from proxytest import *

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(
    params=[
        "no_auth_etcd_proxy",
        "auth_etcd_proxy",
        "toml_proxy",
        "external_etcd_proxy",
        "auth_external_etcd_proxy",
        "external_toml_proxy",
    ]
)
def proxy(request):
    return request.getfixturevalue(request.param)
