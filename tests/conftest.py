"""General pytest fixtures"""

import pytest

from jupyterhub_traefik_proxy import TraefikProxy


@pytest.fixture
def proxy():
    """Fixture returning a configured Traefik Proxy"""
    # TODO: set up the proxy
    proxy = TraefikProxy()
    yield proxy
