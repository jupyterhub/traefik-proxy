"""Tests for the base traefik proxy"""

import pytest

from proxytest import *

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio
# Mark all tests in this file as slow
pytestmark = pytest.mark.slow


@pytest.fixture(
    params=[
        "no_auth_consul_proxy",
        "auth_consul_proxy",
        "no_auth_etcd_proxy",
        "auth_etcd_proxy",
        "toml_proxy",
        "external_consul_proxy",
        "auth_external_consul_proxy",
        "external_etcd_proxy",
        "auth_external_etcd_proxy",
        "external_toml_proxy",
    ]
)
def proxy(request):
    return request.getfixturevalue(request.param)
