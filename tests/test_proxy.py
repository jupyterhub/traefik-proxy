"""Tests for the base traefik proxy"""

import pytest

from proxytest import *

# Mark all tests in this file as asyncio and slow
pytestmark = [pytest.mark.asyncio, pytest.mark.slow]


@pytest.fixture(
    params=[
        "no_auth_consul_proxy",
        "auth_consul_proxy",
        "no_auth_etcd_proxy",
        "auth_etcd_proxy",
        "file_proxy_toml",
        "file_proxy_yaml",
        "external_consul_proxy",
        "auth_external_consul_proxy",
        "external_etcd_proxy",
        "auth_external_etcd_proxy",
        "external_file_proxy_toml",
        "external_file_proxy_yaml",
    ]
)
def proxy(request):
    return request.getfixturevalue(request.param)
