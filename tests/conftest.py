"""General pytest fixtures"""

import os
import shutil
import subprocess
import sys
import time

import pytest
from _pytest.mark import Mark

from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikConsulProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy


# Define a "slow" test marker so that we can run the slow tests at the end
# ref: https://docs.pytest.org/en/6.0.1/example/simple.html#control-skipping-of-tests-according-to-command-line-option
# ref: https://stackoverflow.com/questions/61533694/run-slow-pytest-commands-at-the-end-of-the-test-suite
empty_mark = Mark("", [], {})


def by_slow_marker(item):
    return item.get_closest_marker("slow", default=empty_mark)


def pytest_addoption(parser):
    parser.addoption("--slow-last", action="store_true", default=False)


def pytest_collection_modifyitems(items, config):
    if config.getoption("--slow-last"):
        items.sort(key=by_slow_marker)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow.")


@pytest.fixture
async def no_auth_consul_proxy(consul_no_acl):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl disabled.
    """
    proxy = TraefikConsulProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_consul_proxy(consul_acl):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl enabled.
    """
    proxy = TraefikConsulProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        kv_password="secret",
        check_route_timeout=45,
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def no_auth_etcd_proxy():
    """
    Fixture returning a configured TraefikEtcdProxy.
    No etcd authentication.
    """
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_etcd_proxy(etcd):
    """
    Fixture returning a configured TraefikEtcdProxy
    Etcd has credentials set up
    """
    enable_auth_in_etcd("secret")
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        kv_password="secret",
        kv_username="root",
        check_route_timeout=45,
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
        check_route_timeout=180,
        should_start=True,
    )

    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
def external_consul_proxy(consul_no_acl):
    proxy = TraefikConsulProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik(kv_store="consul")
    yield proxy

    traefik_process.kill()
    traefik_process.wait()


@pytest.fixture
def auth_external_consul_proxy(consul_acl):
    proxy = TraefikConsulProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        kv_password="secret",
        check_route_timeout=45,
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik(kv_store="consul", password="secret")
    yield proxy

    traefik_process.kill()
    traefik_process.wait()


@pytest.fixture
def external_etcd_proxy():
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik(kv_store="etcd")
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
        kv_password="secret",
        kv_username="root",
        check_route_timeout=45,
        should_start=False,
    )
    traefik_process = configure_and_launch_traefik(kv_store="etcd", password="secret")
    yield proxy

    traefik_process.kill()
    traefik_process.wait()
    disable_auth_in_etcd("secret")


@pytest.fixture
def external_toml_proxy():
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
    )
    proxy.should_start = False
    proxy.toml_dynamic_config_file = "./tests/config_files/rules.toml"
    # Start traefik manually
    traefik_process = subprocess.Popen(
        ["traefik", "-c", "./tests/config_files/traefik.toml"], stdout=None
    )
    yield proxy
    open("./tests/config_files/rules.toml", "w").close()
    traefik_process.kill()
    traefik_process.wait()


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
def consul_no_acl():
    consul_proc = subprocess.Popen(
        ["consul", "agent", "-dev"], stdout=None, stderr=None
    )
    yield consul_proc

    consul_proc.kill()
    consul_proc.wait()


@pytest.fixture()
def consul_acl():
    etcd_proc = subprocess.Popen(
        [
            "consul",
            "agent",
            "-advertise=127.0.0.1",
            "-config-file=./tests/config_files/consul_config.json",
            "-bootstrap-expect=1",
        ],
        stdout=None,
        stderr=None,
    )
    yield etcd_proc

    etcd_proc.kill()
    etcd_proc.wait()
    shutil.rmtree(os.getcwd() + "/consul.data")


def configure_and_launch_traefik(kv_store, password=""):
    if kv_store == "etcd":
        storeconfig_command = [
            "traefik",
            "storeconfig",
            "-c",
            "./tests/config_files/traefik_etcd_config.toml",
            "--etcd",
            "--etcd.endpoint=127.0.0.1:2379",
            "--etcd.useapiv3=true",
        ]

        traefik_launch_command = ["traefik", "--etcd", "--etcd.useapiv3=true"]

        if password:
            credentials = ["--etcd.username=root", "--etcd.password=" + password]
            storeconfig_command += credentials
            traefik_launch_command += credentials

    elif kv_store == "consul":
        storeconfig_command = [
            "traefik",
            "storeconfig",
            "-c",
            "./tests/config_files/traefik_consul_config.toml",
            "--consul",
            "--consul.endpoint=127.0.0.1:8500",
        ]

        traefik_launch_command = ["traefik", "--consul"]

        if password:
            os.environ["CONSUL_HTTP_TOKEN"] = password

    """
    Try storing the static config to the kv store.
    Stop if the kv store isn't ready in 60s.
    """
    timeout = time.time() + 60
    while True:
        if time.time() > timeout:
            raise Exception("KV not ready! 60s timeout expired!")
        try:
            # Put static config from file in kv store.
            subprocess.check_call(storeconfig_command)
            break
        except subprocess.CalledProcessError:
            pass

    # Start traefik manually
    traefik_process = subprocess.Popen(traefik_launch_command, stdout=None)

    return traefik_process


def enable_auth_in_etcd(password):
    subprocess.call(["etcdctl", "user", "add", "root:" + password])
    subprocess.call(["etcdctl", "user", "grant-role", "root", "root"])
    assert (
        subprocess.check_output(["etcdctl", "auth", "enable"])
        .decode(sys.stdout.encoding)
        .strip()
        == "Authentication Enabled"
    )


def disable_auth_in_etcd(password):
    subprocess.call(["etcdctl", "user", "remove", "root"])
    subprocess.check_output(
        ["etcdctl", "--user", "root:" + password, "auth", "disable"]
    ).decode(sys.stdout.encoding).strip() == "Authentication Disabled"
