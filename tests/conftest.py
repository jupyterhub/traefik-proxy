"""General pytest fixtures"""

import pytest
import sys
import utils
import subprocess
import os
import shutil

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from os.path import abspath, dirname, join


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


@pytest.fixture(scope="module")
def etcd():
    etcd_proc = subprocess.Popen("etcd", stdout=None, stderr=None)
    yield etcd_proc
    etcd_proc.kill()
    etcd_proc.wait()
    shutil.rmtree(os.getcwd() + "/default.etcd/")


@pytest.fixture()
def clean_etcd():
    subprocess.run(["etcdctl", "del", '""', "--from-key=true"])


@pytest.fixture
def restart_traefik_proc(proxy):
    proxy._stop_traefik()
    proxy._start_traefik()


@pytest.fixture
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
