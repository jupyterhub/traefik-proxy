"""General pytest fixtures"""

import pytest

from jupyterhub_traefik_proxy import TraefikProxy


@pytest.fixture
async def proxy():
    """Fixture returning a configured Traefik Proxy"""
    # TODO: set up the proxy
    proxy = TraefikProxy()
    await proxy.start()
    yield proxy
