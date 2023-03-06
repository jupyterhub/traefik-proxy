"""Tests for the base traefik proxy"""

import pytest

# Some proxy tests are defined in `proxytest` so that they can be used in external repositories
from proxytest import *  # noqa

from jupyterhub_traefik_proxy.proxy import TraefikProxy

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


def test_default_port():
    p = TraefikProxy(
        public_url="http://127.0.0.1/", traefik_api_url="https://127.0.0.1/"
    )
    assert p.public_url == "http://127.0.0.1:80/"
    assert p.traefik_api_url == "https://127.0.0.1:443/"

    with pytest.raises(ValueError):
        TraefikProxy(public_url="ftp://127.0.0.1:23/")
