"""General pytest fixtures"""

import pytest
import sys
import utils

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from os.path import abspath, dirname, join
from subprocess import Popen


@pytest.fixture
async def proxy():
    """Fixture returning a configured Traefik Proxy"""
    proxy = TraefikEtcdProxy(public_url="http://127.0.0.1:8000")
    try:
        await proxy.start()
        yield proxy
    finally:
        await proxy.stop()


@pytest.fixture
def restart_traefik_proc(proxy):
    proxy._stop_traefik()
    proxy._start_traefik()


_ports = {"default_backend": 9000, "first_backend": 9090, "second_backend": 9099}


@pytest.fixture
def launch_backends(request):
    default_backend_port, first_backend_port, second_backend_port = (
        utils.get_backend_ports()
    )

    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))

    default_backend = Popen(
        [sys.executable, dummy_server_path, str(default_backend_port)], stdout=None
    )
    first_backend = Popen(
        [sys.executable, dummy_server_path, str(first_backend_port)], stdout=None
    )
    second_backend = Popen(
        [sys.executable, dummy_server_path, str(second_backend_port)], stdout=None
    )

    request.addfinalizer(default_backend.kill)
    request.addfinalizer(first_backend.kill)
    request.addfinalizer(second_backend.kill)


@pytest.fixture
def default_backend(request):
    default_backend_port, _, _ = utils.get_backend_ports()

    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))

    default_backend = Popen(
        [sys.executable, dummy_server_path, str(default_backend_port)], stdout=None
    )

    request.addfinalizer(default_backend.kill)
