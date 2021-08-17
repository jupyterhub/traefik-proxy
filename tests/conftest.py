"""General pytest fixtures"""

import os
import shutil
import subprocess
import sys
import time

import pytest
from _pytest.mark import Mark

from jupyterhub_traefik_proxy import TraefikFileProxy


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
# There must be a way to parameterise this to run on both yaml and toml files?
async def toml_proxy():
    """Fixture returning a configured TraefikFileProxy"""
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.toml"
    )
    proxy = TraefikFileProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=180,
        should_start=True,
        dynamic_config_file=dynamic_config_file,
        static_config_file="traefik.toml"
    )

    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def yaml_proxy():
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.yaml"
    )
    proxy = TraefikFileProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=180,
        should_start=True,
        dynamic_config_file=dynamic_config_file,
        static_config_file="traefik.yaml"
    )

    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def external_toml_proxy(launch_traefik_file):
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.toml"
    )
    proxy = TraefikFileProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=45,
        should_start=False,
        dynamic_config_file=dynamic_config_file,
    )

    yield proxy
    os.remove(dynamic_config_file)


@pytest.fixture
async def external_yaml_proxy(launch_traefik_file):
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.yaml"
    )
    proxy = TraefikFileProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
        check_route_timeout=180,
        should_start=False,
        dynamic_config_file=dynamic_config_file,
    )

    yield proxy
    os.remove(dynamic_config_file)


@pytest.fixture
def launch_traefik_file():
    proc = subprocess.Popen(
        ["traefik", "--configfile", "./tests/config_files/traefik.toml"]
    )
    yield proc
    proc.kill()
    proc.wait()


@pytest.fixture(scope="session", autouse=False)
def etcd():
    etcd_proc = subprocess.Popen("etcd", stdout=None, stderr=None)
    yield etcd_proc

    etcd_proc.kill()
    etcd_proc.wait()
    shutil.rmtree(os.getcwd() + "/default.etcd/")


@pytest.fixture(scope="function", autouse=False)
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
