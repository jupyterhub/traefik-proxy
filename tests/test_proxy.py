"""Tests for the base traefik proxy"""

import pytest
import subprocess
import sys

from proxytest import *
from traitlets.config import Config
from os.path import dirname, join, abspath

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub.tests.mocking import MockHub

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def launch_backend():
    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))
    running_backends = []

    def _launch_backend(port, proto="http"):
        backend = subprocess.Popen(
            [sys.executable, dummy_server_path, str(port), proto], stdout=None
        )
        running_backends.append(backend)

    yield _launch_backend

    for proc in running_backends:
        proc.kill()
    for proc in running_backends:
        proc.wait()


@pytest.fixture
def cfg_etcd_proxy():
    cfg = Config()
    cfg.TraefikEtcdProxy.public_url = "http://127.0.0.1:8000"
    cfg.TraefikEtcdProxy.traefik_api_password = "admin"
    cfg.TraefikEtcdProxy.traefik_api_username = "admin"
    cfg.TraefikEtcdProxy.should_start = True
    cfg.proxy_class = TraefikEtcdProxy
    yield cfg


@pytest.fixture
def cfg_toml_proxy():
    cfg = Config()
    cfg.TraefikTomlProxy.public_url = "http://127.0.0.1:8000"
    cfg.TraefikTomlProxy.traefik_api_password = "admin"
    cfg.TraefikTomlProxy.traefik_api_username = "admin"
    cfg.TraefikTomlProxy.should_start = True
    cfg.proxy_class = TraefikTomlProxy
    yield cfg


@pytest.fixture(params=["cfg_etcd_proxy", "cfg_toml_proxy"])
async def app(request):
    cfg = request.getfixturevalue(request.param)
    app = MockHub.instance(config=cfg)
    MockHub.proxy_class = cfg.proxy_class

    await app.initialize([])
    await app.start()

    yield app

    app.log.handlers = []
    MockHub.clear_instance()
    try:
        app.stop()
    except Exception as e:
        print("Error stopping Hub: %s" % e, file=sys.stderr)


@pytest.fixture
def disable_check_routes(app):
    # disable periodic check_routes while we are testing
    app.last_activity_callback.stop()
    try:
        yield
    finally:
        app.last_activity_callback.start()
