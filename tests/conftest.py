"""General pytest fixtures"""

import pytest

from jupyterhub_traefik_proxy import TraefikEtcdProxy


@pytest.fixture
async def proxy():
    """Fixture returning a configured Traefik Proxy"""
    proxy = TraefikEtcdProxy()
    try:
        await proxy.start()
        yield proxy
    finally:
        await proxy.stop()


@pytest.fixture
def restart_traefik_proc(proxy):
    proxy._stop_traefik()
    proxy._start_traefik()
