"""General pytest fixtures"""

import pytest
import sys
import utils
import subprocess
import os
import shutil

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub.tests.mocking import MockHub

from traitlets.config import Config
from os.path import abspath, dirname, join
from tornado import ioloop, gen
from tornado.platform.asyncio import AsyncIOMainLoop


@pytest.fixture()
async def etcd_proxy():
    """Fixture returning a configured TraefikEtcdProxy"""
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture()
async def toml_proxy():
    """Fixture returning a configured TraefikTomlProxy"""
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture(params=["etcd_proxy", "toml_proxy"])
def proxy(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="session", autouse=True)
def etcd():
    etcd_proc = subprocess.Popen("etcd", stdout=None, stderr=None)
    yield etcd_proc
    etcd_proc.kill()
    etcd_proc.wait()
    shutil.rmtree(os.getcwd() + "/default.etcd/")


@pytest.fixture(scope="function", autouse=True)
def clean_etcd():
    subprocess.run(["etcdctl", "del", '""', "--from-key=true"])


@pytest.fixture()
def restart_traefik_proc(proxy):
    proxy._stop_traefik()
    proxy._start_traefik()


@pytest.fixture()
def launch_backend():
    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))
    running_backends = []

    def _launch_backend(port):
        backend = subprocess.Popen(
            [sys.executable, dummy_server_path, str(port)], stdout=None
        )
        running_backends.append(backend)

    yield _launch_backend

    for proc in running_backends:
        proc.kill()
    for proc in running_backends:
        proc.wait()


@pytest.fixture()
def cfg_etcd_proxy():
    cfg = Config()
    cfg.TraefikEtcdProxy.public_url = "http://127.0.0.1:8000"
    cfg.TraefikEtcdProxy.traefik_api_password = "admin"
    cfg.TraefikEtcdProxy.traefik_api_username = "admin"
    cfg.TraefikEtcdProxy.should_start = True
    cfg.proxy_class = TraefikEtcdProxy
    yield cfg


@pytest.fixture()
def cfg_toml_proxy():
    cfg = Config()
    cfg.TraefikTomlProxy.public_url = "http://127.0.0.1:8000"
    cfg.TraefikTomlProxy.traefik_api_password = "admin"
    cfg.TraefikTomlProxy.traefik_api_username = "admin"
    cfg.TraefikTomlProxy.should_start = True
    cfg.proxy_class = TraefikTomlProxy
    yield cfg


@pytest.fixture()
def cfg_configurable_http_proxy():
    cfg = Config()
    cfg.ConfigurableHTTPProxy.auth_token = "secret!"
    cfg.ConfigurableHTTPProxy.api_url = "http://127.0.0.1:8000"
    cfg.ConfigurableHTTPProxy.should_start = True
    cfg.proxy_class = ConfigurableHTTPProxy
    yield cfg


@pytest.fixture(
    params=["cfg_etcd_proxy", "cfg_toml_proxy", "cfg_configurable_http_proxy"]
)
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
