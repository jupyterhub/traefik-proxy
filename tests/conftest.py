"""General pytest fixtures"""

import pytest
import sys
import subprocess
import os
import shutil

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub.tests.mocking import MockHub
from traitlets.config import Config


@pytest.fixture()
async def etcd_proxy():
    """Fixture returning a configured TraefikEtcdProxy"""
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        should_start=True,
    )
    app = MockHub()
    app.init_hub()
    proxy.app = app
    proxy.hub = app.hub

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
        should_start=True,
    )
    app = MockHub()
    app.init_hub()
    proxy.app = app
    proxy.hub = app.hub

    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture()
async def configurable_http_proxy():
    """Fixture returning a configured ConfigurableHTTPProxy"""
    proxy = ConfigurableHTTPProxy(
        auth_token="secret!",
        api_url="http://127.0.0.1:54321",
        should_start=True,
        public_url="http://127.0.0.1:8000",
    )

    app = MockHub()
    app.init_hub()
    proxy.app = app
    proxy.hub = app.hub

    await proxy.start()
    yield proxy
    proxy.stop()


@pytest.fixture()
def external_toml_proxy():
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    proxy.should_start = False
    proxy.toml_dynamic_config_file = "./tests/rules.toml"
    # Start traefik manually
    traefik_process = subprocess.Popen(
        ["traefik", "-c", "./tests/traefik.toml"], stdout=None
    )

    yield proxy

    open("./tests/rules.toml", "w").close()
    traefik_process.kill()
    traefik_process.wait()


@pytest.fixture()
def external_etcd_proxy():
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    proxy.should_start = False
    # Get the static config from file
    subprocess.run(
        [
            "traefik",
            "storeconfig",
            "-c",
            "./tests/traefik_etcd_config.toml",
            "--etcd",
            "--etcd.endpoint=127.0.0.1:2379",
            "--etcd.useapiv3=true",
        ]
    )
    # Start traefik manually
    traefik_process = subprocess.Popen(
        ["traefik", "--etcd", "--etcd.useapiv3=true"], stdout=None
    )

    yield proxy

    traefik_process.kill()
    traefik_process.wait()


@pytest.fixture(
    params=[
        "etcd_proxy",
        "toml_proxy",
        "configurable_http_proxy",
        "external_etcd_proxy",
        "external_toml_proxy",
    ]
)
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
    dummy_server_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "dummy_http_server.py")
    )
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
