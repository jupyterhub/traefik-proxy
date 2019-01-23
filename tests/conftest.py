"""General pytest fixtures"""

import pytest
import subprocess
import os
import shutil

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub.tests.mocking import MockHub


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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
    params=["etcd_proxy", "toml_proxy", "external_etcd_proxy", "external_toml_proxy"]
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
