"""General pytest fixtures"""

import pytest
import subprocess
import os
import shutil
import sys

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub.tests.mocking import MockHub


@pytest.fixture
async def no_auth_etcd_proxy():
    """Fixture returning a configured TraefikEtcdProxy"""
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_etcd_proxy(etcd):
    """Fixture returning a configured TraefikEtcdProxy
    for etcd with credentials"""
    enable_auth_in_etcd("secret")
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        etcd_root_password="secret",
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()
    disable_auth_in_etcd("secret")


@pytest.fixture(params=["no_auth_etcd_proxy", "auth_etcd_proxy"])
def etcd_proxy(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
async def toml_proxy():
    """Fixture returning a configured TraefikTomlProxy"""
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        should_start=True,
    )

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


def configure_and_launch_traefik(password=""):
    storeconfig_command = [
        "traefik",
        "storeconfig",
        "-c",
        "./tests/traefik_etcd_config.toml",
        "--etcd",
        "--etcd.endpoint=127.0.0.1:2379",
        "--etcd.useapiv3=true",
    ]

    traefik_launch_command = ["traefik", "--etcd", "--etcd.useapiv3=true"]

    if password:
        credentials = ["--etcd.username=root", "--etcd.password=" + password]
        storeconfig_command += credentials
        traefik_launch_command += credentials

    # Get the static config from file
    subprocess.run(storeconfig_command)
    # Start traefik manually
    traefik_process = subprocess.Popen(traefik_launch_command, stdout=None)

    return traefik_process


@pytest.fixture
def external_etcd_proxy():
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik()
    yield proxy

    traefik_process.kill()
    traefik_process.wait()


@pytest.fixture
def auth_external_etcd_proxy():
    enable_auth_in_etcd("secret")
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        etcd_root_password="secret",
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik("secret")
    yield proxy

    traefik_process.kill()
    traefik_process.wait()
    disable_auth_in_etcd("secret")


@pytest.fixture(
    params=[
        "no_auth_etcd_proxy",
        "auth_etcd_proxy",
        "toml_proxy",
        "external_etcd_proxy",
        "auth_external_etcd_proxy",
        "external_toml_proxy",
    ]
)
def proxy(request):
    return request.getfixturevalue(request.param)


def enable_auth_in_etcd(password):
    subprocess.call(["etcdctl", "user", "add", "root:" + password])
    subprocess.call(["etcdctl", "user", "grant-role", "root", "root"])
    assert subprocess.check_output(["etcdctl", "auth", "enable"]).decode(sys.stdout.encoding).strip() == "Authentication Enabled"


def disable_auth_in_etcd(password):
    subprocess.call(["etcdctl", "user", "remove", "root"])
    subprocess.check_output(["etcdctl", "--user", "root:" + password, "auth", "disable"]).decode(sys.stdout.encoding).strip() == "Authentication Disabled"


@pytest.fixture(scope="session", autouse=True)
def etcd():
    etcd_proc = subprocess.Popen(["etcd", "--debug"], stdout=None, stderr=None)
    yield etcd_proc

    etcd_proc.kill()
    etcd_proc.wait()
    shutil.rmtree(os.getcwd() + "/default.etcd/")


@pytest.fixture(scope="function", autouse=True)
def clean_etcd():
    subprocess.run(["etcdctl", "del", '""', "--from-key=true"])
