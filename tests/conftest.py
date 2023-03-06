"""General pytest fixtures"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from consul.aio import Consul
from jupyterhub.utils import exponential_backoff
from traitlets.log import get_logger

from jupyterhub_traefik_proxy.consul import TraefikConsulProxy
from jupyterhub_traefik_proxy.etcd import TraefikEtcdProxy
from jupyterhub_traefik_proxy.fileprovider import TraefikFileProviderProxy

HERE = Path(__file__).parent.resolve()
config_files = os.path.join(HERE, "config_files")


class Config:
    """Namespace for repeated variables.

    N.B. The user names and passwords are also stored in various configuration
    files, saved in ./tests/config_files, both in plain text, and in the case
    of the consul token, base64 encoded (so cannot be grep'ed)."""

    # Force etcdctl to run with the v3 API. This gives us access to various
    # commandss, e.g.  txn
    # Must be passed to the env parameter of any subprocess.Popen call that runs
    # etcdctl
    etcdctl_env = dict(os.environ, ETCDCTL_API="3")

    # Etcd3 auth login credentials
    etcd_password = "secret"
    etcd_user = "root"

    # Consul auth login credentials
    consul_token = "secret"
    consul_port = 8500
    consul_auth_port = 8501

    # Traefik api auth login credentials
    traefik_api_user = "api_admin"
    traefik_api_pass = "admin"

    # The URL that should be proxied to jupyterhub
    # Putting here, can easily change between http and https
    public_url = "https://127.0.0.1:8000"


# Define a "slow" test marker so that we can run the slow tests at the end


def by_slow_marker(item):
    m = item.get_closest_marker("slow")
    if m is None:
        return 0
    else:
        return 1


def pytest_addoption(parser):
    parser.addoption("--slow-last", action="store_true", default=False)


def pytest_collection_modifyitems(items, config):
    if config.getoption("--slow-last"):
        items.sort(key=by_slow_marker)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow.")


@pytest.fixture
async def no_auth_consul_proxy(launch_consul):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl disabled.
    """
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        consul_url=f"http://127.0.0.1:{Config.consul_port}",
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_consul_proxy(launch_consul_acl):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl enabled.
    """
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        consul_url=f"http://127.0.0.1:{Config.consul_port}",
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        consul_password=Config.consul_token,
        check_route_timeout=45,
        should_start=True,
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def no_auth_etcd_proxy(launch_etcd):
    """
    Fixture returning a configured TraefikEtcdProxy.
    No etcd authentication.
    """
    proxy = _make_etcd_proxy(auth=False)
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_etcd_proxy(enable_auth_in_etcd):
    """
    Fixture returning a configured TraefikEtcdProxy
    Etcd has credentials set up
    """
    proxy = _make_etcd_proxy(auth=True)
    await proxy.start()
    yield proxy
    await proxy.stop()


def _make_etcd_proxy(auth=False, **extra_kwargs):
    grpc_options = [
        ("grpc.ssl_target_name_override", "localhost"),
        ("grpc.default_authority", "localhost"),
    ]
    kwargs = dict(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
    )
    if auth:
        kwargs.update(
            dict(
                grpc_options=grpc_options,
                etcd_url="https://localhost:2379",
                etcd_client_ca_cert=f"{config_files}/fake-ca-cert.crt",
                etcd_insecure_skip_verify=True,
                etcd_username=Config.etcd_user,
                etcd_password=Config.etcd_password,
            )
        )
    kwargs.update(extra_kwargs)
    proxy = TraefikEtcdProxy(**kwargs)
    return proxy


@pytest.fixture(autouse=True)
def traitlets_log():
    """Setup traitlets logger at debug-level

    This is the logger used by all Proxy instances (via LoggingConfigurable)
    """
    log = get_logger()
    log.setLevel(logging.DEBUG)


# There must be a way to parameterise this to run on both yaml and toml files?
@pytest.fixture
async def file_proxy_toml():
    """Fixture returning a configured TraefikFileProviderProxy"""
    dynamic_config_file = os.path.join(config_files, "dynamic_config", "rules.toml")
    static_config_file = "traefik.toml"
    proxy = _file_proxy(
        dynamic_config_file, static_config_file=static_config_file, should_start=True
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def file_proxy_yaml():
    dynamic_config_file = os.path.join(config_files, "dynamic_config", "rules.yaml")
    static_config_file = "traefik.yaml"
    proxy = _file_proxy(
        dynamic_config_file, static_config_file=static_config_file, should_start=True
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


def _file_proxy(dynamic_config_file, **kwargs):
    return TraefikFileProviderProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        dynamic_config_file=dynamic_config_file,
        check_route_timeout=60,
        **kwargs,
    )


@pytest.fixture
async def external_file_proxy_yaml(launch_traefik_file):
    dynamic_config_file = os.path.join(config_files, "dynamic_config", "rules.yaml")
    proxy = _file_proxy(dynamic_config_file, should_start=False)
    await proxy._wait_for_static_config()
    yield proxy
    os.remove(dynamic_config_file)


@pytest.fixture
async def external_file_proxy_toml(launch_traefik_file):
    dynamic_config_file = os.path.join(config_files, "dynamic_config", "rules.toml")
    proxy = _file_proxy(dynamic_config_file, should_start=False)
    await proxy._wait_for_static_config()
    yield proxy
    os.remove(dynamic_config_file)


@pytest.fixture
async def external_consul_proxy(launch_consul, configure_consul, launch_traefik_consul):
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        consul_url=f"http://127.0.0.1:{Config.consul_port}",
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=False,
    )
    await proxy._wait_for_static_config()
    yield proxy


@pytest.fixture
async def auth_external_consul_proxy(
    launch_consul_acl, configure_consul_auth, launch_traefik_consul_auth
):
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        consul_url=f"http://127.0.0.1:{Config.consul_auth_port}",
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        consul_password=Config.consul_token,
        check_route_timeout=45,
        should_start=False,
    )
    await proxy._wait_for_static_config()
    yield proxy


@pytest.fixture
async def external_etcd_proxy(launch_traefik_etcd):
    proxy = _make_etcd_proxy(auth=False, should_start=False)
    await proxy._wait_for_static_config()
    yield proxy
    proxy.etcd.close()


@pytest.fixture
async def auth_external_etcd_proxy(
    launch_traefik_etcd_auth,
):
    proxy = _make_etcd_proxy(auth=True, should_start=False)
    await proxy._wait_for_static_config()
    yield proxy
    proxy.etcd.close()


#########################################################################
# Fixtures for launching traefik, with each backend and with or without #
# authentication                                                        #
#########################################################################


@pytest.fixture
def launch_traefik_file():
    args = ("--configfile", os.path.join(config_files, "traefik.toml"))
    print(f"\nLAUNCHING TRAEFIK with args: {args}\n")
    proc = _launch_traefik(*args)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_etcd(launch_etcd, configure_etcd):
    env = Config.etcdctl_env
    proc = _launch_traefik_cli("--providers.etcd", env=env)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_etcd_auth(launch_etcd_auth, configure_etcd_auth):
    extra_args = (
        "--providers.etcd.tls.insecureSkipVerify=true",
        "--providers.etcd.tls.ca=" + f"{config_files}/fake-ca-cert.crt",
        "--providers.etcd.username=" + Config.etcd_user,
        "--providers.etcd.password=" + Config.etcd_password,
    )
    proc = _launch_traefik_cli(*extra_args, env=Config.etcdctl_env)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_consul():
    proc = _launch_traefik_cli("--providers.consul")
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_consul_auth():
    extra_args = (
        f"--providers.consul.endpoints=http://127.0.0.1:{Config.consul_auth_port}",
    )
    traefik_env = os.environ.copy()
    traefik_env.update({"CONSUL_HTTP_TOKEN": Config.consul_token})
    proc = _launch_traefik_cli(*extra_args, env=traefik_env)
    yield proc
    shutdown_traefik(proc)


def _launch_traefik_cli(*extra_args, env=None):
    default_args = (
        "--api",
        "--log.level=debug",
        # "--entrypoints.web.address=:8000",
        "--entrypoints.websecure.address=:8000",
        "--entrypoints.enter_api.address=:8099",
    )
    args = default_args + extra_args
    return _launch_traefik(*args, env=env)


def _launch_traefik(*extra_args, env=None):
    traefik_launch_command = ("traefik",) + extra_args
    print("launching", traefik_launch_command)
    proc = subprocess.Popen(traefik_launch_command, env=env)
    return proc


#########################################################################
# Fixtures for configuring the traefik providers                        #
#########################################################################

# Etcd Launchers and configurers #
##################################


@pytest.fixture
def configure_etcd(launch_etcd):
    """Load traefik api rules into the etcd kv store"""
    yield _config_etcd()


@pytest.fixture
def configure_etcd_auth(launch_etcd_auth, enable_auth_in_etcd):
    """Load traefik api rules into the etcd kv store, with authentication"""
    yield _config_etcd(
        "--user=" + Config.etcd_user + ":" + Config.etcd_password,
        "--insecure-skip-tls-verify=true",
        "--insecure-transport=false",
    )


def _config_etcd(*extra_args):
    data_store_cmd = ("etcdctl", "txn", "--debug") + extra_args
    # Load a pre-baked dynamic configuration into the etcd store.
    # This essentially puts authentication on the traefik api handler.
    with open(os.path.join(config_files, "traefik_etcd_txns.txt")) as fd:
        txns = fd.read()
    proc = subprocess.Popen(
        data_store_cmd, stdin=subprocess.PIPE, env=Config.etcdctl_env
    )
    # need two trailing newlines for etcdctl txn to complete
    proc.communicate(txns.encode() + b'\n\n')
    proc.wait()
    assert (
        proc.returncode == 0
    ), f"{data_store_cmd} exited with status {proc.returncode}"


@pytest.fixture
def enable_auth_in_etcd(launch_etcd_auth):
    user = Config.etcd_user
    pw = Config.etcd_password
    common_args = [
        "--insecure-skip-tls-verify=true",
        "--insecure-transport=false",
        "--debug",
    ]
    subprocess.check_call(
        ["etcdctl", "user", "add", f"{user}:{pw}"] + common_args, env=Config.etcdctl_env
    )
    subprocess.check_call(
        ["etcdctl", "user", "grant-role", user, "root"] + common_args,
        env=Config.etcdctl_env,
    )
    assert (
        subprocess.check_output(
            ["etcdctl", "auth", "enable"] + common_args, env=Config.etcdctl_env
        )
        .decode(sys.stdout.encoding)
        .strip()
        == "Authentication Enabled"
    )
    yield

    assert (
        subprocess.check_output(
            ["etcdctl", "--user", f"{user}:{pw}", "auth", "disable"] + common_args,
            env=Config.etcdctl_env,
        )
        .decode(sys.stdout.encoding)
        .strip()
        == "Authentication Disabled"
    )
    subprocess.call(
        ["etcdctl", "user", "revoke-role", "root", user] + common_args,
        env=Config.etcdctl_env,
    )
    subprocess.call(
        ["etcdctl", "user", "delete", user] + common_args, env=Config.etcdctl_env
    )


@pytest.fixture
async def launch_etcd_auth():
    etcd_proc = subprocess.Popen(
        [
            "etcd",
            "--log-level=debug",
            "--peer-auto-tls",
            f"--cert-file={config_files}/test-cert.crt",
            f"--key-file={config_files}/test-key.key",
            "--initial-cluster=default=https://localhost:2380",
            "--initial-advertise-peer-urls=https://localhost:2380",
            "--listen-peer-urls=https://localhost:2380",
            "--listen-client-urls=https://localhost:2379",
            "--advertise-client-urls=https://localhost:2379",
            "--log-level=debug",
        ],
    )
    try:
        await _wait_for_etcd(
            "--user",
            f"{Config.etcd_user}:{Config.etcd_password}",
            "--insecure-skip-tls-verify=true",
            "--insecure-transport=false",
            "--debug",
        )
        yield etcd_proc
    finally:
        shutdown_etcd(etcd_proc)


@pytest.fixture
async def launch_etcd():
    with TemporaryDirectory() as etcd_path:
        etcd_proc = subprocess.Popen(
            ["etcd", "--log-level=debug"],
            cwd=etcd_path,
        )
        try:
            await _wait_for_etcd("--debug=true")
            yield etcd_proc
        finally:
            shutdown_etcd(etcd_proc)


async def _wait_for_etcd(*etcd_args):
    """Etcd may not be ready if we jump straight into the tests.
    Make sure it's running before we continue with configuring it or running
    tests against it.

    In production, etcd would already be running, so don't put this in the
    proxy classes.
    """

    def check():
        p = subprocess.run(
            ["etcdctl", "endpoint", "health", *etcd_args],
            env=Config.etcdctl_env,
            check=False,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        return "is healthy" in p.stdout + p.stderr

    await exponential_backoff(check, "etcd health check", timeout=10)


# @pytest.fixture(scope="function", autouse=True)
# Is this referenced anywhere??
# @pytest.fixture
def clean_etcd():
    subprocess.run(["etcdctl", "del", '""', "--from-key=true"], env=Config.etcdctl_env)


# Consul Launchers and configurers #
####################################


@pytest.fixture(scope="module")
def launch_consul():
    with TemporaryDirectory() as consul_path:
        print(f"Launching consul in {consul_path}")
        consul_proc = subprocess.Popen(
            [
                "consul",
                "agent",
                "-dev",
                f"-http-port={Config.consul_port}",
            ],
            cwd=consul_path,
        )
        asyncio.run(
            _wait_for_consul(token=Config.consul_token, port=Config.consul_port)
        )
        yield consul_proc
        shutdown_consul(consul_proc)


@pytest.fixture(scope="module")
def launch_consul_acl():
    with TemporaryDirectory() as consul_path:
        consul_proc = subprocess.Popen(
            [
                "consul",
                "agent",
                "-dev",
                # the only one we care about
                f"-http-port={Config.consul_auth_port}",
                # the rest of these are to avoid conflicts
                # https://developer.hashicorp.com/consul/docs/install/ports
                "-dns-port=8610",
                "-server-port=8310",
                "-grpc-port=8512",
                "-grpc-tls-port=8513",
                "-serf-lan-port=8311",
                "-serf-wan-port=8312",
                f"-config-file={config_files}/consul_config.json",
                "-bootstrap-expect=1",
            ],
            cwd=consul_path,
        )
        asyncio.run(
            _wait_for_consul(token=Config.consul_token, port=Config.consul_auth_port)
        )
        yield consul_proc
        shutdown_consul(
            consul_proc, secret=Config.consul_token, port=Config.consul_auth_port
        )


async def _wait_for_consul(token=None, **kwargs):
    """Consul takes ages to shutdown and start. Make sure it's running before
    we continue with configuring it or running tests against it.

    In production, consul would already be running, so don't put this in the
    proxy classes.
    """

    async def _check_consul():
        try:
            cli = Consul(token=token, **kwargs)
            index, data = await cli.kv.get("getting_any_nonexistent_key_will_do")
        except Exception as e:
            print(f"Consul not up: {e}")
            return False

        print("Consul is up!")
        return True

    await exponential_backoff(
        _check_consul,
        "Consul not available",
        timeout=20,
    )


@pytest.fixture
def configure_consul():
    """Load an initial config into the consul KV store"""
    yield _config_consul()


@pytest.fixture
def configure_consul_auth():
    """Load an initial config into the consul KV store, using authentication"""
    yield _config_consul(secret=Config.consul_token, port=Config.consul_auth_port)


def _config_consul(secret=None, port=8500):
    proc_env = None
    if secret is not None:
        proc_env = os.environ.copy()
        proc_env.update({"CONSUL_HTTP_TOKEN": secret})

    consul_import_cmd = [
        "consul",
        "kv",
        "import",
        f"-http-addr=http://127.0.0.1:{port}",
        f"@{config_files}/traefik_consul_config.json",
    ]

    """
    Try storing the static config to the kv store.
    Stop if the kv store isn't ready in 60s.
    """
    timeout = time.perf_counter() + 60
    while True:
        if time.perf_counter() > timeout:
            raise Exception("KV not ready! 60s timeout expired!")
        try:
            # Put static config from file in kv store.
            proc = subprocess.check_call(consul_import_cmd, env=proc_env)
            break
        except subprocess.CalledProcessError as e:
            print("Error setting up consul")
            time.sleep(3)


#########################################################################
# Teardown functions                                                    #
#########################################################################


def shutdown_consul(consul_proc, secret=None, port=8500):
    terminate_process(consul_proc, timeout=30)


def shutdown_etcd(etcd_proc):
    clean_etcd()
    terminate_process(etcd_proc, timeout=20)

    # Remove the default.etcd folder, so no settings left over
    # from a completed run
    default_etcd = os.path.join(os.getcwd(), "default.etcd")
    if os.path.exists(default_etcd):
        shutil.rmtree(default_etcd)


def shutdown_traefik(traefik_process):
    terminate_process(traefik_process)


def terminate_process(proc, timeout=5):
    proc.terminate()
    try:
        proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    finally:
        proc.wait()
