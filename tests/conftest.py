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


def create_etcd_proxy():
    """Function returning a TraefikEtcdProxy object"""
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    return proxy


def create_toml_proxy():
    """Function returning a TraefikTomlProxy object"""
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
    )
    return proxy


@pytest.fixture(params=[create_etcd_proxy, create_toml_proxy])
async def proxy(request):
    """Fixture returning a configured Traefik Proxy"""
    proxy = request.param()
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture()
async def etcd_proxy():
    """Fixture returning a configured Traefik Proxy"""
    proxy = create_etcd_proxy()
    await proxy.start()
    yield proxy
    # await proxy.stop()


@pytest.fixture()
async def toml_proxy():
    """Fixture returning a configured Traefik Proxy"""
    proxy = create_toml_proxy()
    await proxy.start()
    yield proxy
    # await proxy.stop()


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


_ports = {"default_backend": 9000, "first_backend": 9090, "second_backend": 9099}


@pytest.fixture
def launch_backends():
    default_backend_port, first_backend_port, second_backend_port = (
        utils.get_backend_ports()
    )

    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))

    default_backend = subprocess.Popen(
        [sys.executable, dummy_server_path, str(default_backend_port)], stdout=None
    )
    first_backend = subprocess.Popen(
        [sys.executable, dummy_server_path, str(first_backend_port)], stdout=None
    )
    second_backend = subprocess.Popen(
        [sys.executable, dummy_server_path, str(second_backend_port)], stdout=None
    )

    yield

    default_backend.kill()
    first_backend.kill()
    second_backend.kill()

    default_backend.wait()
    first_backend.wait()
    second_backend.wait()


@pytest.fixture
def default_backend():
    default_backend_port, _, _ = utils.get_backend_ports()

    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))

    default_backend = subprocess.Popen(
        [sys.executable, dummy_server_path, str(default_backend_port)], stdout=None
    )

    yield
    default_backend.kill()
    default_backend.wait()
